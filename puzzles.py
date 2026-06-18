"""
The Turing Solstice — Puzzle Engine
====================================
Logic gate puzzles, cipher decoding. All puzzle types defined and solvable here.
"""

import random
from typing import Optional
from enum import Enum, auto

import pygame
from settings import (
    LIGHT_PANEL_RECT, DARK_PANEL_RECT,
    LIGHT_PRIMARY, LIGHT_SECONDARY, LIGHT_ACCENT, LIGHT_TEXT, LIGHT_BG,
    DARK_PRIMARY, DARK_SECONDARY, DARK_ACCENT, DARK_TEXT, DARK_BG,
    PUZZLES_TO_WIN, PuzzleType,
)


class GateType(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


def evaluate_gate(gate: GateType, inputs: list[int]) -> int:
    if gate == GateType.AND:
        return 1 if all(i == 1 for i in inputs) else 0
    elif gate == GateType.OR:
        return 1 if any(i == 1 for i in inputs) else 0
    elif gate == GateType.NOT:
        return 0 if inputs[0] == 1 else 1
    return 0


class Puzzle:
    """A single puzzle instance."""

    def __init__(self, data: dict, ptype: PuzzleType, index: int):
        self.data = data
        self.ptype = ptype
        self.index = index
        self.solved = False
        self.attempts = 0
        self.hints_used = 0
        self.gate_type: Optional[GateType] = None
        if data.get("gate_type"):
            try:
                self.gate_type = GateType(data["gate_type"].upper())
            except (KeyError, ValueError):
                self.gate_type = None
        self.options = [GateType.AND, GateType.OR, GateType.NOT]
        random.shuffle(self.options)
        self.selected_option: Optional[GateType] = None
        self.player_text = ""
        self.show_result = False
        self.result_is_correct = False
        self.result_feedback = ""
        self.result_score = 5
        self.result_timer = 0.0

    @property
    def description(self) -> str: return self.data.get("description", "")
    @property
    def question(self) -> str: return self.data.get("question", "")
    @property
    def hint(self) -> str: return self.data.get("hint", "")
    @property
    def solution(self) -> str: return self.data.get("solution", "")
    @property
    def inputs(self) -> list[int]: return self.data.get("inputs", [0, 0])

    def check_answer(self, player_answer: str) -> bool:
        return player_answer.strip().lower() == self.solution.strip().lower()

    def set_result(self, feedback: str, score: int, correct: bool):
        self.show_result = True
        self.result_feedback = feedback
        self.result_score = score
        self.result_is_correct = correct
        self.result_timer = 3.5

    def update(self, dt: float):
        if self.show_result:
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.show_result = False


class PuzzleRenderer:
    """Renders puzzles on the light panel with retro aesthetic."""

    def __init__(self):
        self.font_sm: Optional[pygame.font.Font] = None
        self.font_md: Optional[pygame.font.Font] = None
        self.font_lg: Optional[pygame.font.Font] = None
        self._init_fonts()
        self.glow_phase = 0.0
        self.cursor_blink = True
        self.cursor_timer = 0.0

    def _init_fonts(self):
        try:
            self.font_sm = pygame.font.Font(None, 18)
            self.font_md = pygame.font.Font(None, 26)
            self.font_lg = pygame.font.Font(None, 38)
        except Exception:
            self.font_sm = pygame.font.Font(None, 18)
            self.font_md = pygame.font.Font(None, 26)
            self.font_lg = pygame.font.Font(None, 38)

    def render(self, surface: pygame.Surface, puzzle: Puzzle):
        rect = pygame.Rect(LIGHT_PANEL_RECT)
        panel = surface.subsurface(rect)
        panel.fill(LIGHT_BG)
        self._draw_grid(panel)
        # Title
        title_rect = pygame.Rect(0, 0, rect.width, 40)
        pygame.draw.rect(panel, (20, 15, 10), title_rect)
        pygame.draw.line(panel, LIGHT_SECONDARY, (0, 40), (rect.width, 40), 1)
        title = self.font_sm.render("◈ LIGHT PANEL — Solve the Logic ◈", True, LIGHT_PRIMARY)
        panel.blit(title, (rect.width // 2 - title.get_width() // 2, 10))
        content_y, content_x = 55, 20
        max_w = rect.width - 40
        desc_surf = self.font_md.render(puzzle.description, True, LIGHT_TEXT)
        panel.blit(desc_surf, (content_x, content_y))
        content_y += 35
        q_lines = self._wrap(puzzle.question, self.font_md, max_w)
        for line in q_lines:
            q_surf = self.font_md.render(line, True, LIGHT_PRIMARY)
            panel.blit(q_surf, (content_x, content_y))
            content_y += 30
        content_y += 15
        if puzzle.ptype == PuzzleType.GATE_SELECT:
            content_y = self._render_gate_select(panel, puzzle, content_x, content_y, max_w)
        elif puzzle.ptype == PuzzleType.CIPHER:
            content_y = self._render_cipher(panel, puzzle, content_x, content_y, max_w)
        else:
            content_y = self._render_generic(panel, puzzle, content_x, content_y, max_w)
        if puzzle.show_result:
            self._render_result(panel, puzzle, rect)

    def _draw_grid(self, panel):
        w, h = panel.get_size()
        for x in range(0, w, 40):
            pygame.draw.line(panel, (18, 14, 10), (x, 0), (x, h), 1)
        for y in range(0, h, 40):
            pygame.draw.line(panel, (18, 14, 10), (0, y), (w, y), 1)

    def _render_gate_select(self, panel, puzzle, cx, cy, max_w):
        inputs = puzzle.inputs
        in_text = f"INPUTS:  {'  '.join(str(i) for i in inputs)}"
        in_surf = self.font_lg.render(in_text, True, LIGHT_ACCENT)
        panel.blit(in_surf, (cx, cy))
        cy += 50
        node_r = 10
        input_x = cx + 40
        for i, val in enumerate(inputs):
            color = LIGHT_PRIMARY if val == 1 else LIGHT_SECONDARY
            pygame.draw.circle(panel, color, (input_x + i * 60, cy), node_r)
            pygame.draw.circle(panel, (255, 255, 255), (input_x + i * 60, cy), node_r, 1)
            lbl = self.font_sm.render(str(val), True, (0, 0, 0))
            panel.blit(lbl, (input_x + i * 60 - 4, cy - 6))
        cy += 40
        jx = input_x + (len(inputs) - 1) * 30
        for i in range(len(inputs)):
            st = (input_x + i * 60, cy - 40 + node_r)
            en = (jx, cy - 10)
            color = LIGHT_PRIMARY if inputs[i] == 1 else LIGHT_SECONDARY
            pygame.draw.line(panel, color, st, en, 2)
        pygame.draw.circle(panel, LIGHT_PRIMARY, (jx, cy - 10), 4)
        gate_x = jx + 60
        pygame.draw.line(panel, LIGHT_ACCENT, (jx, cy - 10), (gate_x, cy - 10), 2)
        pygame.draw.polygon(panel, LIGHT_ACCENT,
                            [(gate_x, cy - 10), (gate_x - 8, cy - 15), (gate_x - 8, cy - 5)])
        gate_rect = pygame.Rect(gate_x - 20, cy - 35, 70, 50)
        pygame.draw.rect(panel, LIGHT_SECONDARY, gate_rect, 2)
        gl = self.font_md.render("???", True, LIGHT_PRIMARY)
        panel.blit(gl, (gate_rect.centerx - 15, gate_rect.centery - 10))
        cy += 30
        out_x = gate_rect.right + 10
        pygame.draw.line(panel, LIGHT_ACCENT, (gate_rect.right, gate_rect.centery),
                         (out_x + 30, gate_rect.centery), 2)
        pygame.draw.circle(panel, LIGHT_PRIMARY, (out_x + 30, gate_rect.centery), 8)
        ol = self.font_sm.render("?", True, (0, 0, 0))
        panel.blit(ol, (out_x + 27, gate_rect.centery - 6))
        ql = self.font_md.render("Which gate is in the box?", True, LIGHT_ACCENT)
        panel.blit(ql, (cx, cy))
        cy += 40
        btn_w, btn_h = 120, 50
        total_w = len(puzzle.options) * btn_w + (len(puzzle.options) - 1) * 15
        start_x = cx + (max_w - total_w) // 2
        for i, gate in enumerate(puzzle.options):
            bx, by = start_x + i * (btn_w + 15), cy
            btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
            if puzzle.selected_option == gate:
                pygame.draw.rect(panel, LIGHT_PRIMARY, btn_rect, 0, border_radius=6)
                tc = (0, 0, 0)
            else:
                pygame.draw.rect(panel, LIGHT_SECONDARY, btn_rect, 2, border_radius=6)
                tc = LIGHT_PRIMARY
            gt = self.font_lg.render(gate.value, True, tc)
            panel.blit(gt, (btn_rect.centerx - gt.get_width() // 2,
                            btn_rect.centery - gt.get_height() // 2))
        cy += btn_h + 20
        if puzzle.selected_option is not None:
            sr = pygame.Rect(cx + max_w // 2 - 60, cy, 120, 40)
            pygame.draw.rect(panel, LIGHT_ACCENT, sr, 0, border_radius=4)
            st = self.font_md.render("SUBMIT", True, (0, 0, 0))
            panel.blit(st, (sr.centerx - st.get_width() // 2, sr.centery - st.get_height() // 2))
        return cy + 60

    def _render_cipher(self, panel, puzzle, cx, cy, max_w):
        cl = self.font_md.render("ENCRYPTED:", True, LIGHT_SECONDARY)
        panel.blit(cl, (cx, cy))
        cy += 28
        ct = self.font_lg.render(puzzle.question, True, LIGHT_PRIMARY)
        panel.blit(ct, (cx, cy))
        cy += 45
        il = self.font_md.render("Your decoding:", True, LIGHT_ACCENT)
        panel.blit(il, (cx, cy))
        cy += 28
        inp_r = pygame.Rect(cx, cy, max_w, 42)
        pygame.draw.rect(panel, LIGHT_SECONDARY, inp_r, 2, border_radius=3)
        disp = puzzle.player_text
        if self.cursor_blink:
            disp += "▌"
        inp_s = self.font_md.render(disp, True, LIGHT_PRIMARY)
        panel.blit(inp_s, (cx + 8, cy + 8))
        cy += 55
        if puzzle.player_text.strip():
            sr = pygame.Rect(cx + max_w // 2 - 60, cy, 120, 40)
            pygame.draw.rect(panel, LIGHT_ACCENT, sr, 0, border_radius=4)
            st = self.font_md.render("SUBMIT", True, (0, 0, 0))
            panel.blit(st, (sr.centerx - st.get_width() // 2, sr.centery - st.get_height() // 2))
        return cy + 60

    def _render_generic(self, panel, puzzle, cx, cy, max_w):
        msg = self.font_md.render("Solve the puzzle above.", True, LIGHT_TEXT)
        panel.blit(msg, (cx, cy))
        return cy + 40

    def _render_result(self, panel, puzzle, rect):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        alpha = min(180, int(puzzle.result_timer * 60))
        if puzzle.result_is_correct:
            overlay.fill((20, 50, 20, alpha))
        else:
            overlay.fill((50, 20, 20, alpha))
        panel.blit(overlay, (0, 0))
        color = (100, 255, 100) if puzzle.result_is_correct else (255, 120, 120)
        lines = self._wrap(puzzle.result_feedback, self.font_md, rect.width - 60)
        y = rect.height // 2 - len(lines) * 15
        for line in lines:
            fb = self.font_md.render(line, True, color)
            panel.blit(fb, (rect.width // 2 - fb.get_width() // 2, y))
            y += 28
        sc = self.font_lg.render(f"Machine Score: {puzzle.result_score}/10", True, LIGHT_ACCENT)
        panel.blit(sc, (rect.width // 2 - sc.get_width() // 2, y + 10))

    def _wrap(self, text, font, max_w):
        words = text.split(" ")
        lines, cur = [], ""
        for w in words:
            test = cur + (" " if cur else "") + w
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or [text]

    def get_clicked_option(self, puzzle, mx, my):
        if puzzle.ptype != PuzzleType.GATE_SELECT:
            return None
        lr = pygame.Rect(LIGHT_PANEL_RECT)
        if not lr.collidepoint(mx, my):
            return None
        lx, ly = mx - lr.x, my - lr.y
        btn_w, btn_h = 120, 50
        max_w = lr.width - 40
        total_w = len(puzzle.options) * btn_w + (len(puzzle.options) - 1) * 15
        start_x = 20 + (max_w - total_w) // 2
        cy_approx = 290
        for i, gate in enumerate(puzzle.options):
            bx = start_x + i * (btn_w + 15)
            by = cy_approx
            if bx <= lx <= bx + btn_w and by <= ly <= by + btn_h:
                return gate
        return None

    def get_submit_clicked(self, puzzle, mx, my):
        lr = pygame.Rect(LIGHT_PANEL_RECT)
        if not lr.collidepoint(mx, my):
            return False
        lx, ly = mx - lr.x, my - lr.y
        max_w = lr.width - 40
        sr = pygame.Rect(20 + max_w // 2 - 60, 360, 120, 40)
        if puzzle.ptype == PuzzleType.CIPHER:
            sr = pygame.Rect(20 + max_w // 2 - 60, 310, 120, 40)
        return sr.collidepoint(lx, ly) and (
            (puzzle.ptype == PuzzleType.GATE_SELECT and puzzle.selected_option is not None) or
            (puzzle.ptype == PuzzleType.CIPHER and puzzle.player_text.strip() != "")
        )


def create_puzzle_from_data(data: dict, index: int) -> Puzzle:
    ptype_str = data.get("gate_type", "")
    if ptype_str in ("AND", "OR", "NOT"):
        ptype = PuzzleType.GATE_SELECT
    elif data.get("cipher_type"):
        ptype = PuzzleType.CIPHER
    else:
        ptype = PuzzleType.GATE_SELECT
    return Puzzle(data, ptype, index)
