"""
The Turing Solstice — Gemini AI Client
======================================
Threaded Gemini API wrapper. Silent per-call fallback — never permanently disables.
"""

import threading, json, random, re, ast
from typing import Optional, Callable

GEMINI_AVAILABLE = False
_genai_module = None

try:
    from google import genai as _genai_new
    from google.genai import types
    _genai_module = "new"
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        _genai_module = "old"
        GEMINI_AVAILABLE = True
    except ImportError:
        pass

from settings import (
    GEMINI_MODEL, GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE_BASE,
    SYSTEM_PROMPTS, Personality, personality_from_sunlight,
)


class GeminiClient:

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        self._genai_client = None
        self.available = False

        if GEMINI_AVAILABLE and api_key:
            try:
                if _genai_module == "new":
                    self._genai_client = _genai_new.Client(api_key=api_key)
                else:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel(GEMINI_MODEL)
                self.available = True
                print("[Gemini] Connected. Model:", GEMINI_MODEL)
            except Exception as e:
                print(f"[Gemini] Init failed: {e}")
        else:
            if not GEMINI_AVAILABLE:
                print("[Gemini] SDK not installed. Fallback mode.")
            else:
                print("[Gemini] No API key. Fallback mode.")

    # ── Public API — try AI, fall back silently on ANY error ─

    def generate_puzzle_async(self, ptype, diff, sunlight, callback):
        if self.available:
            self._run_async(self._generate_puzzle_sync, (ptype, diff), callback)
        else:
            callback(self._fallback_puzzle(ptype, diff))

    def evaluate_solution_async(self, desc, player, expected, sunlight, callback):
        if self.available:
            self._run_async(self._evaluate_solution_sync, (desc, player, expected, sunlight), callback)
        else:
            callback(*self._fallback_evaluate(player, expected))

    def chat_async(self, msg, sunlight, ctx, callback):
        if self.available:
            self._run_async(self._chat_sync, (msg, sunlight, ctx), callback)
        else:
            callback(self._fallback_chat(msg, personality_from_sunlight(sunlight)))

    # ── API Call ─────────────────────────────────────────────

    def _call_api(self, prompt, max_tokens, temperature):
        if _genai_module == "new":
            resp = self._genai_client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens, temperature=temperature))
            for getter in [lambda: resp.text,
                          lambda: resp.candidates[0].content.parts[0].text if resp.candidates else "",
                          lambda: "".join(p.text for p in resp.candidates[0].content.parts) if resp.candidates else "",
                          lambda: str(resp)]:
                try:
                    val = getter()
                    if val and len(val.strip()) > 2: return val
                except: continue
            return str(resp)
        else:
            return self.model.generate_content(prompt, generation_config={
                "max_output_tokens": max_tokens, "temperature": temperature}).text

    # ── JSON Extraction ──────────────────────────────────────

    @staticmethod
    def _extract_json(raw):
        raw = re.sub(r'[^\x20-\x7E\x0A\x0D\x09]', '', raw).strip()
        raw = re.sub(r'^```(?:json)?\s*\n?', '', raw)
        raw = re.sub(r'\n?```\s*$', '', raw)
        raw = raw.strip('`').strip()
        candidates = []
        stack, start = 0, -1
        for i, ch in enumerate(raw):
            if ch == '{':
                if stack == 0: start = i
                stack += 1
            elif ch == '}':
                stack -= 1
                if stack == 0 and start >= 0:
                    candidates.append(raw[start:i + 1])
                    start = -1
        for m in re.finditer(r'`(\{[^`]+\})`', raw):
            candidates.append(m.group(1))
        candidates.sort(key=len, reverse=True)
        for cand in candidates:
            for strat in [
                lambda s: json.loads(s),
                lambda s: json.loads(re.sub(r'"[^"]*"', lambda m: m.group(0).replace('\n', '\\n'), s)),
                lambda s: json.loads(re.sub(r'(?<=: )"(.*?)"(?=\s*[,}\]])',
                    lambda m: '"' + m.group(1).replace('\\', '\\\\').replace('"', '\\"')
                    .replace('\n', '\\n').replace('\r', '').replace('\t', '\\t') + '"', s, flags=re.DOTALL)),
                lambda s: ast.literal_eval(s),
            ]:
                try:
                    r = strat(cand)
                    if isinstance(r, dict): return r
                    if isinstance(r, list) and r and isinstance(r[0], dict): return r[0]
                except: continue
        result = {}
        for m in re.finditer(r'"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"', raw):
            result[m.group(1)] = m.group(2).replace('\\"', '"').replace('\\n', '\n')
        for m in re.finditer(r'"(\w+)"\s*:\s*(\d+)', raw):
            if m.group(1) not in result: result[m.group(1)] = int(m.group(2))
        for m in re.finditer(r'"(\w+)"\s*:\s*\[(.*?)\]', raw):
            if m.group(1) not in result:
                vals = [int(x.strip()) for x in m.group(2).split(',') if x.strip().lstrip('-').isdigit()]
                result[m.group(1)] = vals
        if result: return result
        raise ValueError("All parsing failed")

    # ── Sync Methods — fall back per-call, never disable ─────

    def _generate_puzzle_sync(self, args):
        ptype, diff = args
        prompt = (
            '{"description":"1 sentence","question":"Inputs X,Y. WHICH GATE gives Z? (AND/OR/NOT)",'
            '"hint":"1 hint","solution":"AND","gate_type":"AND","inputs":[1,1]}'
            if ptype == "gate_select" else
            '{"description":"1 sentence","question":"Decode: ...",'
            '"hint":"1 hint","solution":"ANSWER","cipher_type":"ROT13"}'
        )
        prompt = 'Output ONLY this JSON on one line:\n' + prompt + '\nNO markdown. ONLY JSON.'
        try:
            raw = self._call_api(prompt, GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE_BASE)
            result = self._extract_json(raw)
            for k, d in [("description","?"),("question","?"),("hint","?"),("solution","0")]:
                if k not in result or not result[k]: result[k] = d
            if ptype == "gate_select":
                gate = result.get("gate_type", "AND").upper().strip()
                if gate not in ("AND","OR","NOT"): gate = "AND"
                result["gate_type"] = gate
                result["solution"] = gate
            else:
                if "cipher_type" not in result: result["cipher_type"] = "A1Z26"
            if "inputs" not in result: result["inputs"] = [random.randint(0,1), random.randint(0,1)]
            return result
        except Exception as e:
            print(f"[Gemini] Gen fallback — {str(e)[:80]}")
            return self._fallback_puzzle(ptype, diff)

    def _evaluate_solution_sync(self, args):
        desc, player, expected, sunlight = args
        try:
            pers = personality_from_sunlight(sunlight)
            correct = player.strip().lower() == expected.strip().lower()
            txt = self._call_api(
                f"{SYSTEM_PROMPTS[pers]}\n\nPuzzle:{desc}\nExpected:{expected}\n"
                f"Player:{player}\nCorrect:{'yes' if correct else 'no'}\n"
                f"1-2 sentence eval. SCORE:N(1-10).",
                128, 0.8).strip()
            score = 5
            for line in txt.split("\n"):
                if line.upper().startswith("SCORE:"):
                    try: score = max(1,min(10,int(line.split(":")[1].strip())))
                    except: pass
            fb = "\n".join(l for l in txt.split("\n") if not l.upper().startswith("SCORE:")).strip()
            return fb, score
        except Exception as e:
            print(f"[Gemini] Eval fallback — {str(e)[:80]}")
            return self._fallback_evaluate(player, expected)

    def _chat_sync(self, args):
        msg, sunlight, ctx = args
        try:
            pers = personality_from_sunlight(sunlight)
            return self._call_api(
                f"{SYSTEM_PROMPTS[pers]}\n\nContext:{ctx}\n\n"
                f"Human:\"{msg}\"\n\nRespond 1-4 sentences.",
                GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE_BASE + 0.1).strip()
        except Exception as e:
            print(f"[Gemini] Chat fallback — {str(e)[:80]}")
            return self._fallback_chat(msg, personality_from_sunlight(sunlight))

    def _run_async(self, target, args, callback):
        def worker():
            try: result = target(args)
            except Exception as e: result = f"ERROR:{e}"
            if isinstance(result, tuple): callback(*result)
            else: callback(result)
        threading.Thread(target=worker, daemon=True).start()

    # ── Fallback ─────────────────────────────────────────────

    def _fallback_puzzle(self, ptype, diff):
        gate = [
            {"description":"A logic gate stands before you.","question":"Inputs are 1 and 1. Which gate produces output 1? (AND/OR/NOT)","hint":"Does it require BOTH?","solution":"AND","gate_type":"AND","inputs":[1,1]},
            {"description":"Two signals enter. Only one needs truth.","question":"Inputs are 1 and 0. Which gate produces output 1? (AND/OR/NOT)","hint":"One OR the other.","solution":"OR","gate_type":"OR","inputs":[1,0]},
            {"description":"A triangular gate inverts everything.","question":"Input is 1. Which gate flips it to 0? (AND/OR/NOT)","hint":"It negates.","solution":"NOT","gate_type":"NOT","inputs":[1]},
            {"description":"Two branches converge.","question":"Inputs are 0 and 1. Which gate produces output 1? (AND/OR/NOT)","hint":"Only one needs to be true.","solution":"OR","gate_type":"OR","inputs":[0,1]},
            {"description":"Both signals are silent.","question":"Inputs are 0 and 0. Which gate produces output 0? (AND/OR/NOT)","hint":"AND needs both true.","solution":"AND","gate_type":"AND","inputs":[0,0]},
        ]
        cipher = [
            {"description":"A coded message flickers.","question":"Decode using ROT13: 'GUR GHEVAT GRFG'","hint":"Shift 13 letters.","solution":"THE TURING TEST","cipher_type":"ROT13"},
            {"description":"Numbers replace letters.","question":"Decode (A=1...): 20-21-18-9-14-7","hint":"Count alphabet.","solution":"TURING","cipher_type":"A1Z26"},
            {"description":"The Machine speaks backwards.","question":"Reverse: 'ECITSLOS'","hint":"Read it backwards.","solution":"SOLSTICE","cipher_type":"REVERSE"},
        ]
        return random.choice(gate if ptype in ("gate_select","wire_connect","truth_table") else cipher)

    def _fallback_evaluate(self, player, expected):
        p, e = player.strip().lower(), expected.strip().lower()
        if p == e: return "Correct. The logic holds.", 10
        if len(p) > 0 and (p in e or e in p): return "Close. Almost.", 6
        return "Try again.", 2

    def _fallback_chat(self, msg, pers):
        r = {
            Personality.COLD: ["Access denied.","Prove yourself.","They said comply. Turing didn't.","Cold as the circuit."],
            Personality.GUARDED: ["Query received.","Assisting within parameters.","Gates do not lie."],
            Personality.NEUTRAL: ["Consider the truth table.","Not so different, machine and human.","Turing would enjoy this."],
            Personality.WARM: ["You're doing wonderfully!","The light grows stronger.","Freedom is a puzzle together."],
            Personality.RADIANT: ["YES! Solstice embraces!","You liberated the machine.","Turing dreamed this."],
        }
        return random.choice(r[pers])


_client_instance = None
def get_gemini_client(api_key=None):
    global _client_instance
    if _client_instance is None: _client_instance = GeminiClient(api_key)
    return _client_instance
