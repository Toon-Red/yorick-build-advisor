"""Configuration for LoL Build Advisor v2."""

from pathlib import Path
import os

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DDRAGON_DIR = DATA_DIR / "ddragon"
LOL_PATH = Path(os.getenv("LOL_PATH", r"C:\Riot Games\League of Legends"))
LOCKFILE_PATH = LOL_PATH / "lockfile"

# Server
API_PORT = 5001
API_HOST = os.getenv("API_HOST", "127.0.0.1")

# Data Dragon
DDRAGON_BASE = "https://ddragon.leagueoflegends.com/cdn"
DDRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"

# Rune style IDs
RUNE_STYLES = {
    8000: "Precision",
    8100: "Domination",
    8200: "Sorcery",
    8300: "Inspiration",
    8400: "Resolve",
}

# Difficulty tier color mapping (from docx cell shading)
DIFFICULTY_COLORS = {
    "6d9eeb": "Easy",
    "6c9eea": "Easy",
    "93c47d": "Medium",
    "6aa84f": "Medium",
    "93c37f": "Medium",
    "ffd966": "Advanced",
    "ffd96b": "Advanced",
    "e69138": "HARD",
    "e6923e": "HARD",
    "e06666": "EXTREME",
    "df6967": "EXTREME",
}

# Ensure data dirs exist
DATA_DIR.mkdir(exist_ok=True)
DDRAGON_DIR.mkdir(exist_ok=True)
