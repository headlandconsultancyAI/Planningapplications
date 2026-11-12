# North East Lincolnshire Idox document inventory

Target: **DM/0631/26/FUL**, Idox key **TJPJA1LJI5600**. The user-provided screenshot showed **1,109** document entries on 12 November 2026; the live count can change.

## Run entirely in GitHub

1. Create a **private** GitHub repository and upload the files in this project, preserving `.github/workflows/discover.yml`.
2. Open **Actions → Discover Idox documents → Run workflow**.
3. Once the job finishes, open the run's **Artifacts** section and download `planning-inventory-and-diagnostics`.
4. Review `manifest.csv` / `manifest.json`. The reported count must be reconciled with the live portal before proceeding.

## What is and is not implemented

- **Implemented:** browser-based read-only discovery, heuristic document table parsing, a conservative Next-link pagination attempt, CSV/JSON manifests, diagnostics on failure, GitHub Actions execution, and basic tests.
- **Not implemented:** bulk ZIP downloads, extraction, retries, SHA-256 file hashing, or resumability. Those require inspecting the live portal's controls and verifying copying permissions. Do **not** treat this as a finished 1,109-file downloader.
- **Not yet verified against the live site:** selectors, pagination, whether a browser session is required, and whether the council site accepts GitHub-hosted runners. The document table may have different column offsets; inspect sample manifest entries before trusting them.

## Local development (optional)

```bash
pip install -r requirements.txt
python -m playwright install chromium
python download.py
pytest -q
```

## Access and rights

This workflow only inventories public-facing document metadata; it does not copy PDF contents. Before implementing or running document downloads, confirm the applicable permissions from the council/copyright owners. Respect access controls and do not bypass restrictions. Avoid putting downloaded planning files in Git history or public artifacts.
