import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY is missing from .env")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN is missing from .env")

# Model Routing Configurations
SPECIALIST_MODEL = os.getenv("SPECIALIST_MODEL", "claude-3-5-haiku-latest")
VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", "claude-3-5-sonnet-latest")
