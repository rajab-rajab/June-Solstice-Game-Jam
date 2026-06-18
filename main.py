#!/usr/bin/env python3
"""
The Turing Solstice
===================
A narrative puzzle game for the June Solstice Game Jam.
Celebrating Alan Turing, Pride Month, and Juneteenth through
a split-screen logic puzzle adventure powered by Google Gemini AI.

Usage:
    python main.py                    # Fallback puzzles (no API key)
    python main.py --api-key KEY      # Full Gemini AI experience
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")

import argparse
import os
import sys
import math
import struct
import pygame

from env_loader import load_dotenv
from game import Game


def main():
    # Load .env file before anything else (if present)
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)

    # Resolve API key: prefer GOOGLE_API_KEY (new SDK), fall back to GEMINI_API_KEY
    api_key = (
        os.environ.get("GOOGLE_API_KEY", None) or
        os.environ.get("GEMINI_API_KEY", None)
    )

    parser = argparse.ArgumentParser(description="The Turing Solstice")
    parser.add_argument("--api-key", type=str, default=api_key,
                        help="Google Gemini API key (or set GOOGLE_API_KEY in .env)")
    parser.add_argument("--fullscreen", action="store_true",
                        help="Run in fullscreen mode")
    args = parser.parse_args()

    pygame.init()
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        _init_sounds()
    except Exception as e:
        print(f"[Sound] Mixer init failed (sound disabled): {e}")
        SOUND_SOLVE = SOUND_STATIC = SOUND_CLICK = None

    if args.fullscreen:
        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    print("─" * 50)
    print("  THE TURING SOLSTICE")
    if args.api_key:
        print(f"  Gemini AI: ENABLED ({args.api_key[:8]}...)")
    else:
        print("  Gemini AI: DISABLED (use --api-key for dynamic AI puzzles)")
    print("─" * 50)

    game = Game(api_key=args.api_key)
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n[Game] Interrupted. Goodbye.")
    finally:
        pygame.quit()
        sys.exit(0)


def _init_sounds():
    """Generate retro square-wave sound effects (skips if mixer unavailable)."""
    try:
        if not pygame.mixer.get_init():
            return
    except Exception:
        return
    sample_rate = 22050

    def make_sound(freqs, durs, volume=0.3):
        samples = []
        for freq, dur in zip(freqs, durs):
            n = int(sample_rate * dur)
            for i in range(n):
                t = i / sample_rate
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                samples.append(val * volume)
            samples.extend([0.0] * int(sample_rate * 0.02))
        int_samples = [int(max(-32767, min(32767, s * 32767))) for s in samples]
        raw = struct.pack(f"<{len(int_samples)}h", *int_samples)
        return pygame.mixer.Sound(buffer=raw)

    global SOUND_SOLVE, SOUND_STATIC, SOUND_CLICK
    try:
        SOUND_SOLVE = make_sound([440, 554, 659, 880], [0.08, 0.08, 0.08, 0.2], 0.25)
        SOUND_STATIC = make_sound([80, 120, 90, 110], [0.03, 0.03, 0.03, 0.03], 0.15)
        SOUND_CLICK = make_sound([600], [0.05], 0.2)
    except Exception as e:
        print(f"[Sound] Could not generate: {e}")
        SOUND_SOLVE = SOUND_STATIC = SOUND_CLICK = None


if __name__ == "__main__":
    main()