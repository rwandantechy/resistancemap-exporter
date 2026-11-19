# ResistanceMap Exporter

This project collects publicly available antibiotic resistance and use data from
[One Health Trust ResistanceMap](https://resistancemap.onehealthtrust.org/) and
turns it into a single Excel workbook.

The scraper first discovers available countries, downloads their data, and stores
the original responses as JSON. It then combines those responses into overview,
resistance, and antibiotic-use worksheets.

## Requirements

- Python 3.11 or newer
- An internet connection
- Playwright Chromium

## Getting started

From the project folder:

```bash
cd resistancemap-exporter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Using the exporter

### Run everything

Discover countries, scrape available data, and create the Excel workbook:

```bash
python main.py
```

### Discover countries

Refresh the country manifest without downloading country data:

```bash
python main.py --discover-only
```

### Scrape data

Scrape without exporting an Excel workbook:

```bash
python main.py --scrape-only
```

To limit the run to the first few countries:

```bash
python main.py --scrape-only --limit 5
```

To refresh already-cached countries:

```bash
python main.py --scrape-only --force
```

To scrape or retry one country:

```bash
python main.py --scrape-only --country "Côte d'Ivoire" --force
```

Use the country name or slug. For example, `Côte d'Ivoire` and
`cote-d-ivoire` refer to the same country.

### Export without scraping

Create a workbook only from the JSON files already stored locally:

```bash
python main.py --export-only
```

## Generated files

The workbook is saved to:

```text
data/output/ResistanceMap_Country_Data_<YYYY-MM-DD>.xlsx
```

The downloaded JSON responses are saved to:

```text
data/raw/<country-slug>.json
```

The discovered country list is stored in:

```text
data/raw/countries_manifest.json
```

## Data notes

- Missing or null values remain blank. They are not converted to zero.
- Resistance percentages use the 0–100 scale reported by ResistanceMap.
- Antibiotic-use units come from the source request or response when available.
  If the source does not provide a verifiable unit, the workbook leaves the unit
  blank.
- Country availability in the overview is based on ResistanceMap's country
  directory.
- A country can appear in the manifest but still have no downloadable payload.
  In that case, the exporter reports `FAILED - No JSON payload captured`.
