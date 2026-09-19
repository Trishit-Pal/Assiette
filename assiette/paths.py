from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DISTRIBUTIONS_PATH = DATA_DIR / "distributions.json"
KNOWLEDGE_PATH = DATA_DIR / "knowledge.md"
FALLBACK_RESTAURANTS_PATH = DATA_DIR / "fallback_restaurants.json"
