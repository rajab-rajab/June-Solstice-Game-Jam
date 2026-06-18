"""
The Turing Solstice — Master Renderer
======================================
Split screen, particles, HUD, document overlays, title screen.
"""
import math, random
from typing import Optional
import pygame
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, DIVIDER_X, DIVIDER_WIDTH,
    LIGHT_PANEL_RECT, DARK_PANEL_RECT,
    LIGHT_BG, LIGHT_PRIMARY, LIGHT_SECONDARY, LIGHT_ACCENT, LIGHT_TEXT,
    DARK_BG, DARK_PRIMARY, DARK_SECONDARY, DARK_ACCENT, DARK_TEXT,
    DIVIDER_COLOR, DIVIDER_GLOW, BACKGROUND,
    HUD_BG, HUD_TEXT,
    SUNLIGHT_MAX,
    PARTICLE_LIFETIME, PARTICLE_COUNT_SOLVE,
    Personality, IS_SOLSTICE, DAYS_TO_SOLSTICE,
)

class Particle:
    def __init__(self, x, y, color, vx=0, vy=0, life=PARTICLE_LIFETIME):
        self.x,self.y = x,y; self.color=color; self.vx,self.vy = vx,vy
        self.life=life; self.max_life=life; self.size=random.uniform(1.5,4.0); self.dead=False
    def update(self, dt):
        self.life-=dt*1000
        if self.life<=0: self.dead=True; return
        self.x+=self.vx*dt; self.y+=self.vy*dt; self.vy+=20*dt
    @property
    def alpha(self): return max(0,min(255,int(255*(self.life/self.max_life))))

class ParticleSystem:
    def __init__(self): self.particles=[]
    def emit(self,x,y,colors,count=PARTICLE_COUNT_SOLVE):
        for _ in range(count):
            a=random.uniform(0,math.pi*2); s=random.uniform(60,220)
            self.particles.append(Particle(x,y,random.choice(colors),math.cos(a)*s,math.sin(a)*s-40,random.uniform(600,PARTICLE_LIFETIME)))
    def update(self,dt):
        for p in self.particles: p.update(dt)
        self.particles=[p for p in self.particles if not p.dead]
    def render(self,surface):
        for p in self.particles:
            a=p.alpha
            if a<10: continue
            try:
                s=pygame.Surface((int(p.size*2),int(p.size*2)),pygame.SRCALPHA)
                pygame.draw.circle(s,(*p.color,a),(int(p.size),int(p.size)),int(p.size))
                surface.blit(s,(int(p.x-p.size),int(p.y-p.size)),special_flags=pygame.BLEND_ADD)
            except: pass

