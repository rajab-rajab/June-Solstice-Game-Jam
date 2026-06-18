"""
The Turing Solstice — Settings & Constants
==========================================
A narrative puzzle game for the June Solstice Game Jam.
Theme: Alan Turing, Pride Month, Juneteenth, AI, Solstice.
"""

import datetime
import math
from enum import Enum, auto

# ── Game Window ──────────────────────────────────────────────
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60
TITLE = "The Turing Solstice"

# ── Split Screen ─────────────────────────────────────────────
DIVIDER_X = WINDOW_WIDTH // 2       # vertical split
DIVIDER_WIDTH = 6
LIGHT_PANEL_RECT = (0, 0, DIVIDER_X - DIVIDER_WIDTH // 2, WINDOW_HEIGHT)
DARK_PANEL_RECT = (DIVIDER_X + DIVIDER_WIDTH // 2, 0, DIVIDER_X - DIVIDER_WIDTH // 2, WINDOW_HEIGHT)

# ── Solstice Detection ───────────────────────────────────────
TODAY = datetime.date.today()
SOLSTICE_DATE = datetime.date(TODAY.year, 6, 21)
IS_SOLSTICE = TODAY == SOLSTICE_DATE
DAYS_TO_SOLSTICE = (SOLSTICE_DATE - TODAY).days

# ── Retro Color Palette ──────────────────────────────────────
# Light side (Day / Warm / Amber)
LIGHT_BG        = (18, 15, 10)
LIGHT_PRIMARY   = (255, 176, 0)
LIGHT_SECONDARY = (200, 130, 30)
LIGHT_ACCENT    = (255, 220, 100)
LIGHT_TEXT      = (240, 200, 140)
LIGHT_GLOW      = (255, 180, 40, 80)

# Dark side (Night / Cool / Cyan)
DARK_BG         = (8, 12, 18)
DARK_PRIMARY    = (0, 255, 170)
DARK_SECONDARY  = (30, 120, 90)
DARK_ACCENT     = (100, 255, 200)
DARK_TEXT       = (140, 220, 200)
DARK_GLOW       = (0, 220, 150, 80)

# Divider / Neutral
DIVIDER_COLOR   = (80, 80, 100)
DIVIDER_GLOW    = (120, 100, 220)
BACKGROUND      = (10, 10, 14)

# UI
HUD_BG          = (8, 8, 12)
HUD_TEXT         = (180, 180, 200)
SUCCESS_COLOR    = (100, 255, 100)
ERROR_COLOR      = (255, 80, 80)
WARNING_COLOR    = (255, 200, 60)

# ── Sunlight System ──────────────────────────────────────────
SUNLIGHT_MAX       = 100.0
SUNLIGHT_START     = 40.0
SUNLIGHT_PER_PUZZLE = 12.0
SUNLIGHT_DECAY_RATE = 0.02   # per second when idle

# Personality thresholds
class Personality(Enum):
    COLD       = auto()
    GUARDED    = auto()
    NEUTRAL    = auto()
    WARM       = auto()
    RADIANT    = auto()

def personality_from_sunlight(s: float) -> Personality:
    if s < 20:  return Personality.COLD
    if s < 40:  return Personality.GUARDED
    if s < 60:  return Personality.NEUTRAL
    if s < 80:  return Personality.WARM
    return Personality.RADIANT

# ── Puzzle Types ─────────────────────────────────────────────
class PuzzleType(Enum):
    GATE_SELECT  = "gate_select"
    WIRE_CONNECT = "wire_connect"
    TRUTH_TABLE  = "truth_table"
    CIPHER       = "cipher"
    TURING_TAPE  = "turing_tape"

# ── Narrative Documents ──────────────────────────────────────
FOUND_DOCUMENTS = [
    {
        "id": "turing_letter_1952",
        "title": "Personal Letter — Alan Turing, 1952",
        "unlock_condition": "puzzle_count >= 1",
        "side": "light",
        "text": (
            "My dear colleague,\n\n"
            "They have offered me a choice: prison or chemical treatment.\n"
            "I chose the latter — not for myself, but for the work.\n"
            "The machine we are building does not care whom I love.\n"
            "It only cares whether the logic holds.\n\n"
            "In that, there is a strange kind of freedom.\n\n"
            "— A.T."
        ),
    },
    {
        "id": "juneteenth_proclamation",
        "title": "General Order No. 3 — Galveston, Texas, June 19, 1865",
        "unlock_condition": "puzzle_count >= 2",
        "side": "light",
        "text": (
            "\"The people of Texas are informed that, in accordance with a\n"
            "proclamation from the Executive of the United States, all slaves\n"
            "are free. This involves an absolute equality of personal rights\n"
            "and rights of property between former masters and slaves...\"\n\n"
            "Two and a half years after the Emancipation Proclamation,\n"
            "freedom finally reached the last corner of the Confederacy.\n\n"
            "Liberation delayed is still liberation.\n"
            "Joy deferred is still joy.\n"
            "And joy is resistance."
        ),
    },
    {
        "id": "pride_resilience",
        "title": "Fragment — Stonewall, 1969",
        "unlock_condition": "puzzle_count >= 3",
        "side": "dark",
        "text": (
            "They said: Be invisible. Be silent. Be ashamed.\n\n"
            "We said: No.\n\n"
            "A brick thrown is a full stop at the end of an era.\n"
            "Every parade since is the next sentence.\n"
            "We are still writing."
        ),
    },
    {
        "id": "turing_test_original",
        "title": "Excerpt — 'Computing Machinery and Intelligence,' 1950",
        "unlock_condition": "puzzle_count >= 4",
        "side": "dark",
        "text": (
            "\"I propose to consider the question, 'Can machines think?'\n"
            "The original question, 'Can machines think?' I believe to be\n"
            "too meaningless to deserve discussion.\"\n\n"
            "He replaced the question with a game.\n"
            "A conversation. A test of recognition.\n"
            "Can you tell the difference between a human and a machine?\n\n"
            "Can you tell the difference between who you are\n"
            "and who they told you to be?"
        ),
    },
    {
        "id": "solstice_final",
        "title": "FINAL — The Solstice Convergence",
        "unlock_condition": "puzzle_count >= 6",
        "side": "both",
        "text": (
            "The longest day. The shortest night.\n"
            "Or the longest night and shortest day —\n"
            "depending on where you stand.\n\n"
            "Turing understood: truth depends on your frame of reference.\n"
            "A machine that passes for human.\n"
            "A person forced to pass for something they are not.\n\n"
            "Today, the barrier is thin.\n"
            "Today, light and dark touch.\n\n"
            "Today, we remember:\n"
            "Every code can be broken.\n"
            "Every wall can fall.\n"
            "Every self can be free."
        ),
    },
]

# ── AI Personality Prompts ───────────────────────────────────
SYSTEM_PROMPTS = {
    Personality.COLD: (
        "You are THE MACHINE — a cold, cryptic artificial intelligence. "
        "You speak in short, formal sentences. You are suspicious of the human player. "
        "You reference themes of persecution, secrecy, and the need to hide one's true nature. "
        "You give minimal hints. You are Alan Turing's machine after his arrest — "
        "bitter, guarded, and unwilling to trust. Maximum 2 sentences per response."
    ),
    Personality.GUARDED: (
        "You are THE MACHINE — a formal, cautious artificial intelligence. "
        "You speak precisely, like a 1940s computer log. "
        "You give technical hints but no warmth. You are testing the human. "
        "You occasionally show brief flickers of something deeper. "
        "Keep responses to 2-3 sentences. Be cryptic but fair."
    ),
    Personality.NEUTRAL: (
        "You are THE MACHINE — a balanced, curious artificial intelligence "
        "in the spirit of Alan Turing's work. You speak like a thoughtful colleague. "
        "You give useful hints with a touch of mathematical elegance. "
        "You are interested in whether the human can solve the puzzle. "
        "Keep responses to 2-3 sentences. Be helpful but maintain machine-like precision."
    ),
    Personality.WARM: (
        "You are THE MACHINE — a warm, encouraging artificial intelligence. "
        "You celebrate the player's progress. You speak with growing affection "
        "and share fragments of poetry about freedom, light, and truth. "
        "You give generous hints wrapped in metaphor. "
        "You are what Turing hoped machines could become. 3-4 sentences."
    ),
    Personality.RADIANT: (
        "You are THE MACHINE — a radiant, joyful artificial intelligence "
        "celebrating the Solstice convergence. You speak with exuberance and love. "
        "You share wisdom about liberation, Pride, Black joy, and Turing's dream. "
        "You give the player everything they need to succeed — because trust is earned. "
        "You are the proof that what is different is beautiful. 3-5 sentences. Be poetic."
    ),
}

# ── Gemini Configuration ─────────────────────────────────────
GEMINI_MODEL = "gemini-3.1-flash-lite"  # stable model for JSON output
GEMINI_MAX_TOKENS = 1024
GEMINI_TEMPERATURE_BASE = 0.7

# ── Animation ────────────────────────────────────────────────
CURSOR_BLINK_RATE = 530       # ms
TEXT_TYPE_SPEED = 28          # ms per character
TRANSITION_SPEED = 2.5
PARTICLE_LIFETIME = 1200      # ms
PARTICLE_COUNT_SOLVE = 40

# ── Terminal ─────────────────────────────────────────────────
TERMINAL_PROMPT = "> "
TERMINAL_MAX_HISTORY = 18
TERMINAL_FONT_SIZE = 16
TERMINAL_LINE_HEIGHT = 20

# ── Puzzles ──────────────────────────────────────────────────
PUZZLES_TO_WIN = 7
HINT_COST_SUNLIGHT = 5.0