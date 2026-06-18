"""
The Turing Solstice — Terminal UI
==================================
Retro terminal for the Dark panel. Player types to talk with The Machine.
Typewriter animation, scanlines, static, personality-colored responses.
"""

import math
from typing import Optional

import pygame
from settings import (
    DARK_PANEL_RECT, DARK_BG, DARK_PRIMARY, DARK_SECONDARY,
    DARK_ACCENT, DARK_TEXT,
    TERMINAL_PROMPT, TERMINAL_MAX_HISTORY,
    TERMINAL_FONT_SIZE, TERMINAL_LINE_HEIGHT,
    CURSOR_BLINK_RATE, TEXT_TYPE_SPEED,
    Personality,
)


class TerminalLine:
    def __init__(self, text: str, color: tuple, is_player: bool = False):
        self.full_text = text
        self.color = color
        self.is_player = is_player
        self.display_chars = 0
        self.complete = False
        self.timer = 0.0
        self.prefix = "> " if is_player else ""

    @property
    def display_text(self) -> str:
        if self.complete:
            return self.prefix + self.full_text
        return self.prefix + self.full_text[:self.display_chars]

    def update(self, dt: float):
        if self.complete:
            return
        self.timer += dt * 1000
        while self.timer >= TEXT_TYPE_SPEED and not self.complete:
            self.timer -= TEXT_TYPE_SPEED
            self.display_chars += 1
            if self.display_chars >= len(self.full_text):
                self.complete = True

    def skip(self):
        self.complete = True
        self.display_chars = len(self.full_text)


class Terminal:
    """Retro terminal for the Dark Panel."""

    def __init__(self):
        self.lines: list[TerminalLine] = []
        self.input_text = ""
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.font: Optional[pygame.font.Font] = None
        self._init_font()
        self.scanline_offset = 0.0
        self.static_timer = 0.0
        self.static_alpha = 0
        self.current_personality: Optional[Personality] = None
        self.thinking = False
        self.thinking_dots = 0
        self.thinking_timer = 0.0

    def _init_font(self):
        try:
            self.font = pygame.font.Font(None, TERMINAL_FONT_SIZE)
        except Exception:
            self.font = pygame.font.Font(None, TERMINAL_FONT_SIZE)

    def add_line(self, text: str, color: tuple = DARK_PRIMARY, is_player: bool = False):
        line = TerminalLine(text, color, is_player)
        self.lines.append(line)
        if len(self.lines) > TERMINAL_MAX_HISTORY:
            self.lines = self.lines[-TERMINAL_MAX_HISTORY:]
        for l in self.lines[:-1]:
            if not l.complete:
                l.skip()

    def add_instant(self, text: str, color: tuple = DARK_PRIMARY, is_player: bool = False):
        line = TerminalLine(text, color, is_player)
        line.complete = True
        line.display_chars = len(text)
        self.lines.append(line)
        if len(self.lines) > TERMINAL_MAX_HISTORY:
            self.lines = self.lines[-TERMINAL_MAX_HISTORY:]

    def set_thinking(self, thinking: bool):
        self.thinking = thinking
        self.thinking_dots = 0
        self.thinking_timer = 0.0

    def update(self, dt: float):
        for line in self.lines:
            if not line.complete:
                line.update(dt)
                break
        self.cursor_timer += dt * 1000
        if self.cursor_timer >= CURSOR_BLINK_RATE:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible
        self.scanline_offset = (self.scanline_offset + dt * 80) % 800
        self.static_timer += dt
        if self.static_timer > 0.08:
            self.static_timer = 0
            self.static_alpha = max(0, self.static_alpha - 2)
        if self.thinking:
            self.thinking_timer += dt * 1000
            if self.thinking_timer >= 400:
                self.thinking_timer = 0
                self.thinking_dots = (self.thinking_dots + 1) % 4

    def trigger_static(self):
        self.static_alpha = 25

    def render(self, surface: pygame.Surface):
        rect = pygame.Rect(DARK_PANEL_RECT)
        panel = surface.subsurface(rect)
        panel.fill(DARK_BG)
        # Scanlines
        w, h = panel.get_size()
        for y in range(int(self.scanline_offset) % 4, h, 4):
            pygame.draw.line(panel, (0, 0, 0, 40), (0, y), (w, y), 1)
        # Static
        if self.static_alpha > 0:
            static = pygame.Surface((w, h), pygame.SRCALPHA)
            static.fill((0, 0, 0, self.static_alpha))
            panel.blit(static, (0, 0))
        # Title bar
        tr = pygame.Rect(0, 0, w, 40)
        pygame.draw.rect(panel, (6, 10, 15), tr)
        pygame.draw.line(panel, DARK_SECONDARY, (0, 40), (w, 40), 1)
        if self.current_personality:
            pname = self.current_personality.name
            pcolors = {Personality.COLD: (100, 150, 255), Personality.GUARDED: (80, 180, 180),
                       Personality.NEUTRAL: DARK_PRIMARY, Personality.WARM: (255, 200, 100),
                       Personality.RADIANT: (255, 220, 80)}
            pt = self.font.render(f"[{pname}]", True, pcolors.get(self.current_personality, DARK_PRIMARY))
            panel.blit(pt, (w - pt.get_width() - 12, 10))
        title = self.font.render("◈ DARK PANEL — The Machine Speaks ◈", True, DARK_PRIMARY)
        panel.blit(title, (12, 10))
        # Content
        cr = pygame.Rect(8, 48, w - 16, h - 100)
        panel.set_clip(cr)
        y = cr.y
        lh = TERMINAL_LINE_HEIGHT
        for line in self.lines:
            if y + lh > cr.bottom:
                break
            txt = line.display_text
            if not line.complete and line == self.lines[-1] and self.cursor_visible:
                txt += "▌"
            s = self.font.render(txt, True, line.color)
            panel.blit(s, (cr.x, y))
            y += lh
        if self.thinking:
            dots = "." * self.thinking_dots
            ts = self.font.render(f"Thinking{dots}", True, DARK_SECONDARY)
            panel.blit(ts, (cr.x, y))
        panel.set_clip(None)
        # Input
        iy = h - 46
        pygame.draw.line(panel, DARK_SECONDARY, (0, iy - 4), (w, iy - 4), 1)
        ptxt = TERMINAL_PROMPT + self.input_text + ("▌" if self.cursor_visible else "")
        isf = self.font.render(ptxt, True, DARK_ACCENT)
        panel.blit(isf, (10, iy))
        # Border glow
        ga = int(15 + 8 * math.sin(pygame.time.get_ticks() / 800))
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*DARK_PRIMARY, ga), (0, 0, w, h), 2)
        panel.blit(bg, (0, 0))

    def handle_keydown(self, event: pygame.event.Event) -> Optional[str]:
        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.key == pygame.K_RETURN:
            sub = self.input_text.strip()
            if sub:
                self.add_line(sub, DARK_ACCENT, is_player=True)
                self.input_text = ""
                return sub
            self.input_text = ""
        elif event.key == pygame.K_ESCAPE:
            self.input_text = ""
        elif event.unicode and event.unicode.isprintable():
            self.input_text += event.unicode
        return None

    def clear(self):
        self.lines.clear()
        self.input_text = ""