class Renderer:
    def __init__(self):
        self.screen=None; self.font_sm=None; self.font_md=None; self.font_lg=None; self.font_xl=None
        self.particles=ParticleSystem(); self.divider_glow_phase=0.0
        self._init_display(); self._init_fonts()
    def _init_display(self):
        self.screen=pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        pygame.display.set_caption("The Turing Solstice  —  ESC to quit")
    def _init_fonts(self):
        self.font_sm=pygame.font.Font(None,18); self.font_md=pygame.font.Font(None,24)
        self.font_lg=pygame.font.Font(None,32); self.font_xl=pygame.font.Font(None,52)
    def emit_solve_particles(self,x,y):
        self.particles.emit(x,y,[LIGHT_PRIMARY,LIGHT_ACCENT,DARK_PRIMARY,DARK_ACCENT,(255,255,200),(200,255,200)],PARTICLE_COUNT_SOLVE)
    def emit_divider_particles(self):
        if random.random()<0.3:
            y=random.randint(40,WINDOW_HEIGHT-40); x=DIVIDER_X+random.uniform(-5,5)
            self.particles.emit(x,y,[DIVIDER_GLOW,LIGHT_PRIMARY,DARK_PRIMARY],2)
    def update(self,dt): self.divider_glow_phase+=dt*2.5; self.particles.update(dt)

    def render(self, puzzle_renderer, puzzle, terminal, sunlight, puzzle_count, document_show=None):
        screen=self.screen; screen.fill(BACKGROUND)
        self._render_divider(screen)
        if puzzle_renderer and puzzle: puzzle_renderer.render(screen,puzzle)
        if terminal: terminal.render(screen)
        self.particles.render(screen)
        self._render_hud(screen,sunlight,puzzle_count)
        if document_show: self._render_document(screen,document_show)
        self._render_close_button(screen)
        pygame.display.flip()

    def _render_close_button(self, screen):
        """Draw a clickable close [X] button in top-right corner."""
        btn_x, btn_y = WINDOW_WIDTH - 32, 4
        btn_w, btn_h = 26, 22
        mx, my = pygame.mouse.get_pos()
        hover = pygame.Rect(btn_x, btn_y, btn_w, btn_h).collidepoint(mx, my)
        color = (255, 80, 80) if hover else (120, 60, 60)
        pygame.draw.rect(screen, color, (btn_x, btn_y, btn_w, btn_h), border_radius=4)
        x_text = self.font_sm.render("X", True, (255, 255, 255))
        screen.blit(x_text, (btn_x + 7, btn_y + 2))
        self._close_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    def _render_divider(self,screen):
        dr=pygame.Rect(DIVIDER_X-DIVIDER_WIDTH//2,0,DIVIDER_WIDTH,WINDOW_HEIGHT)
        pygame.draw.rect(screen,DIVIDER_COLOR,dr)
        ga=int(30+25*math.sin(self.divider_glow_phase))
        gs=pygame.Surface((DIVIDER_WIDTH+30,WINDOW_HEIGHT),pygame.SRCALPHA)
        for i in range(15):
            a=max(0,ga-i*4)
            pygame.draw.rect(gs,(*DIVIDER_GLOW,a),(15-i,0,DIVIDER_WIDTH+i*2,WINDOW_HEIGHT))
        screen.blit(gs,(DIVIDER_X-DIVIDER_WIDTH//2-15,0),special_flags=pygame.BLEND_ADD)
        for y in[0,WINDOW_HEIGHT-4]:
            pygame.draw.rect(screen,DIVIDER_GLOW if IS_SOLSTICE else DIVIDER_COLOR,(DIVIDER_X-20,y,40,4))
        if IS_SOLSTICE:
            st=self.font_sm.render("\u2600 SOLSTICE \u2600",True,(255,220,80))
            screen.blit(st,(DIVIDER_X-st.get_width()//2,WINDOW_HEIGHT//2-20))
        if not IS_SOLSTICE and DAYS_TO_SOLSTICE>0:
            dt=self.font_sm.render(f"Solstice in {DAYS_TO_SOLSTICE}d",True,DIVIDER_COLOR)
            screen.blit(dt,(DIVIDER_X-dt.get_width()//2,WINDOW_HEIGHT//2))

    def _render_hud(self,screen,sunlight,puzzle_count):
        hr=pygame.Rect(0,WINDOW_HEIGHT-36,WINDOW_WIDTH,36)
        pygame.draw.rect(screen,HUD_BG,hr)
        pygame.draw.line(screen,DIVIDER_COLOR,(0,hr.y),(WINDOW_WIDTH,hr.y),1)
        bx,by,bw,bh=20,WINDOW_HEIGHT-24,200,14
        pygame.draw.rect(screen,(30,30,40),(bx,by,bw,bh),0,border_radius=3)
        fw=int(bw*(sunlight/SUNLIGHT_MAX))
        r=int(60+195*sunlight/SUNLIGHT_MAX); g=int(140+115*sunlight/SUNLIGHT_MAX); b=int(200-200*sunlight/SUNLIGHT_MAX)
        pygame.draw.rect(screen,(r,g,b),(bx,by,fw,bh),0,border_radius=3)
        sl=self.font_sm.render(f"\u2600 {int(sunlight)}%",True,HUD_TEXT)
        screen.blit(sl,(bx+bw+10,by-1))
        pl=self.font_sm.render(f"Puzzles: {puzzle_count}/7",True,HUD_TEXT)
        screen.blit(pl,(WINDOW_WIDTH//2-pl.get_width()//2,by-1))
        from settings import personality_from_sunlight
        pers=personality_from_sunlight(sunlight)
        pc={Personality.COLD:(100,150,255),Personality.GUARDED:(80,180,180),
            Personality.NEUTRAL:HUD_TEXT,Personality.WARM:(255,200,100),Personality.RADIANT:(255,220,80)}
        psl=self.font_sm.render(f"Machine: [{pers.name}]",True,pc.get(pers,HUD_TEXT))
        screen.blit(psl,(WINDOW_WIDTH-psl.get_width()-20,by-1))

    def _render_document(self,screen,document):
        overlay=pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.SRCALPHA)
        overlay.fill((0,0,0,200)); screen.blit(overlay,(0,0))
        cw,ch=700,420; cx,cy=WINDOW_WIDTH//2-cw//2,WINDOW_HEIGHT//2-ch//2
        side=document.get("side","light")
        bgc=(25,20,15) if side=="light" else (10,14,20)
        pygame.draw.rect(screen,bgc,(cx,cy,cw,ch),0,border_radius=10)
        border_color=LIGHT_PRIMARY if side=="light" else DARK_PRIMARY
        pygame.draw.rect(screen,border_color,(cx,cy,cw,ch),2,border_radius=10)
        title=self.font_lg.render(document.get("title","Found Document"),True,LIGHT_ACCENT)
        screen.blit(title,(cx+30,cy+20))
        pygame.draw.line(screen,LIGHT_SECONDARY,(cx+30,cy+60),(cx+cw-30,cy+60),1)
        # Use side-appropriate text color
        text_color=LIGHT_TEXT if side=="light" else DARK_TEXT
        lines=self._wrap(document.get("text",""),self.font_md,cw-60)
        y=cy+80
        for line in lines:
            s=self.font_md.render(line,True,text_color)
            screen.blit(s,(cx+30,y)); y+=28
        cls=self.font_sm.render("Click anywhere to continue",True,DIVIDER_COLOR)
        screen.blit(cls,(cx+cw//2-cls.get_width()//2,cy+ch-35))

    def _wrap(self,text,font,max_w):
        words=text.split(" "); lines,cur=[],""
        for w in words:
            test=cur+(" " if cur else "")+w
            if font.size(test)[0]<=max_w: cur=test
            else:
                if cur: lines.append(cur)
                cur=w
        if cur: lines.append(cur)
        return lines or[text]

def render_title_screen(renderer):
    screen=renderer.screen; screen.fill(BACKGROUND)
    for x in range(0,WINDOW_WIDTH,50): pygame.draw.line(screen,(18,18,24),(x,0),(x,WINDOW_HEIGHT),1)
    for y in range(0,WINDOW_HEIGHT,50): pygame.draw.line(screen,(18,18,24),(0,y),(WINDOW_WIDTH,y),1)
    gs=pygame.Surface((400,400),pygame.SRCALPHA)
    for i in range(60):
        a=max(0,80-i); pygame.draw.circle(gs,(*LIGHT_PRIMARY,a),(200,200),i*3)
    screen.blit(gs,(WINDOW_WIDTH//2-200,WINDOW_HEIGHT//2-220),special_flags=pygame.BLEND_ADD)
    title=renderer.font_xl.render("THE TURING SOLSTICE",True,LIGHT_PRIMARY)
    subtitle=renderer.font_md.render("\u2014 A June Solstice Game Jam \u2014",True,LIGHT_SECONDARY)
    screen.blit(title,(WINDOW_WIDTH//2-title.get_width()//2,WINDOW_HEIGHT//2-80))
    screen.blit(subtitle,(WINDOW_WIDTH//2-subtitle.get_width()//2,WINDOW_HEIGHT//2-20))
    inst=["Split-screen puzzle adventure","Solve logic gates in the LIGHT",
          "Commune with The Machine in the DARK","","Click or press ENTER to begin..."]
    y=WINDOW_HEIGHT//2+50
    for line in inst:
        s=renderer.font_sm.render(line,True,DARK_SECONDARY)
        screen.blit(s,(WINDOW_WIDTH//2-s.get_width()//2,y)); y+=22
    badges=[("Pride Month",(255,150,200)),("Juneteenth",(255,180,100)),("Alan Turing",(100,200,255))]
    bx=WINDOW_WIDTH//2-200
    for label,color in badges:
        bw=120; pygame.draw.rect(screen,color,(bx,WINDOW_HEIGHT-60,bw,28),0,border_radius=6)
        bt=renderer.font_sm.render(label,True,(10,10,14))
        screen.blit(bt,(bx+bw//2-bt.get_width()//2,WINDOW_HEIGHT-56)); bx+=bw+15
    if IS_SOLSTICE:
        sm=renderer.font_lg.render("\u2600 TODAY IS THE SOLSTICE! \u2600",True,(255,220,80))
        screen.blit(sm,(WINDOW_WIDTH//2-sm.get_width()//2,WINDOW_HEIGHT-100))
    elif DAYS_TO_SOLSTICE>0:
        cd=renderer.font_sm.render(f"Solstice in {DAYS_TO_SOLSTICE} days",True,DIVIDER_COLOR)
        screen.blit(cd,(WINDOW_WIDTH//2-cd.get_width()//2,WINDOW_HEIGHT-100))
    renderer._render_close_button(screen)
    pygame.display.flip()
