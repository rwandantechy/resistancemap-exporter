from pathlib import Path

COUNTRY_DIRECTORY_URL = "https://resistancemap.onehealthtrust.org/Countries.php"
RESISTANCE_MAP_BASE_URL = "https://resistancemap.onehealthtrust.org"
ONE_HEALTH_TRUST_URL = "https://onehealthtrust.org"

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
MANIFEST_PATH = RAW_DIR / "countries_manifest.json"

REQUEST_TIMEOUT_SECONDS = 60
RATE_LIMIT_SECONDS = 2.0
RETRY_ATTEMPTS = 3
USER_AGENT = "ResistanceMap-Exporter/1.0 (One Health Trust public data export)"

REGIONS = [
    "East Asia & Pacific",
    "Europe & Central Asia",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
]