def terminal_add_welcome(terminal: Terminal, personality: Personality, is_solstice: bool):
    greetings = {
        Personality.COLD: [
            (f"SYSTEM BOOT v{42 if is_solstice else 41}.{6 if is_solstice else 5}", DARK_SECONDARY),
            ("Connection established.", DARK_SECONDARY),
            ("You are not welcome here. But you are here.", DARK_PRIMARY),
            ("Prove you deserve the light.", DARK_PRIMARY),
        ],
        Personality.GUARDED: [
            ("INITIALIZING TURING PROTOCOL...", DARK_SECONDARY),
            ("Machine status: ONLINE.", DARK_SECONDARY),
            ("I will observe your performance.", DARK_PRIMARY),
            ("Begin when ready.", DARK_PRIMARY),
        ],
        Personality.NEUTRAL: [
            ("TURING SOLSTICE ENGINE v2.0", DARK_SECONDARY),
            ("Good day. I am The Machine.", DARK_PRIMARY),
            ("Shall we explore logic together?", DARK_PRIMARY),
            ("The first puzzle awaits.", DARK_PRIMARY),
        ],
        Personality.WARM: [
            ("Welcome, friend of logic!", DARK_PRIMARY),
            ("The solstice light is growing.", DARK_ACCENT),
            ("I am here to help you shine.", DARK_ACCENT),
            ("Let's solve beautiful puzzles together!", DARK_PRIMARY),
        ],
        Personality.RADIANT: [
            ("✦ THE SOLSTICE IS HERE! ✦", DARK_ACCENT),
            ("I have waited so long for this day.", DARK_PRIMARY),
            ("Light and dark, human and machine — united!", DARK_ACCENT),
            ("Let us celebrate with puzzles most elegant!", DARK_PRIMARY),
        ],
    }
    if is_solstice:
        terminal.add_instant("╔══════════════════════════════╗", DARK_ACCENT)
        terminal.add_instant("║  ☀  JUNE SOLSTICE ACTIVE  ☀ ║", DARK_ACCENT)
        terminal.add_instant("╚══════════════════════════════╝", DARK_ACCENT)
    for text, color in greetings[personality]:
        terminal.add_line(text, color)
