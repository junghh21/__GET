"""Verify every capture call site's selector still resolves on the live page.

Run: `python -m __CAP.element_checker [--name foo] [--out report.json]`

Each `Target` in `__CAP/targets.py` is loaded in a fresh Chromium page, popups
dismissed, optional click button verified, and every selector probed for
`visible` state + non-zero bounding box. Result is a JSON report consumable by
`__CAP/fixer.py`.
"""

import argparse
import json
import sys
import time
from dataclasses import asdict
from typing import Optional

sys.path.append("../")
sys.path.append("./")

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

from __CAP.targets import TARGETS, Target


_LAUNCH_ARGS = [
	"--no-sandbox",
	"--disable-dev-shm-usage",
	"--disable-gpu",
	"--allow-running-insecure-content",
	"--disable-web-security",
	"--ignore-certificate-errors",
	"--disable-blink-features=AutomationControlled",
]

_USER_AGENT = (
	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
	"(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _selector(sel: str) -> str:
	"""Return a Playwright-prefixed selector. XPath is auto-detected."""
	s = sel.strip()
	if s.startswith("/") or s.startswith("(/") or s.startswith("(//"):
		return f"xpath={s}"
	return s


def _probe(page: Page, sel: str, frame_xpath: Optional[str] = None, timeout_ms: int = 10000) -> dict:
	prefixed = _selector(sel)
	try:
		if frame_xpath:
			loc = page.frame_locator(_selector(frame_xpath)).locator(prefixed).first
		else:
			loc = page.locator(prefixed).first
		loc.wait_for(state="visible", timeout=timeout_ms)
		box = loc.bounding_box()
		if box is None:
			return {"selector": sel, "status": "no_bounding_box"}
		if box["width"] == 0 or box["height"] == 0:
			return {"selector": sel, "status": "zero_size", "box": box}
		return {"selector": sel, "status": "ok", "box": box}
	except PWTimeout as e:
		return {"selector": sel, "status": "timeout", "detail": str(e).splitlines()[0][:200]}
	except Exception as e:
		return {"selector": sel, "status": "error", "detail": f"{type(e).__name__}: {str(e)[:200]}"}


def check_target(target: Target, headless: bool = True) -> dict:
	report: dict = {
		"name": target.name,
		"url": target.url,
		"selectors": [],
		"popup": None,
		"click": None,
		"page_status": "ok",
	}
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=headless, args=_LAUNCH_ARGS)
		try:
			page = browser.new_context(user_agent=_USER_AGENT).new_page()
			t0 = time.time()
			try:
				page.goto(target.url, wait_until="load", timeout=60000)
			except Exception as e:
				report["page_status"] = "goto_failed"
				report["page_detail"] = f"{type(e).__name__}: {str(e)[:200]}"
				return report
			report["goto_ms"] = int((time.time() - t0) * 1000)

			if target.delay_wait:
				page.wait_for_timeout(target.delay_wait * 1000)

			if target.popup:
				report["popup"] = _probe(page, target.popup, timeout_ms=5000)
				if target.popup_button and report["popup"]["status"] == "ok":
					try:
						page.locator(_selector(target.popup_button)).first.click(timeout=5000)
						page.wait_for_timeout(2000)
					except Exception as e:
						report["popup"]["dismiss_error"] = f"{type(e).__name__}: {str(e)[:200]}"

			for sel in target.xpath:
				report["selectors"].append(_probe(page, sel, frame_xpath=target.xpath_iframe))

			if target.click:
				report["click"] = _probe(page, target.click, timeout_ms=5000)
		finally:
			browser.close()
	return report


def _summarize(report: dict) -> str:
	statuses = [r["status"] for r in report["selectors"]]
	if report["click"]:
		statuses.append(report["click"]["status"])
	if report["page_status"] != "ok":
		return f"PAGE_FAIL ({report['page_status']})"
	if all(s == "ok" for s in statuses):
		return "OK"
	bad = [s for s in statuses if s != "ok"]
	return f"FAIL ({len(bad)}/{len(statuses)}: {','.join(set(bad))})"


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--name", help="Run only the target with this name (substring match)")
	parser.add_argument("--out", help="Write JSON report to this path (also prints)")
	parser.add_argument("--headed", action="store_true", help="Run with visible browser (debug)")
	args = parser.parse_args()

	targets = TARGETS
	if args.name:
		targets = [t for t in TARGETS if args.name in t.name]
		if not targets:
			print(f"no target matches {args.name!r}")
			print(f"available: {', '.join(t.name for t in TARGETS)}")
			sys.exit(2)

	report = []
	for t in targets:
		print(f"[checking] {t.name} :: {t.url}")
		r = check_target(t, headless=not args.headed)
		print(f"           -> {_summarize(r)}")
		report.append({"target": asdict(t), "result": r})

	bad = [e for e in report if not _summarize(e["result"]).startswith("OK")]
	print(f"\nsummary: {len(report) - len(bad)}/{len(report)} OK, {len(bad)} failing")
	for e in bad:
		print(f"  - {e['target']['name']}: {_summarize(e['result'])}")

	if args.out:
		with open(args.out, "w", encoding="utf-8") as f:
			json.dump(report, f, ensure_ascii=False, indent=2)
		print(f"\nwrote {args.out}")

	sys.exit(1 if bad else 0)


if __name__ == "__main__":
	main()
