from dotenv import load_dotenv
import os
import json
from pathlib import Path
import time
import typing as t

try:
    import openai
except Exception:
    openai = None

# New OpenAI client (openai>=1.0) exposes OpenAI class
try:
    from openai import OpenAI as OpenAIClient
except Exception:
    OpenAIClient = None

# Cache directory
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# load .env file if present
load_dotenv()


def _cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol.upper()}.json"


def get_cached_summary(symbol: str) -> t.Optional[dict]:
    p = _cache_path(symbol)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def clear_cache(symbol: t.Optional[str] = None):
    if symbol:
        p = _cache_path(symbol)
        if p.exists():
            p.unlink()
    else:
        for f in CACHE_DIR.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass


def _ensure_openai():
    if openai is None:
        raise RuntimeError("openai package not installed. Add openai to requirements.txt and reinstall.")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set in environment. Export your key and retry.")


def _build_prompt(symbol: str, company_name: t.Optional[str]) -> str:
    display_name = company_name or symbol
    # Template: request JSON only with the requested fields
    return f"""
You are an expert company analyst. Produce a JSON object (no extra text) with the following keys for the company identified by the symbol `{symbol}` and name `{display_name}`:

Overview: short (1-2 sentences) description not copied from stock/ticker fields.
Core Products: an array of top 5 products/services (strings).
Vision: one-sentence future-looking statement.
Accomplishment: one-sentence notable accomplishment.
Why: one or two sentences answering whether someone should own this business and why.

Return valid JSON only, for example:
{{
  "Overview": "...",
  "Core Products": ["p1","p2","p3","p4","p5"],
  "Vision": "...",
  "Accomplishment": "...",
  "Why": "..."
}}
"""


def generate_company_summary(symbol: str, company_name: t.Optional[str] = None, model: str = "gpt-4o-mini", timeout: int = 30) -> dict:
    """Generate a 5-field summary for a company via OpenAI and cache result locally.

    Caches results to `ai/cache/<SYMBOL>.json`.
    Requires `OPENAI_API_KEY` env var and the `openai` package.
    """
    sym = symbol.upper()
    cached = get_cached_summary(sym)
    if cached:
        return cached

    _ensure_openai()

    prompt = _build_prompt(sym, company_name)

    # Use new OpenAI client if available; otherwise fall back to older APIs
    try:
        if OpenAIClient is not None:
            client = OpenAIClient()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a concise analyst."},
                          {"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=400,
                timeout=timeout,
            )
            # try attribute-style access, then dict conversion
            try:
                text = resp.choices[0].message.content.strip()
            except Exception:
                try:
                    d = resp.to_dict()
                    text = d["choices"][0]["message"]["content"].strip()
                except Exception:
                    text = str(resp)
        else:
            # fallback to older openai module functions
            if hasattr(openai, "ChatCompletion"):
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "system", "content": "You are a concise analyst."},
                              {"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=400,
                    timeout=timeout,
                )
                text = resp["choices"][0]["message"]["content"].strip()
            else:
                resp = openai.Completion.create(
                    model=model,
                    prompt=prompt,
                    temperature=0.2,
                    max_tokens=400,
                    timeout=timeout,
                )
                text = resp["choices"][0]["text"].strip()

        # Attempt to parse JSON from the model output. If the model includes extra text,
        # try to extract the first JSON object.
        try:
            doc = json.loads(text)
        except Exception:
            # naive extraction: find first { ... }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                doc = json.loads(text[start:end+1])
            else:
                raise

        # Persist to cache
        p = _cache_path(sym)
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        return doc

    except Exception as e:
        raise RuntimeError(f"AI summary generation failed for {symbol}: {e}")
