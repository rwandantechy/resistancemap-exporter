import json
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from config import COUNTRY_DIRECTORY_URL, MANIFEST_PATH, PROJECT_ROOT, REGIONS, RESISTANCE_MAP_BASE_URL


def slugify(value: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w]+", "-", value.lower()).strip("-")
    return value


def discover_countries(headless: bool = True) -> list[dict]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(COUNTRY_DIRECTORY_URL, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1_500)
        discovered = page.evaluate(
            """() => {
                const regions = [];
                let currentRegion = null;
                for (const li of document.querySelectorAll('ul.countrylist > li')) {
                    const regionNode = li.querySelector('.countries_region_head_country');
                    if (regionNode) {
                        currentRegion = regionNode.textContent.trim();
                        continue;
                    }
                    const anchor = li.querySelector('a[href*="CountryPage"]');
                    if (!anchor || !currentRegion) continue;
                    const href = anchor.getAttribute('href');
                    const countryIdMatch = href.match(/[?&]countryId=(\\d+)/);
                    const imageSources = Array.from(li.querySelectorAll('img')).map(img => img.getAttribute('src') || '');
                    regions.push({
                        region: currentRegion,
                        country: anchor.textContent.trim(),
                        countryId: countryIdMatch ? countryIdMatch[1] : null,
                        resistanceAvailable: imageSources.some(src => /bug\\.png/.test(src)) ? 'Yes' : 'No',
                        useAvailable: imageSources.some(src => /drug\\.png/.test(src)) ? 'Yes' : 'No',
                        href: href
                    });
                }
                return regions;
            }"""
        )
        browser.close()

    manifest: list[dict] = []
    for item in discovered:
        name = item["country"]
        href = item["href"].replace("&amp;", "&")
        manifest.append(
            {
                "region": item["region"],
                "country": name,
                "slug": slugify(name),
                "country_id": item["countryId"],
                "resistance_available": item["resistanceAvailable"],
                "use_available": item["useAvailable"],
                "source_url": urljoin(RESISTANCE_MAP_BASE_URL + "/", href),
            }
        )

    if not manifest:
        raise RuntimeError("No countries discovered; ResistanceMap DOM or availability markup may have changed")

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    entries = discover_countries()
    print(f"Discovered {len(entries)} countries")
