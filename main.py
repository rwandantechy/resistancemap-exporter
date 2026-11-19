import argparse
import logging

from src.discover import discover_countries
from src.scraper import scrape_all
from src.parser import parse_all
from src.exporter import export_workbook


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export ResistanceMap country data to Excel")
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--scrape-only", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--country", help="Scrape one country by name or slug")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    setup_logging()

    if args.discover_only:
        entries = discover_countries()
        print(f"Discovered {len(entries)} countries")
        return 0

    if args.scrape_only:
        results = scrape_all(limit=args.limit, force=args.force, country=args.country)
        failed = sum(1 for result in results if result["status"] == "failed")
        print(f"Scraped {len(results)} countries; {failed} failed")
        return 0

    if args.export_only:
        df_overview, df_resistance, df_use, extracted_at = parse_all()
    else:
        discover_countries()
        scrape_all(limit=args.limit, force=args.force, country=args.country)
        df_overview, df_resistance, df_use, extracted_at = parse_all()

    output_path = export_workbook(df_overview, df_resistance, df_use, extracted_at)
    print(f"Exported: {output_path}")
    print(f"Overview: {len(df_overview)} rows")
    print(f"Resistance: {len(df_resistance)} rows")
    print(f"Use: {len(df_use)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
