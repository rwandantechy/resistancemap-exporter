# ResistanceMap Country Data Exporter

Production-oriented Python pipeline for extracting country-level antibiotic resistance and use data from One Health Trust ResistanceMap.

## Setup

Python 3.11 or newer is required.

```bash
cd resistancemap-exporter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Commands

Discover countries and write the manifest:

```bash
python main.py --discover-only
```

Run discovery and scrape the first five countries:

```bash
python main.py --limit 5
```

Scrape without exporting:

```bash
python main.py --scrape-only --limit 5
```

Scrape or retry a single country:

```bash
python main.py --scrape-only --country "Côte d'Ivoire" --force
```

Force a cache refresh:

```bash
python main.py --scrape-only --force
```

Export cached payloads without network discovery or scraping:

```bash
python main.py --export-only
```

Run the complete scrape and export:

```bash
python main.py
```

The generated workbook is written to `data/output/ResistanceMap_Country_Data_<YYYY-MM-DD>.xlsx`. Cached JSON payloads are stored in `data/raw/<country-slug>.json`.

## Data notes

- Missing and null metrics remain blank/`NaN`; they are never converted to zero.
- Resistance percentages are interpreted on the source-reported 0-100 scale.
- Use values are reported in DDD per 1,000 inhabitants/day unless the payload indicates otherwise.
- Country availability is based on the ResistanceMap country directory icons.
# ResistanceMap Exporter
