import pygame
import math
import webbrowser
import time
import cv2

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RUNNING = True

INTERFERANCE_PATTERN = []

WALL_LIST = []    
WAVE_LIST = []

def closeGame():
    pygame.quit()
    exit()

def gradientRect( window, colors, target_rect ):
    """ Draw a horizontal-gradient filled rectangle covering <target_rect> """
    colour_rect = pygame.Surface( ( 2, len(colors) ) , pygame.SRCALPHA)     
    for i, color in enumerate(colors):
        pygame.draw.line( colour_rect, color,  ( 0,i ), ( 1,i ) )     
    colour_rect = pygame.transform.smoothscale( colour_rect, ( target_rect.width, target_rect.height ) )  # stretch!
    window.blit( colour_rect, target_rect )                                    # paint it

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def get(self):
        return (self.x, self.y)

class Wall:
    def __init__(self, TL: tuple[int, int], BR: tuple[int, int]) -> None:
        self.TL: Point = Point(TL[0], TL[1])
        self.BR: Point = Point(BR[0], BR[1])
    
        self.rect: pygame.Rect = pygame.Rect(self.TL.x, 
                                             self.TL.y, 
                                             self.BR.x - self.TL.x, 
                                             self.BR.y - self.TL.y)
    
    def draw(self, display):
        pygame.draw.rect(display, (150, 150, 150), self.rect)

    def drawInterferancePattern(self, display, i):
        width = 1000 - self.BR.x 
        s = pygame.Surface((width, 2), pygame.SRCALPHA )
        alpha = (i[1]) / 2
        if alpha > 0:
            s.fill((255, 255, 0, 50))            
        else:
            s.fill((0, 0, 0,50))            
        display.blit(s, (self.BR.x, i[0]))

class WallGap:
    def __init__(self, TL, BR, gaps: list[tuple[int, int]]) -> None:
        self.TL = Point(TL[0], TL[1])
        self.BR = Point(BR[0], BR[1])
        
        self.gaps = []
        self.gapsRectangles = []
        
        for gap in gaps:
            gapTL = Point(TL[0], gap[0])
            gapBR = Point(BR[0], gap[1])
            
            self.gaps.append((gapTL, gapBR, True))
            
            gapRect = pygame.Rect(gapTL.x,
                                  gapTL.y,
                                  gapBR.x - gapTL.x,
                                  gapBR.y - gapTL.y)

            self.gapsRectangles.append(gapRect)
        
        self.rectWall: pygame.Rect = pygame.Rect(self.TL.x, 
                                             self.TL.y, 
                                             self.BR.x - self.TL.x, 
                                             self.BR.y - self.TL.y)
        
                
    def draw(self, display):
        pygame.draw.rect(display, (150, 150, 150), self.rectWall)
        for rect in self.gapsRectangles:
            pygame.draw.rect(display, (0, 0, 0), rect)

