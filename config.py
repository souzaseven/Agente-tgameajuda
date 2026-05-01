import os
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).parent
load_dotenv(_root / ".env")           # arquivo principal
load_dotenv(_root / ".env.example")   # fallback se .env não existir

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-7")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "20"))

PROJECT_ROOT = Path(__file__).parent
KB_PATH = PROJECT_ROOT / "knowledge_base.json"

SISTEMA_TICKETS = "Movidesk"
SISTEMA_ERP = "Sistema interno Delphi/Pascal"
