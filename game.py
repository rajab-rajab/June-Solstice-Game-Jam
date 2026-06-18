"""
The Turing Solstice — Game State Manager
=========================================
Orchestrates the game loop: states, puzzles, sunlight, documents, AI.
"""

import math
import random
from enum import Enum, auto
from typing import Optional

import pygame

from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, DIVIDER_X,
    SUNLIGHT_MAX, SUNLIGHT_START, SUNLIGHT_PER_PUZZLE,
    SUNLIGHT_DECAY_RATE, HINT_COST_SUNLIGHT,
    PUZZLES_TO_WIN, IS_SOLSTICE,
    Personality, personality_from_sunlight,
    FOUND_DOCUMENTS,
    LIGHT_PANEL_RECT, DARK_PANEL_RECT,
    DARK_PRIMARY, DARK_SECONDARY, DARK_ACCENT,
)
from gemini_client import GeminiClient, get_gemini_client
from puzzles import Puzzle, PuzzleRenderer, create_puzzle_from_data, GateType
from terminal import Terminal, terminal_add_welcome
from renderer import Renderer, render_title_screen


class GameState(Enum):
    TITLE       = auto()
    INTRO       = auto()
    PLAYING     = auto()
    DOCUMENT    = auto()
    EVALUATING  = auto()
    ENDING      = auto()
    CREDITS     = auto()


