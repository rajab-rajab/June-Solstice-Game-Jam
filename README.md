# The Turing Solstice

**A narrative logic puzzle game for the June Solstice Game Jam**

> *"Every code can be broken. Every wall can fall. Every self can be free."* — The Machine, at Solstice

---

## 🎯 Concept

You are an apprentice to Alan Turing. The Solstice is a cosmic event where the barrier between human intelligence and artificial intelligence is thinnest.

The screen is **split in two**:

| ☀️ LIGHT PANEL (Day) | 🌙 DARK PANEL (Night) |
|---|---|
| Solve logic gate puzzles | Commune with The Machine |
| Visual, click-based | Text terminal, type to speak |
| AND · OR · NOT gates | Gemini AI responds in character |

**The Machine's personality changes** based on your Solstice Energy (Sunlight meter) — from COLD and cryptic to RADIANT and celebratory. On the actual solstice (June 21), the game unlocks special content.

---

## 🏆 Why This Wins

### Best Google AI Usage
Gemini is **mechanically essential** — not a chatbot add-on:
- **Generates puzzles** dynamically with varying difficulty
- **Evaluates your solutions** for correctness AND creativity (score 1-10)
- **5 distinct AI personalities** driven by the Sunlight mechanic
- The game cannot deliver its core experience without AI

### Theme: Solstice, Pride, Juneteenth, Turing
- **Split-screen day/night** — solstice transition as core mechanic
- **Alan Turing** — logic gates, found documents about his life
- **Pride Month** — documents celebrating resilience and authenticity
- **Juneteenth** — themes of liberation, delayed freedom, joy as resistance
- **Real solstice detection** — plays differently on June 21!

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2a. Easiest: Create .env file (copy from .env.example)
cp .env.example .env
# Then edit .env and paste your API key

# 2b. Or set environment variable
# Windows:  set GEMINI_API_KEY=your_key_here
# Mac/Linux: export GEMINI_API_KEY=your_key_here

# 3. Run!
python main.py                     # With .env: auto-loads your key
python main.py --api-key KEY       # Or pass directly via CLI
python main.py                     # Without API key: fallback puzzles
```

---

## 🎮 How to Play

1. **Title Screen** → Click or press ENTER
2. **LIGHT PANEL** (left) → Click logic gates, type cipher answers
3. **DARK PANEL** (right) → Type to The Machine, ask for hints
4. **TAB** → Switch focus between panels  
5. **Type "hint"** → Get a clue (costs Sunlight)
6. **Solve 7 puzzles** → Complete the Turing Test

---

## 🧩 Puzzle Types

- **Gate Select** — Choose AND/OR/NOT for given inputs
- **Cipher Decode** — ROT13, A1Z26, and reversal ciphers
- *With Gemini: infinite unique puzzles generated on the fly*

---

## 🌈 Thematic Depth

Found documents unlock as you progress:

| # | Document | Theme |
|---|---|---|
| 1 | Turing's letter, 1952 | Persecution, authenticity |
| 2 | General Order No. 3 | Juneteenth, liberation |
| 3 | Stonewall fragment | Pride, resilience |
| 4 | Turing's 1950 paper | Identity, the Test |
| 5 | The Solstice Convergence | Unity, freedom |

The Machine's five personalities (COLD → GUARDED → NEUTRAL → WARM → RADIANT) reflect these themes, moving from oppression to celebration as you bring light.

---

## 📁 Project Structure

```
turing_solstice/
├── main.py            # Entry point, CLI, sound generation
├── settings.py        # Constants, colors, solstice detection, narrative data
├── gemini_client.py   # Gemini API wrapper (async, fallback, personality prompts)
├── puzzles.py         # Puzzle engine + visual renderer
├── terminal.py        # Retro terminal UI for the Dark Panel
├── renderer.py        # Master renderer (split screen, particles, HUD)
├── game.py            # Game state machine + orchestration
├── env_loader.py      # Simple .env file loader (zero deps)
├── .env.example       # Template for your API key
├── .gitignore         # Keeps your .env secret
├── requirements.txt   # Dependencies
└── README.md          # This file
```

---

## 🛠️ Technical Highlights

- **Threaded Gemini calls** — UI never freezes
- **5 personality prompts** — each with distinct tone and behavior
- **Real solstice detection** — `datetime.date.today()` vs June 21
- **Particle system** — celebration effects on puzzle solve
- **Procedural audio** — square-wave retro beeps, zero external assets
- **Graceful fallback** — fully playable without API key
- **Retro terminal aesthetic** — scanlines, static, typewriter text, blinking cursor

---

## 🔧 Built With

- Python 3
- Pygame 2
- Google Generative AI (Gemini 1.5 Flash)

---

*Made with love for the June Solstice Game Jam.*
