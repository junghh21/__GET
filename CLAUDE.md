# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A scheduled web scraper that captures screenshots of financial market sites with headless Chrome (Selenium) and pushes the images / text summaries to Telegram. Execution is driven by GitHub Actions cron schedules, running inside a pre-built Docker image. There is no server, no database, no tests — each run is a one-shot script invocation that exits.

## Two entrypoints, two cadences

- `main.py` — `job_30min` (S&P futures, Yahoo markets snapshot, VIX one-month + intraday, vixcentral term structure, NG futures) plus `job_coin` (rplant.xyz mining pool SSE + CoinGecko top-2 + CoinMarketCap MBC). Run by `.github/workflows/main (2).yml` every 30 minutes. The `__main__` block calls `job_30min()` and `job_coin()` then `exit()`s — the `schedule.every(...)` block below the `exit()` is dead code, do not assume it runs.
- `main1.py` — `job_0600` / `job_1800` (Hull sentiment meter, finviz S&P map, TradingEconomics market/NG/Gold/Bond, CNN fear & greed, VIX, EU NG (TTF), natgasweather, EIA grid). Run by `.github/workflows/main1.yml` every 6 hours via cron. Same `exit()`-before-scheduler pattern.

Each capture is wrapped in its own `try/except` that posts a "*** capture failed*" Telegram message on error, so one broken XPath does not abort the run. When fixing a broken capture, look for the corresponding failure message — XPaths drift constantly as target sites are redesigned.

## Execution model — Docker image is the runtime

The Dockerfile installs Playwright + Chromium + Korean locale + Python deps but **does not `COPY` the source**. Workflows pull `ghcr.io/junghh21/venv_get:latest` and bind-mount the checked-out repo into `/app`:

```
docker run --rm -v "$(pwd)":/app -w /app ghcr.io/<owner>/venv_get:latest python main.py
```

Consequences:
- Editing `main.py` / `__CAP/` / `__COMMON/` does **not** require rebuilding the image. Push to `main` and the next cron tick picks it up.
- Editing `Dockerfile` or `requirements.txt` **does** require a rebuild. `docker-publish.yml` rebuilds and pushes `ghcr.io/<owner>/venv_get:latest` on every push to `main`. Wait for that workflow before triggering the runtime workflows.
- Browser is Playwright-managed Chromium installed via `playwright install --with-deps chromium`; launch flags (`--no-sandbox --disable-dev-shm-usage --disable-gpu`) are passed in `__CAP/cap_web.py` via `_LAUNCH_ARGS`.

Local run (matches CI): `docker run --rm -v "$(pwd)":/app -w /app ghcr.io/junghh21/venv_get:latest python main.py`. Plain host `python main.py` works if `playwright install chromium` has been run locally.

## Capture library — `__CAP/cap_web.py`

`capture_element_screenshot(url, xpath, ...)` is the workhorse. It:
1. spins up a fresh `sync_playwright` browser per call (one Chromium per capture, no reuse),
2. optionally dismisses a popup, optionally clicks a tab/button after a first capture (used to grab "1-month" then "intraday" VIX views from the same page),
3. uses `locator.screenshot()` for plain element captures, falling back to `page.screenshot(clip=bounding_box + size_mod)` when `size_mod` is set to extend the box.

`xpath` accepts a `str` or `list[str]`; with a list (or with `click=` set, which captures pre- and post-click), the function returns a list of PIL images, otherwise a single image. Callers unpack accordingly — keep this contract in mind when adding XPaths.

`capture_with_summary` and `summary_element` use `g4f` (free GPT proxy) to summarize the text of one element while capturing another. `g4f` is unstable upstream; a failure here cascades into the wrapping `try/except` in `main*.py`.

## Telegram + secrets

`__COMMON/globals.py` holds `bot_token` and `chat_id` **as plaintext, committed to the repo**. The coin job in `main.py` additionally hard-codes a second bot token and chat id inline. Treat these as already-public; don't introduce a "fix" that breaks the workflows by moving them to env vars without also wiring secrets into the workflow files.

`telegram_send_photo(img)` expects a PIL `Image.Image`. `telegram_send_message(text, token=None, c_id=None)` defaults to the globals; the coin job passes overrides to route to a different chat.

## Selector maintenance — checker + fixer

The dominant maintenance task in this repo is patching XPaths after target sites redesign. Two helpers automate this:

- **`__CAP/targets.py`** — single source of truth for every capture call site (URL, selectors, popup, click, delay). `main.py` and `main1.py` look up entries via `from __CAP.targets import BY_NAME as T` and reference `T["name"].url` / `T["name"].xpath` / etc. Per-target post-processing (image resizes, telegram message ordering, summary titles) stays inline in the main files; only the URL+selectors live in the catalog. The fixer mutates this file and the next cron tick picks up the new selectors automatically.
- **`__CAP/element_checker.py`** — `python -m __CAP.element_checker [--name foo] [--out report.json]`. Loads each target in headless Chromium, dismisses popups, probes every selector for visible + non-zero box, prints a pass/fail summary, exits non-zero if any target fails. Selector dialect is auto-detected (XPath if it starts with `/`, CSS otherwise).
- **`__CAP/fixer.py`** — `python -m __CAP.fixer [--name foo] [--apply] [--max-iter 3]`. For each failing selector: scrubs `<script>`/`<style>` from the live HTML, asks the LLM for a replacement, validates the proposal against the page (must hit `status=ok` in `_probe`), then rewrites `targets.py` via literal string replacement. Dry-run by default; `--apply` is required to mutate the file. LLM backend prefers Gemini (`GEMINI_API_KEY` env var) and falls back to `g4f`.

Both reuse `_LAUNCH_ARGS` / `_probe` / `_selector` from `element_checker.py` to stay consistent with how `cap_web.py` actually launches Chromium.

## Other workflows

- `LONG.yml`, `Senpai.yml`, `main_w.yml` — Windows runners that set up Chrome Remote Desktop / tmate / Tailscale on GitHub-hosted machines for interactive access. Unrelated to the scraping pipeline; leave them alone unless the user explicitly asks.
- `docker-image.yml` — older variant of the publish job, superseded by `docker-publish.yml`.

## Notebooks

Top-level `.ipynb` files (`test.ipynb`, `aaa.ipynb`, `finviz.ipynb`, `investiny.ipynb`, `investpy.ipynb`, `Untitled-1.ipynb`, `API_Scope.ipynb`) and the ones under `__CAP/` are scratch/experiment notebooks for trying new XPaths or APIs. They are not part of the production path — do not refactor them as if they were.
