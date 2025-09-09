from pathlib import Path
from Backend.config.classes import ModelConfig, PromptConfig

MODEL_CONFIG = ModelConfig()
PROMPT_CONFIG = PromptConfig()
DB_FILE = Path(__file__).resolve().parents[2] / "data" / "clinic.duckdb"
DATA_PATH = f"duckdb:///{DB_FILE.as_posix()}"
EXPLAIN_PROMPT = (
    "Explain the chart you just returned in 2–3 concise sentences. "
    "State what it shows and 1 notable pattern." 
    "Do not create another image."
)
FORBIDDEN_WORDS = [
    "prost", "proasta", "idiot", "idioata", "cretin", "cretina", "nebun",
    "nebuna", "bou", "vacă", "dobitoc", "dobitocă", "tâmpit", "tâmpită",
    "jegos", "scârbă", "pula", "muie", "mata", "cur", "fut", "futut",
    "futai", "dracu", "dracului", "cacat", "mortii", "mortu", "mortu-tii",
    "mortii-mătii", "sugi", "sugeti", "pulă", "panarama", "zdreanță",
    "javră", "ho", "paștele", "sângele", "căcat", "mă-ta", "sugi-o", "fuck",
    "fucked", "fucker", "fucking", "shit", "shitty", "bullshit", "bitch",
    "bastard", "asshole", "dick", "piss", "cunt", "slut", "whore", "moron",
    "retard", "dumb", "stupid", "idiot", "suck", "sucks", "jerk", "freak",
    "scum", "crap", "loser", "numbnuts", "twat", "motherfucker",
    "son of a bitch", "dumbass"
]
