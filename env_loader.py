"""
The Turing Solstice — .env Loader
==================================
Simple .env file loader — no external dependencies.
Loads KEY=VALUE pairs from a .env file into os.environ.
"""

import os
from pathlib import Path


def load_dotenv(path: str = ".env") -> bool:
    """Load environment variables from a .env file.
    Returns True if file was found and loaded."""
    env_path = Path(path)
    if not env_path.exists():
        return False

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE (handle optional quotes)
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes if present
            if value and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            # Only set if not already set in environment
            if key and value and key not in os.environ:
                os.environ[key] = value

    print(f"[Env] Loaded {env_path.resolve()}")
    return True
