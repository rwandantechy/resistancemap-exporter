import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from config import MANIFEST_PATH, RAW_DIR, RETRY_ATTEMPTS, RATE_LIMIT_SECONDS, REQUEST_TIMEOUT_SECONDS


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def scrape_country(browser, entry: dict, force: bool = False) -> dict:
    output_path = RAW_DIR / f"{entry['slug']}.json"
    if output_path.exists() and not force:
        cached = json.loads(output_path.read_text(encoding="utf-8"))
        return {"country": entry["country"], "status": "cached", "path": str(output_path), "payload_count": len(cached.get("responses", []))}

    responses: list[dict] = []
    page = browser.new_page()

    def capture(response):
        url = response.url
        if not (url.endswith("/getData.php") or url.endswith("/getSubData.php")):
            return
        if response.status != 200:
            return
        try:
            payload = response.json()
        except Exception:
            return
        if payload:
            responses.append({
                "url": url,
                "method": response.request.method,
                "post_data": response.request.post_data,
                "payload": payload,
            })

    page.on("response", capture)
    try:
        page.goto(entry["source_url"], wait_until="networkidle", timeout=REQUEST_TIMEOUT_SECONDS * 1000)
        page.wait_for_timeout(2_000)

        for label in ("Resistance Map", "Resistance Trend", "Resistance Chart", "Use Map", "Use Trend", "Use Chart"):
            locator = page.get_by_text(label, exact=True)
            if locator.count():
                try:
                    locator.first.click(timeout=5_000)
                    page.wait_for_timeout(1_500)
                except Exception:
                    pass
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(f"Timeout loading {entry['country']}: {exc}") from exc
    finally:
        page.close()

    unique = []
    seen = set()
    for response in responses:
        key = (response["url"], response["post_data"])
        if key not in seen:
            seen.add(key)
            unique.append(response)

    if not unique:
        raise RuntimeError(f"No JSON payload captured for {entry['country']}")

    output_path.write_text(
        json.dumps(
            {
                "country": entry["country"],
                "region": entry["region"],
                "source_url": entry["source_url"],
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "responses": unique,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"country": entry["country"], "status": "scraped", "path": str(output_path), "payload_count": len(unique)}


def scrape_all(limit: int | None = None, force: bool = False, country: str | None = None) -> list[dict]:
    manifest = load_manifest()
    if country:
        normalized = country.strip().lower()
        manifest = [
            entry
            for entry in manifest
            if entry["country"].lower() == normalized or entry["slug"].lower() == normalized
        ]
        if not manifest:
            raise RuntimeError(f"Country not found in manifest: {country}")
    if limit:
        manifest = manifest[:limit]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for index, entry in enumerate(manifest, start=1):
            try:
                result = scrape_country(browser, entry, force=force)
                print(f"[{index}/{len(manifest)}] {entry['country']}: {result['status']}")
            except Exception as exc:
                print(f"[{index}/{len(manifest)}] {entry['country']}: FAILED - {exc}")
                result = {"country": entry["country"], "status": "failed", "error": str(exc)}
            results.append(result)
            if index < len(manifest):
                time.sleep(max(0.0, RATE_LIMIT_SECONDS + random.uniform(-0.25, 0.25)))
        browser.close()
    return results