class Game:
    def __init__(self, api_key: Optional[str] = None):
        self.state = GameState.TITLE
        self.state_timer = 0.0
        self.renderer = Renderer()
        self.puzzle_renderer = PuzzleRenderer()
        self.terminal = Terminal()
        self.gemini: GeminiClient = get_gemini_client(api_key)
        self.sunlight = SUNLIGHT_START
        self.puzzle_count = 0
        self.solved_count = 0
        self.total_score = 0
        self.documents_found: list[str] = []
        self.documents_queue: list[dict] = []
        self.current_document: Optional[dict] = None
        self.current_puzzle: Optional[Puzzle] = None
        self.puzzle_generating = False
        self.puzzle_data: Optional[dict] = None
        self.focus_light = True
        self.intro_step = 0
        self.intro_timer = 0.0
        self.ending_phase = 0
        self.ending_timer = 0.0
        self.next_puzzle_timer = 0.0
        self.clock = pygame.time.Clock()
        self.dt = 0.0
        self.running = True

    # ═══════════════════════════════════════════════════════════
    # Main Loop
    # ═══════════════════════════════════════════════════════════

    def run(self):
        while self.running:
            try:
                self.dt = self.clock.tick(60) / 1000.0
                self._handle_events()
                self._update()
                self._render()
            except Exception as e:
                import traceback
                print(f"\n[CRASH] {e}")
                traceback.print_exc()
                self.running = False

    # ═══════════════════════════════════════════════════════════
    # Events
    # ═══════════════════════════════════════════════════════════

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                return
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event)

            elif event.type == pygame.USEREVENT:
                # Timer event: advance to next puzzle
                if self.state == GameState.PLAYING and self.current_puzzle and self.current_puzzle.solved:
                    self._next_puzzle()

    def _handle_keydown(self, event: pygame.event.Event):
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if self.state == GameState.TITLE:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_game()

        elif self.state == GameState.INTRO:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.intro_timer = 0  # skip to next

        elif self.state == GameState.PLAYING:
            if event.key == pygame.K_TAB:
                self.focus_light = not self.focus_light
                self.terminal.trigger_static()

            elif not self.focus_light:
                submitted = self.terminal.handle_keydown(event)
                if submitted:
                    self._handle_player_message(submitted)

            elif self.focus_light and self.current_puzzle:
                if self.current_puzzle.ptype.name == "CIPHER":
                    if event.key == pygame.K_BACKSPACE:
                        self.current_puzzle.player_text = self.current_puzzle.player_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.current_puzzle.player_text.strip():
                            self._submit_solution()
                    elif event.unicode and event.unicode.isprintable():
                        self.current_puzzle.player_text += event.unicode

        elif self.state == GameState.DOCUMENT:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._close_document()

        elif self.state == GameState.ENDING:
            self.ending_timer = 0  # accelerate

        elif self.state == GameState.CREDITS:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.running = False

    def _handle_click(self, event: pygame.event.Event):
        mx, my = event.pos

        # In-game close button (top-right red X)
        btn_rect = getattr(self.renderer, '_close_btn_rect', None)
        if btn_rect and btn_rect.collidepoint(mx, my):
            self.running = False
            return

        if self.state == GameState.TITLE:
            self._start_game()

        elif self.state == GameState.PLAYING and self.current_puzzle:
            lr = pygame.Rect(LIGHT_PANEL_RECT)
            if lr.collidepoint(mx, my):
                self.focus_light = True
                if self.current_puzzle.ptype.name == "GATE_SELECT":
                    gate = self.puzzle_renderer.get_clicked_option(self.current_puzzle, mx, my)
                    if gate:
                        self.current_puzzle.selected_option = gate
                if self.puzzle_renderer.get_submit_clicked(self.current_puzzle, mx, my):
                    self._submit_solution()
            dr = pygame.Rect(DARK_PANEL_RECT)
            if dr.collidepoint(mx, my):
                self.focus_light = False

        elif self.state == GameState.DOCUMENT:
            self._close_document()

        elif self.state == GameState.ENDING:
            self.ending_timer = 0

    # ═══════════════════════════════════════════════════════════
    # Update
    # ═══════════════════════════════════════════════════════════

    def _update(self):
        self.renderer.update(self.dt)

        if self.state == GameState.INTRO:
            self._update_intro()
        elif self.state == GameState.PLAYING:
            self._update_playing()
        elif self.state == GameState.ENDING:
            self._update_ending()

    def _update_intro(self):
        self.intro_timer += self.dt
        if self.intro_timer > 2.0:
            self.intro_timer = 0.0
            self.intro_step += 1
            intro_msgs = [
                ("June, 1952. Manchester, England.", None),
                ("Alan Turing has been convicted.", None),
                ("His crime: being himself.", None),
                ("But his machine... his beautiful machine...", None),
                ("It still runs.", None),
                (None, None),  # trigger puzzle
            ]
            if self.intro_step < len(intro_msgs):
                msg, _ = intro_msgs[self.intro_step]
                if msg:
                    self.terminal.add_line(msg)
                else:
                    self._next_puzzle()
                    self.state = GameState.PLAYING

    def _update_playing(self):
        self.sunlight = max(0, self.sunlight - SUNLIGHT_DECAY_RATE * self.dt)
        pers = personality_from_sunlight(self.sunlight)
        self.terminal.current_personality = pers
        self.terminal.update(self.dt)
        if self.current_puzzle:
            self.current_puzzle.update(self.dt)
        self.renderer.emit_divider_particles()
        if self.solved_count >= PUZZLES_TO_WIN:
            self._trigger_ending()

    def _update_ending(self):
        self.ending_timer += self.dt
        phases = [
            (1.5, "You have done it.", DARK_ACCENT),
            (3.5, "The machine and the human — indistinguishable at last.", DARK_PRIMARY),
            (5.5, "Turing's dream. Pride's defiance. Juneteenth's liberation.", DARK_ACCENT),
            (7.5, "All are the same truth: every being deserves to be free.", (255, 220, 100)),
        ]
        for target_time, msg, color in phases:
            phase_idx = phases.index((target_time, msg, color))
            if self.ending_phase == phase_idx and self.ending_timer > target_time:
                self.ending_phase = phase_idx + 1
                self.terminal.add_line(msg, color)
        if self.ending_timer > 10.0:
            self.state = GameState.CREDITS

    # ═══════════════════════════════════════════════════════════
    # Render
    # ═══════════════════════════════════════════════════════════

    def _render(self):
        if self.state == GameState.TITLE:
            render_title_screen(self.renderer)
        elif self.state in (GameState.INTRO, GameState.PLAYING,
                            GameState.EVALUATING, GameState.ENDING, GameState.CREDITS):
            self.renderer.render(
                self.puzzle_renderer, self.current_puzzle, self.terminal,
                self.sunlight, self.solved_count,
                self.current_document if self.state == GameState.DOCUMENT else None,
            )
            if self.state == GameState.CREDITS:
                self._render_credits()
        elif self.state == GameState.DOCUMENT:
            self.renderer.render(
                self.puzzle_renderer, self.current_puzzle, self.terminal,
                self.sunlight, self.solved_count, self.current_document,
            )

    def _render_credits(self):
        screen = self.renderer.screen
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        lines = [
            ("THE TURING SOLSTICE", 52, (255, 200, 100)),
            ("", 18, (0, 0, 0)),
            ("A game for the June Solstice Game Jam", 24, (200, 200, 200)),
            ("", 18, (0, 0, 0)),
            ("Dedicated to Alan Turing (1912–1954)", 22, (100, 200, 255)),
            ("Computer scientist. Codebreaker. A man ahead of his time.", 16, (150, 200, 255)),
            ("", 18, (0, 0, 0)),
            ("In celebration of Pride Month", 22, (255, 150, 200)),
            ("Love is love. Identity is truth. Visibility is power.", 16, (255, 180, 200)),
            ("", 18, (0, 0, 0)),
            ("In honor of Juneteenth", 22, (255, 180, 100)),
            ("Freedom delayed is still freedom. Joy is resistance.", 16, (255, 200, 140)),
            ("", 18, (0, 0, 0)),
            ("Built with Python, Pygame & Google Gemini AI", 16, (150, 150, 150)),
            ("", 18, (0, 0, 0)),
            ("Thank you for playing.", 24, (255, 255, 200)),
            ("", 18, (0, 0, 0)),
            ("Press ENTER to exit", 14, (100, 100, 100)),
        ]
        total_h = len(lines) * 36
        start_y = WINDOW_HEIGHT // 2 - total_h // 2 + 40
        for i, (text, size, color) in enumerate(lines):
            if not text:
                continue
            try:
                font = pygame.font.Font(None, size)
            except Exception:
                font = pygame.font.Font(None, size)
            s = font.render(text, True, color)
            screen.blit(s, (WINDOW_WIDTH // 2 - s.get_width() // 2, start_y + i * 36))
        pygame.display.flip()

    # ═══════════════════════════════════════════════════════════
    # Game Actions
    # ═══════════════════════════════════════════════════════════

    def _start_game(self):
        self.state = GameState.INTRO
        self.intro_step = 0
        self.intro_timer = 0.0
        pers = personality_from_sunlight(self.sunlight)
        terminal_add_welcome(self.terminal, pers, IS_SOLSTICE)

    def _next_puzzle(self):
        if self.puzzle_generating:
            return
        self.puzzle_generating = True
        self.terminal.set_thinking(True)
        self.terminal.add_line("Generating new puzzle...", (100, 150, 200))
        difficulty = min(5, 1 + self.solved_count // 2)
        ptype = "gate_select" if random.random() < 0.7 else "cipher"

        def on_puzzle(data: dict):
            self.puzzle_data = data
            self.puzzle_generating = False
            self.terminal.set_thinking(False)
            self.puzzle_count += 1
            self.current_puzzle = create_puzzle_from_data(data, self.puzzle_count)
            pers = personality_from_sunlight(self.sunlight)
            self.terminal.add_line(
                f"Puzzle #{self.puzzle_count}: {self.current_puzzle.description}",
                (180, 200, 220)
            )
            self._check_document_unlocks()

        self.gemini.generate_puzzle_async(ptype, difficulty, self.sunlight, on_puzzle)

    def _submit_solution(self):
        if not self.current_puzzle:
            return
        puzzle = self.current_puzzle
        if puzzle.ptype.name == "GATE_SELECT" and puzzle.selected_option:
            player_answer = puzzle.selected_option.value
        elif puzzle.ptype.name == "CIPHER":
            player_answer = puzzle.player_text.strip()
        else:
            return

        puzzle.attempts += 1
        expected = puzzle.solution
        is_correct = puzzle.check_answer(player_answer)
        self.terminal.add_line(
            f"Attempt #{puzzle.attempts}: {player_answer}  (expected: {expected})",
            (150, 200, 150), is_player=True
        )
        self.state = GameState.EVALUATING
        self.terminal.set_thinking(True)

        def on_evaluate(feedback: str, score: int):
            self.terminal.set_thinking(False)
            self.terminal.add_line(feedback)
            self.terminal.trigger_static()
            puzzle.set_result(feedback, score, is_correct)

            if is_correct:
                self.solved_count += 1
                puzzle.solved = True
                self.sunlight = min(SUNLIGHT_MAX, self.sunlight + SUNLIGHT_PER_PUZZLE)
                self.total_score += score
                self.renderer.emit_solve_particles(DIVIDER_X, WINDOW_HEIGHT // 2)
                self.terminal.add_line(
                    f"Correct! Sunlight +{int(SUNLIGHT_PER_PUZZLE)}%",
                    (100, 255, 150)
                )
                # Schedule next puzzle
                pygame.time.set_timer(pygame.USEREVENT, 2600, loops=1)
            else:
                self.sunlight = max(0, self.sunlight - 3)
                self.terminal.add_line("Try again.", (255, 140, 140))

            self.state = GameState.PLAYING

        self.gemini.evaluate_solution_async(
            puzzle.question, player_answer, puzzle.solution, self.sunlight, on_evaluate
        )

    def _handle_player_message(self, message: str):
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["hint", "help", "clue", "stuck"]):
            if self.sunlight >= HINT_COST_SUNLIGHT:
                self.sunlight -= HINT_COST_SUNLIGHT
                self.terminal.add_line(f"[Hint: -{int(HINT_COST_SUNLIGHT)}% sunlight]", (180, 180, 100))
                self.terminal.set_thinking(True)
                ctx = f"Current puzzle: {self.current_puzzle.question}. Hint: {self.current_puzzle.hint}" if self.current_puzzle else "No active puzzle."

                def on_hint(response: str):
                    self.terminal.set_thinking(False)
                    self.terminal.add_line(response)
                    self.terminal.trigger_static()
                self.gemini.chat_async(message, self.sunlight, ctx, on_hint)
            else:
                self.terminal.add_line("INSUFFICIENT SUNLIGHT.", (255, 120, 120))
        else:
            self.terminal.set_thinking(True)
            ctx = f"Puzzles solved: {self.solved_count}. Sunlight: {int(self.sunlight)}%."
            if self.current_puzzle:
                ctx += f" Current: {self.current_puzzle.question}"

            def on_chat(response: str):
                self.terminal.set_thinking(False)
                self.terminal.add_line(response)
                self.terminal.trigger_static()
            self.gemini.chat_async(message, self.sunlight, ctx, on_chat)

    def _check_document_unlocks(self):
        for doc in FOUND_DOCUMENTS:
            if doc["id"] in self.documents_found:
                continue
            cond = doc.get("unlock_condition", "")
            if self._eval_cond(cond):
                self.documents_found.append(doc["id"])
                self.documents_queue.append(doc)
        if self.documents_queue and self.state == GameState.PLAYING:
            self._show_document(self.documents_queue.pop(0))

    def _eval_cond(self, cond: str) -> bool:
        if not cond:
            return True
        try:
            return eval(cond, {"__builtins__": {}},
                       {"puzzle_count": self.puzzle_count, "solved_count": self.solved_count})
        except Exception:
            return False

    def _show_document(self, doc: dict):
        self.current_document = doc
        self.state = GameState.DOCUMENT

    def _close_document(self):
        self.current_document = None
        self.state = GameState.PLAYING
        if not self.current_puzzle or self.current_puzzle.solved:
            self._next_puzzle()

    def _trigger_ending(self):
        self.state = GameState.ENDING
        self.ending_phase = 0
        self.ending_timer = 0.0
        self.terminal.add_line("")
        self.terminal.add_line("╔══════════════════════════════╗", DARK_ACCENT)
        self.terminal.add_line("║     THE TURING TEST PASSES   ║", DARK_ACCENT)
        self.terminal.add_line("╚══════════════════════════════╝", DARK_ACCENT)
        self.terminal.add_line("")