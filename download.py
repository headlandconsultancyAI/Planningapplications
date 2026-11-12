"""Read-only Idox document inventory; optional controlled native archive batches.

The portal's selectors and bulk-download workflow have NOT been verified.
"""
import argparse
import asyncio
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

URL = 'https://planninganddevelopment.nelincs.gov.uk/online-applications/applicationDetails.do?activeTab=documents&keyVal=TJPJA1LJI5600'
FIELDS = ['page', 'date_published', 'document_type', 'description', 'view_url']


def safe_name(value):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', value).strip('._')[:100] or 'file'


def same_host(url):
    return urlparse(url).hostname == 'planninganddevelopment.nelincs.gov.uk'


async def extract_rows(page, page_number):
    # Find the document table by its headings, not a brittle generated ID.
    return await page.evaluate('''(pageNumber) => {
      const tables = [...document.querySelectorAll('table')];
      const table = tables.find(t => {
        const h = (t.querySelector('thead')?.innerText || t.querySelector('tr')?.innerText || '').toLowerCase();
        return h.includes('date published') && h.includes('document type') && h.includes('description');
      });
      if (!table) return null;
      const trs = [...table.querySelectorAll('tr')].filter(tr => tr.querySelector('td'));
      return trs.map(tr => {
        const td = [...tr.querySelectorAll('td')];
        const a = td[td.length-1]?.querySelector('a[href]');
        return {page: pageNumber, date_published: td[1]?.innerText.trim() || '',
          document_type: td[2]?.innerText.trim() || '',
          description: td[3]?.innerText.trim() || '',
          view_url: a ? new URL(a.getAttribute('href'), location.href).href : ''};
      });
    }''', page_number)


async def inventory(page, out, max_pages):
    await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
    await page.wait_for_timeout(1200)
    seen = set()
    rows = []
    for page_number in range(1, max_pages + 1):
        current = await extract_rows(page, page_number)
        if current is None:
            raise RuntimeError('Document table not found. Inspect screenshot and HTML artifact; update selectors.')
        for row in current:
            key = (row['date_published'], row['document_type'], row['description'], row['view_url'])
            if key not in seen:
                rows.append(row)
                seen.add(key)
        print(f'Page {page_number}: {len(current)} rows, {len(rows)} unique total', flush=True)
        # Common Idox pagination controls: avoid clicking anything unless clearly Next.
        next_link = page.get_by_role('link', name=re.compile(r'^next(?: page)?\s*(?:>|»)?$', re.I)).first
        if await next_link.count() == 0 or not await next_link.is_visible():
            break
        previous_url = page.url
        previous_first = current[0]['description'] if current else ''
        await next_link.click(timeout=15000)
        await page.wait_for_load_state('domcontentloaded', timeout=30000)
        await page.wait_for_timeout(1000)
        following = await extract_rows(page, page_number + 1)
        if page.url == previous_url and (not following or following[0]['description'] == previous_first):
            raise RuntimeError('Pagination did not advance; refusing to silently claim completeness.')
    else:
        print('WARNING: max-pages reached; inventory may be incomplete', flush=True)
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'manifest.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (out / 'manifest.json').write_text(json.dumps({
        'application': 'DM/0631/26/FUL', 'keyVal': 'TJPJA1LJI5600',
        'observed_count': len(rows), 'expected_count_from_screenshot': 1109,
        'complete_against_screenshot': len(rows) == 1109,
        'generated_utc': datetime.now(timezone.utc).isoformat(), 'documents': rows
    }, indent=2), encoding='utf-8')
    return rows


async def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', default='output')
    p.add_argument('--max-pages', type=int, default=200)
    p.add_argument('--headed', action='store_true')
    args = p.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not args.headed)
        context = await browser.new_context(accept_downloads=False)
        page = await context.new_page()
        try:
            rows = await inventory(page, out, args.max_pages)
            print(f'Inventory complete: {len(rows)} rows; expected 1109 (screenshot, may change).')
            if len(rows) != 1109:
                print('WARNING: count differs; review manifest and portal pagination before any downloads.')
        except Exception:
            await page.screenshot(path=str(out / 'diagnostic.png'), full_page=True)
            (out / 'diagnostic.html').write_text(await page.content(), encoding='utf-8')
            raise
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