class Wave:
    def __init__(self, origin: tuple[int, int], direction: float = 0, rayWidth: int = 10, isRay = True, angleSpecter=360) -> None:
        self.speed: float = 25
        self.length: float = 1
        self.origin: Point = Point(origin[0], origin[1])
        self.startTime: float = 0
        
        self.amplitude = 2
        self.angularVelocity = self.speed / (2 * math.pi)
        self.time = 0
        self.timeLimit = 10**3
        self.direction = direction * (math.pi / 180)
                
        self.ray = isRay
        self.rayWidth = rayWidth
        
        self.angleSpecter = angleSpecter * math.pi/180
        
        self.canDraw = True
        self.intensityMap = False

    def draw(self, display):
        if not self.canDraw:
            return
        
        if self.ray:
            self._drawRay(display)
        else:
            self._drawWave(display)    
            
        self.time += 0.01        
            
    def _drawRay(self, display):
        global WAVE_LIST
        if self.time > self.timeLimit:
            return
        
        pygame.draw.circle(display, BLUE, self.origin.get(), 1)
        
        height = self.amplitude * math.cos(self.angularVelocity * (self.time))
        
        for width in range(self.rayWidth // -2, self.rayWidth // 2):        
            pos = (
                self.origin.x + self.speed * math.cos(self.direction) * self.time + width * math.sin(self.direction),
                self.origin.y - self.speed * math.sin(self.direction) * self.time + width * math.cos(self.direction)
            )
            for wall in WALL_LIST:
                if wall.TL.x < pos[0] and wall.BR.x > pos[0]:
                    self.canDraw = False
                    
                    for gap in wall.gaps:
                        newWave = Wave(origin=(
                            (gap[1].x - gap[0].x) // 2 + gap[0].x,
                            (gap[1].y - gap[0].y) // 2 + gap[0].y                            
                        ),             isRay = False,
                                       angleSpecter = 90)
                        WAVE_LIST.append(newWave)
                    return
                    
            s = pygame.Surface((2, 2), pygame.SRCALPHA )
            alpha = 255 * (height) / 2
            if alpha > 0:
                s.fill((200, 200, 0, abs(alpha)/255*10))
            else:
                s.fill((0, 200, 200, abs(alpha)/255*10))
            
            display.blit(s, pos)
            # pygame.draw.circle(display, (0, 0, 255 * (height+self.amplitude)/4), pos, 1)
                     
    def _drawWave(self, display):
        if self.time > self.timeLimit:
            return
        global WAVE_LIST
        global INTERFERANCE_PATTERN
        pygame.draw.circle(display, BLUE, self.origin.get(), 1)

        height = self.amplitude * math.cos(self.angularVelocity * (self.time))
        
        # circumfarance = (self.speed * self.time) * 2 * math.pi
        # extraSpins = math.ceil(math.log(10 ** ((circumfarance / 10)/360), 2)) + 1
        
        points = self.speed * self.time
        for i in range(int(points)):
            angle = 2 * i / points * self.angleSpecter/2 + (self.direction - self.angleSpecter / 2)
            pos = (
                self.origin.x + self.speed * math.cos(angle) * self.time,
                self.origin.y - self.speed * math.sin(angle) * self.time
            )
            
            canDrawPos = True

            for wall in WALL_LIST:
                if pos[0] > wall.TL.x and self.origin.x < wall.TL.x:
                    canDrawPos = False
                    try:
                        for i in range(len(wall.gaps)):
                            gap = wall.gaps[i]
                            if gap[0].x < pos[0] and gap[0].y < pos[1] < gap[1].y and gap[0].x - self.origin.x > gap[1].x - gap[0].x and gap[2]:
                                newWave = Wave(origin=(
                                    (gap[1].x - gap[0].x) // 2 + gap[0].x,
                                    (gap[1].y - gap[0].y) // 2 + gap[0].y                            
                                ),             isRay = False,
                                            angleSpecter = 90)
                                wall.gaps[i] = (gap[0], gap[1], False)     
                                WAVE_LIST.append(newWave)
                    except:
                        if not self.intensityMap:
                            self.intensityMap = True
                            gradientRect(display, [
                                (0, 0, 0),
                                (0, 0, 0),
                                (0, 0, 0),
                                (200, 200, 200, 75),
                                (0, 0, 0),
                                (200, 200, 200, 100),
                                (0, 0, 0),
                                (200, 200, 200, 125),
                                (0, 0, 0),
                                (200, 200, 200, 150),
                                (0, 0, 0),
                                (200, 200, 200, 200),
                                (0, 0, 0),
                                (200, 200, 200, 255),
                                (0, 0, 0),
                                (200, 200, 200, 200),
                                (0, 0, 0),
                                 (200, 200, 200, 150),
                                (0, 0, 0),
                                (200, 200, 200, 125),
                                (0, 0, 0),
                                (200, 200, 200, 100),
                                (0, 0, 0),
                                (200, 200, 200, 75),
                                (0, 0, 0),
                                (0, 0, 0),
                                (0, 0, 0),                                
                                ], pygame.Rect(wall.BR.x, 0, 1000-wall.BR.x, 1000))
                                    
                    
            if canDrawPos:
                s = pygame.Surface((2, 2), pygame.SRCALPHA )
                alpha = 255 * (height) / 2
                if alpha > 0:
                    s.fill((255, 255, 0, abs(alpha)/255*10))
                else:
                    s.fill((0, 255, 255, abs(alpha)/255*10))
                
                display.blit(s, pos)
                # pygame.draw.circle(display, (0, 0, 255 * (height+self.amplitude)/4), pos, 1)

class Button:
    def __init__(self, x, y, text, bg_color=(50, 50, 50), fg_color=(255, 255, 255)) -> None:
        self.TL = (x, y)
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        font = pygame.font.SysFont('arial', 70)        
        text = font.render(self.text, True, self.fg_color, self.bg_color)
        text_rect = text.get_rect()
        self.rect = pygame.Rect(self.TL[0], self.TL[1], text_rect.width, text_rect.height)
        
    def draw(self, display: pygame.surface.Surface):
        
        font = pygame.font.SysFont('arial', 70)        
        text = font.render(self.text, True, self.fg_color, self.bg_color)
        text_rect = text.get_rect()
        self.rect = pygame.Rect(self.TL[0], self.TL[1], text_rect.width, text_rect.height)
        display.blit(text, self.TL)
           
class Entry:
    def __init__(self, x, y, text='') -> None:
        self.font = pygame.font.Font(None, 32)
        self.rect = pygame.Rect(x, y, 10*4, 32)
        self.active = False
        self.text = bytes(str(text), 'utf-8')



    def draw(self, display: pygame.Surface):
        self.txt_surface = self.font.render(self.text, True, (255, 255, 255))
        width = max(10*4, self.txt_surface.get_width()+10)
        self.rect.w = width
        display.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(display, (150, 150, 150), self.rect, 2)

class Label:
    def __init__(self, x, y, text, multiline=False, size=32, font=None) -> None:
        self.font = pygame.font.SysFont(font, size)
        self.txt_surface = self.font.render(text, True, (255, 255, 255))
        self.rect = pygame.Rect(x, y, self.txt_surface.get_width(), size)
        self.text = text
        self.multiline = multiline
    
    def draw(self, display: pygame.Surface):
        if self.multiline:
            return self.blit_text(display)
        txt_surface = self.font.render(self.text, True, (255, 255, 255))
        display.blit(txt_surface, (self.rect.x+5, self.rect.y+5))
        # pygame.draw.rect(display, (150, 150, 150), self.inputBox, 2)

    def blit_text(self, surface, color=pygame.Color('white')):
        words = [word.split(' ') for word in self.text.splitlines()]  # 2D array where each row is a list of words.
        space = self.font.size(' ')[0]  # The width of a space.
        max_width, max_height = surface.get_size()
        x, y = self.rect.x, self.rect.y
        for line in words:
            for word in line:
                word_surface = self.font.render(word, 0, color)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x = self.rect.x  # Reset the x.
                    y += word_height  # Start on new row.
                surface.blit(word_surface, (x, y))
                x += word_width + space
            x = self.rect.x # Reset the x.
            y += word_height  # Start on new row.

class Circle:
    def __init__(self, x, y, radius, color) -> None:
        self.pos = (x, y)
        self.radius = radius
        self.color = color

    def draw(self, display):
        pygame.draw.circle(display, self.color, self.pos, self.radius)

class Box:
    def __init__(self, x, y, width, height, wingets=None, color=(100, 100, 100)) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.wingets = wingets
        self.color = color

    def draw(self, display):
        pygame.draw.rect(display, self.color, self.rect)
        for winget in self.wingets:
            winget.draw(display)

def main():
    global WAVE_LIST
    pygame.init()
    
    # ray = Wave((100, 500), rayWidth=1000, isRay=False, angleSpecter=90)
    ray = Wave((0, 500), rayWidth=1000)
    wall1 = WallGap((195, 0), (205, 1000), [(495, 505)])
    wall2 = WallGap((495, 0), (505, 1000), [(395, 405), (595, 605)])
    wall3 = Wall((815, 0), (825, 1000))
    
    WAVE_LIST.append(ray)
    WALL_LIST.append(wall1)
    WALL_LIST.append(wall2)
    WALL_LIST.append(wall3)
    
    anotationLabel = Label(650, 950, 
                           "Nota: la pantalla realment és una versió escalada\nde la franga d'interferència de les dues ones.", 
                           True, size=16, font='arial')
    anotationBox = Box(645, 945, 300, 50, [anotationLabel])
    
    
    # llegenda
    crestColor = Circle(50, 40, 15, (255, 255, 0))
    crestLabel = Label(20, 60, "Cresta", size=16, font='Arial')
    dumbColor = Circle(110, 40, 15, (0, 255, 255))
    dumbLabel = Label(93, 60, "Vall", size=16, font='Arial')
    destructiveColor = Circle(184, 40, 15, (0, 255, 0))
    destructiveLabel = Label(149, 60, "Interferència\n destructiva", size=16, multiline=True, font='Arial')
    legend = Box(10, 10, 250, 90, [
        crestColor, crestLabel, dumbColor, dumbLabel, destructiveColor, destructiveLabel
    ])


    DISPLAY = pygame.display.set_mode((1000, 1000), 0, pygame.SRCALPHA)
    CLOCK = pygame.time.Clock()
    
    # MAIN MENU
    simulationButton = Button(50, 40, "Simulació")
    optionButton = Button(50, 170, "Opcions")
    textButton = Button(50, 300, "Explicació")
    escLabel = Label(47, 500, "Prem la tecla 'Esc' per tornar al menu principal", size=30, font='gloria')
    youngTitle = Label(550, 50, "EXPERIMENT\nDE\nYOUNG", True, 72)
    autorsTitle = Label(550, 200, "Fet per: Jaume Majó i Josep Barnada", size=24, font="arial")
    shrekAprovedImage = pygame.image.load("data/shrekApproved.jpg").convert()
    bonusButton = Button(50, 405, "Bonus")
    video33 = cv2.VideoCapture("data/FA33.mp4")
    videoNanoFPS = video33.get(cv2.CAP_PROP_FPS)
    thanksButton = Button(600, 865, "Agraïments")
    ivanJediImage = pygame.image.load("data/OBIIVAN.png").convert()
    pygame.mixer.init()
    
    # THANKS MENU
    thanksText = Label(5, 5, multiline=True, size=28, font='Arial', text="""Hola Ivan, abans que surtis d'aquí et voldriem agraïr el teu esforç i la paciència. Esperem que t'ho hagis passat bé i hagis aprés molt al llarg d'aquesta experiència. Per últim, recorda que, tot i que l'animació pugui semblar senzilla, realment ha costat molt.

Agraïments:
A l'Ivan, per haver confiat sempre en nosaltres i haver executat aquest programa (espero que l'hagis obert). També voldríem agrair a en Genís pel seu mitiquíssim "BRAWL STARS" durant l'explicació. A en Fernando Alonso, pel seu meravellós mewing. A en Mike Wazowski (Ivan 2) i l'Avestrús per ser els pilars fonamentals en la creació d'aquest treball. I, com no podia faltar, l'Shrek, pel seu segell de qualitat indispensable per a la certificació del treball. Evidentment, a en Thomas Young, que sense els seus experiments no hagués estat possible aquest treball. També volem agrair a en Miquel Àngel per no posar pràctiques d'història sobre el Tema 9: La restauració democràtica, ja que el temps que haguéssim utilitzat en fer les pràctiques (33 hores), l'hem pogut invertir en acabar el projecte de YOUNG a temps. Finalment, NO volem agrair a l'Anna Puigdevall per haver vingut a fer de policia a una classe de física i per dubtar de les capacitats del professor del mestre Jedi Ivan Fernandez III.

Ara sí que has arribat al final del treball, abans, però, com que sabem que faràs un cop surtis d'aquí, mira aquest últim vídeo.
                      """)
    eldenRingButton = Button(325, 800, "Video Final")
    videoER = cv2.VideoCapture("data/EldenRing.mp4")
    videoER_FPS = videoER.get(cv2.CAP_PROP_FPS)
    ivanImage = pygame.image.load("data/ivanFacha.png").convert()
    ivanImage = pygame.transform.scale(ivanImage, (300, 300))
    trioImage = pygame.image.load("data/trio.png").convert()
    trioImage = pygame.transform.scale(trioImage, (300, 300))
    
    
    # OPTIONS MENU
    herzosLabel = Label(50, 50, "Freqüència:")
    herzos = Entry(200, 50, text="60 Hz")
    applySettings = Button(60, 150, "Aplicar")
    jajaLabel = Label(300, 40, "Ja t'agradaria Ivan", font='arial', size=32)
    ostrichImage = pygame.image.load('data/avestruz.png').convert()
    trollLabel = Label(50, 90, "Ivan prova de modificar la freqüència, 60 Hz és molt poca cosa.", font='arial', size=28)
    ostrich = False
    

    # EXPLANATION MENU
    brawlStarsImage = pygame.transform.scale(
        pygame.image.load('data/brawlStars.png').convert_alpha(), (500, 190))
    
    textLabel = Label(5, 5, multiline=True, size=28, font='Arial', text="""L'experiment de Young va ser portat a terme pel científic anglès Thomas Young (1773-1829)
el 1804, és a dir, dos anys abans de tenir 33 anys. Aquest experiment va servir per validar el 
model ondulatori, mentre que el corpuscular va ser rebutjat.
                      
Aquest experiment consisteix en un mirall que fa reflectir la llum del Sol per un petit forat a la 
finestra. Després, aquesta llum es divideix en dos raigs pràcticament iguals (que actuen 
com una nova font d'emissió) a través de dues escletxes d'una làmina de cartó gràcies al 
fenomen de la difracció (el canvi en la direcció de propagació que rep una ona quan es 
troba amb un obstacle amb unes mides, aproximadament, més petites o iguals que la 
longitud d'ona). Aquests dos raigs interfereixen entre ells, de manera que es creen 
interferències constructives i destructives, i donen lloc al patró d'interferència. En aquest, es 
poden observar les diferents franges, clares o fosques, que coincideixen amb els patrons 
d'interferència constructiva i destructiva.

Ara, però, quan es parla o s'explica l'experiment de Young, es fa referència a l'experiment 
de la doble escletxa, que té un funcionament molt semblant, però incorpora millores pel que 
fa al patró d'interferències. Aquest consisteix en una font de llum que xoca en una paret 
opaca la qual té una petita escletxa (la qual, com s'ha dit abans, ha de tenir unes 
dimensions iguals o inferiors la longitud d'ona del feix de llum). El feix, a causa de la 
difracció, generarà un nou raig i, aquest, xocarà amb una altra paret (situada al davant de 
l'altra) que tindrà dues escletxes. De la mateixa manera, aquest raig, quan incideix en 
cada escletxa, dona lloc a dues noves fonts emissores i, conseqüentment, dos raigs coherents 
(és a dir, que tenen la mateixa amplitud i freqüència i amb un desfasament constant) de llum. 
Després, aquests raigs xocaran a una tercera paret i, gràcies a una pantalla, es podran 
visualitzar els diferents patrons d'interferència (constructiva i destructiva) dels dos raigs.
                      
                      
""")
    textLabel.multiline = True

    # MANU = MAIN SIMULATION OPTIONS
    MENU = "MAIN"
    playVideoFA = False
    playAudioFA = False
    playVideoER = False
    playAudioER = False
    
    while RUNNING:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                closeGame()
            
            if event.type == pygame.MOUSEBUTTONDOWN and playVideoFA == False and playVideoER == False:
                if simulationButton.rect.collidepoint(event.pos) and MENU == "MAIN":
                    MENU = "SIMULATION"
                    DISPLAY.fill((0, 0, 0))
                
                elif optionButton.rect.collidepoint(event.pos) and MENU == "MAIN":
                    MENU = "OPTIONS"
                    DISPLAY.fill((0, 0, 0))

                elif textButton.rect.collidepoint(event.pos) and MENU == "MAIN":
                    MENU = "EXPLANATION"
                    pygame.mixer.music.load("data/BrawlStars.mp3")
                    pygame.mixer.music.play()
                    DISPLAY.fill((0, 0, 0))
                    
                elif bonusButton.rect.collidepoint(event.pos) and MENU == "MAIN":
                    if not playVideoFA:
                        playVideoFA = True
                        pygame.mixer.music.load("data/FA33.mp3")
                
                elif eldenRingButton.rect.collidepoint(event.pos) and MENU == "THANKS":
                    if not playVideoER:
                        playVideoER = True
                        pygame.mixer.music.load("data/EldenRing.mp3")
                
                elif thanksButton.rect.collidepoint(event.pos) and MENU == "MAIN":
                    MENU = "THANKS"
                    DISPLAY.fill((0, 0, 0))
                    
                elif herzos.rect.collidepoint(event.pos) and MENU == "OPTIONS":
                    jajaLabel.draw(DISPLAY)
                    pygame.display.update()
                    
                    time.sleep(2)
                    webbrowser.open('https://www.pccomponentes.com/asus-tuf-gaming-vg279q1r-27-led-ips-fullhd-144hz-freesync')
                    time.sleep(0.5)
                    ostrich = True

            if event.type == pygame.KEYDOWN and MENU != "MAIN" and not playVideoER:
                if event.key == 27:
                    DISPLAY.fill((0, 0, 0))
                    for wave in WAVE_LIST:
                        wave.canDraw = True
                        wave.time = 0
                    
                    for i, gap in enumerate(wall1.gaps):
                        wall1.gaps[i] = (gap[0], gap[1], True)
                                                
                    for i, gap in enumerate(wall2.gaps):                  
                        wall2.gaps[i] = (gap[0], gap[1], True)
                                                
                    WAVE_LIST = [ray]
                    MENU = "MAIN"
                
        if MENU == "MAIN":
            simulationButton.draw(DISPLAY)
            optionButton.draw(DISPLAY)
            textButton.draw(DISPLAY)
            escLabel.draw(DISPLAY)
            youngTitle.draw(DISPLAY)
            autorsTitle.draw(DISPLAY)
            DISPLAY.blit(ivanJediImage, (575, 350))
            DISPLAY.blit(shrekAprovedImage, (50, 550))
            bonusButton.draw(DISPLAY)
            thanksButton.draw(DISPLAY)
            if playVideoFA:
                if not playAudioFA:
                    pygame.mixer.music.play()
                    playAudioFA = True
                success, frame = video33.read()
                if success:
                    resizedFrame = cv2.resize(frame, (1000//16*9, 1000))
                    video_surf = pygame.image.frombuffer(resizedFrame.tobytes(), resizedFrame.shape[1::-1], "BGR")
                    DISPLAY.blit(video_surf, (233, 0))
                else:
                    playAudioFA = False
                    playVideoFA = False
                    video33.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    
        elif MENU == "OPTIONS":
            herzos.draw(DISPLAY)
            herzosLabel.draw(DISPLAY)
            applySettings.draw(DISPLAY)
            trollLabel.draw(DISPLAY)
            if ostrich:
                DISPLAY.blit(ostrichImage, (125, 200))
            

        elif MENU == "EXPLANATION":
            textLabel.draw(DISPLAY)
            DISPLAY.blit(brawlStarsImage, (230, 820))

        elif MENU == "THANKS":
            thanksText.draw(DISPLAY)
            DISPLAY.blit(ivanImage, (50, 650))
            DISPLAY.blit(trioImage, (650, 650))
            eldenRingButton.draw(DISPLAY)
            if playVideoER:
                if not playAudioER:
                    pygame.mixer.music.play()
                    playAudioER = True
                success, frame = videoER.read()
                if success:
                    resizedFrame = cv2.resize(frame, (1000//16*9, 1000))
                    video_surf = pygame.image.frombuffer(resizedFrame.tobytes(), resizedFrame.shape[1::-1], "BGR")
                    DISPLAY.blit(video_surf, (233, 0))
                else:
                    playAudioER = False
                    playVideoER = False
                    videoER.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    
        if MENU == "SIMULATION":
            for wave in WAVE_LIST:
                wave.draw(DISPLAY)

            for wall in WALL_LIST:
                wall.draw(DISPLAY)
            
            legend.draw(DISPLAY)
            anotationBox.draw(DISPLAY)
        pygame.display.update()
        
        if MENU == "MAIN":
            CLOCK.tick(videoNanoFPS)
        elif MENU == "THANKS":
            CLOCK.tick(videoER_FPS)
        else:
            CLOCK.tick()
        pygame.display.set_caption(F"Experiment de YOUNG")

if __name__ == '__main__':
    main()
