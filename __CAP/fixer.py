"""LLM-driven selector repair loop.

For each target whose selector(s) fail `element_checker`, fetch the live HTML,
ask the LLM for a replacement selector (using the per-target `goal` /
`landmarks` / `stable_attrs` guidance from `targets.json`), validate the
proposal against the page, and patch `__CAP/targets.json` with the verified
replacements. Loop until every target passes or `--max-iter` is reached.

Backend: Gemini if `GEMINI_API_KEY` is set, otherwise `g4f`.

Run: `python -m __CAP.fixer [--name foo] [--apply] [--max-iter 3]`
By default the run is dry — pass `--apply` to actually rewrite targets.json.
"""

import argparse
import importlib
import json
import os
import re
import sys
import time
from typing import List, Optional, Tuple

sys.path.append("../")
sys.path.append("./")

from playwright.sync_api import sync_playwright

from __CAP import targets as targets_module
from __CAP.element_checker import _LAUNCH_ARGS, _USER_AGENT, _probe, check_target
from __CAP.targets import TARGETS, Target, CATALOG_PATH


_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _scrub_html(html: str, max_chars: int = 30000) -> str:
	html = _SCRIPT_RE.sub("", html)
	html = _STYLE_RE.sub("", html)
	html = _COMMENT_RE.sub("", html)
	html = re.sub(r"\s+", " ", html)
	return html[:max_chars]


def _fetch_html(url: str, delay_wait: int = 0) -> Optional[str]:
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
		try:
			page = browser.new_context(user_agent=_USER_AGENT).new_page()
			page.goto(url, wait_until="load", timeout=60000)
			if delay_wait:
				page.wait_for_timeout(delay_wait * 1000)
			return page.content()
		except Exception as e:
			print(f"  fetch_html error: {e}")
			return None
		finally:
			browser.close()


def _validate(url: str, selector: str, delay_wait: int = 0) -> bool:
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
		try:
			page = browser.new_context(user_agent=_USER_AGENT).new_page()
			page.goto(url, wait_until="load", timeout=60000)
			if delay_wait:
				page.wait_for_timeout(delay_wait * 1000)
			return _probe(page, selector)["status"] == "ok"
		except Exception:
			return False
		finally:
			browser.close()


# ---- LLM backends ----

def _build_prompt(target: Target, broken_selector: str, html: str) -> str:
	parts = [
		"You repair broken web scraping selectors.",
		f"URL: {target.url}",
		f"Target name: {target.name}",
		f"Broken selector: {broken_selector}",
	]
	if target.goal:
		parts.append(f"\nWhat the element is (goal):\n  {target.goal}")
	if target.landmarks:
		parts.append("Landmarks to find it:")
		for lm in target.landmarks:
			parts.append(f"  - {lm}")
	if target.stable_attrs:
		parts.append("Stable attributes / hints to prefer:")
		for sa in target.stable_attrs:
			parts.append(f"  - {sa}")
	parts.extend([
		"",
		"Live HTML excerpt (scripts/styles stripped):",
		html,
		"",
		"Output ONLY a single replacement selector (XPath or CSS) targeting the same logical element.",
		"One line, raw selector, no explanation, no markdown fences, no preamble.",
		"Prefer stable attributes (id, data-*, role, aria-label, custom Angular tags) over deep positional /div[N]/ paths.",
	])
	return "\n".join(parts)


def _llm_propose(target: Target, broken_selector: str, html: str) -> Optional[str]:
	prompt = _build_prompt(target, broken_selector, html)
	api_key = os.environ.get("GEMINI_API_KEY")
	if api_key:
		out = _gemini(prompt, api_key)
		if out:
			return out
	return _g4f(prompt)


# gemini-3.1-flash-lite-preview free tier: 15 RPM => 4s minimum spacing.
_GEMINI_MIN_GAP_S = 4.0
_gemini_last_call_ts = 0.0


def _gemini_throttle():
	global _gemini_last_call_ts
	gap = time.monotonic() - _gemini_last_call_ts
	if gap < _GEMINI_MIN_GAP_S:
		time.sleep(_GEMINI_MIN_GAP_S - gap)
	_gemini_last_call_ts = time.monotonic()


def _gemini(prompt: str, api_key: str) -> Optional[str]:
	import requests
	endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent"
	body = {"contents": [{"parts": [{"text": prompt}]}]}
	# 429 (quota burst) / 503 (overload) → back off and retry up to 3 times
	# with progressive 15→30→60s pauses. Other failures fall through.
	for attempt, backoff in enumerate([15, 30, 60], start=1):
		_gemini_throttle()
		try:
			r = requests.post(endpoint, params={"key": api_key}, json=body, timeout=60)
		except Exception as e:
			print(f"  gemini transport error (attempt {attempt}): {e}")
			return None
		if r.status_code not in (429, 503):
			break
		print(f"  gemini http {r.status_code} (attempt {attempt}/3): backing off {backoff}s")
		time.sleep(backoff)
	if not r.ok:
		print(f"  gemini http {r.status_code}: {r.text[:200]}")
		return None
	try:
		text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
	except (KeyError, IndexError, ValueError) as e:
		print(f"  gemini parse error: {e}")
		return None
	return _first_selector_line(text)


def _g4f(prompt: str) -> Optional[str]:
	try:
		import g4f
		resp = g4f.ChatCompletion.create(
			model=g4f.models.gpt_4,
			messages=[{"role": "user", "content": prompt}],
		)
		return _first_selector_line(str(resp)) if resp else None
	except Exception as e:
		print(f"  g4f error: {e}")
		return None


_FENCE_RE = re.compile(r"`+\s*([^`\n]+?)\s*`+")
_SELECTOR_HEAD = re.compile(r"^([/(#.\[]|[a-zA-Z][\w-]*\s*[#.\[>~+])")


def _looks_like_selector(s: str) -> bool:
	if not s or len(s) > 500 or "\n" in s:
		return False
	if s.startswith(("/", "(/", "(//")):
		return True
	return bool(_SELECTOR_HEAD.match(s))


def _first_selector_line(text: str) -> Optional[str]:
	# Prefer the last backtick-fenced fragment that looks like a selector
	# (thinking models like gemma narrate then arrive at a final answer).
	fenced = [m.group(1).strip() for m in _FENCE_RE.finditer(text)]
	for cand in reversed(fenced):
		if _looks_like_selector(cand):
			return cand
	# Fallback: scan lines from the bottom up, stripping bullets/markdown.
	for raw in reversed(text.splitlines()):
		line = re.sub(r"^[\s*\-•>]+", "", raw).strip().strip("`").strip("*").strip()
		if not line:
			continue
		if line.lower().startswith(("here", "the ", "selector", "answer", "xpath", "css", "final", "result")):
			continue
		if _looks_like_selector(line):
			return line
	return None


# ---- targets.json patcher ----

def _patch_targets_json(target_name: str, replacements: List[Tuple[str, str]]) -> int:
	"""Update selectors for a target in targets.json. Returns count applied."""
	with CATALOG_PATH.open(encoding="utf-8") as f:
		data = json.load(f)
	entry = next((t for t in data["targets"] if t["name"] == target_name), None)
	if entry is None:
		print(f"  WARN: target {target_name!r} not found in catalog")
		return 0
	applied = 0
	for old, new in replacements:
		hit = False
		# xpath array
		for i, sel in enumerate(entry.get("xpath", [])):
			if sel == old:
				entry["xpath"][i] = new
				applied += 1
				hit = True
				break
		if hit:
			continue
		# scalar fields
		for key in ("click", "popup", "popup_button", "xpath_iframe"):
			if entry.get(key) == old:
				entry[key] = new
				applied += 1
				hit = True
				break
		if not hit:
			print(f"  WARN: could not locate {old!r} on {target_name}")
	with CATALOG_PATH.open("w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)
		f.write("\n")
	return applied


# ---- main loop ----

def _failing_selectors(report: dict) -> List[str]:
	out = [s["selector"] for s in report["selectors"] if s["status"] != "ok"]
	if report["click"] and report["click"]["status"] != "ok":
		out.append(report["click"]["selector"])
	return out


def review_mode(targets: List[Target]) -> int:
	"""For every target, send the first xpath as if it were broken, print the
	prompt + Gemini response + validation outcome. No mutation. Useful for
	auditing prompt quality and LLM behavior across the whole catalog."""
	api_key = os.environ.get("GEMINI_API_KEY")
	if not api_key:
		print("GEMINI_API_KEY missing — review mode requires Gemini")
		return 1
	for t in targets:
		print(f"\n{'='*70}\n[{t.name}]  {t.url}\n{'='*70}")
		if not t.xpath:
			print("  (no xpath; skipping)")
			continue
		broken = t.xpath[0]
		html = _fetch_html(t.url, t.delay_wait)
		if html is None:
			print("  fetch_html failed; skipping")
			continue
		html = _scrub_html(html)
		prompt = _build_prompt(t, broken, html)
		# Print prompt prefix (skip the long HTML excerpt) for review
		head, _, _ = prompt.partition("Live HTML excerpt")
		print("PROMPT (preamble — HTML excerpt elided):")
		print(head.rstrip())
		print(f"  [HTML excerpt: {len(html)} chars]")
		proposed = _gemini(prompt, api_key)
		print(f"\nGEMINI PROPOSED: {proposed!r}")
		if proposed is None:
			print("  (no proposal)")
			continue
		ok = _validate(t.url, proposed, t.delay_wait)
		match = "MATCHES current" if proposed == broken else "DIFFERENT from current"
		print(f"VALIDATION: {'ok' if ok else 'FAILED'}  ({match})")
	return 0


def main():
	global TARGETS
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--name", help="Run only target containing this substring")
	parser.add_argument("--max-iter", type=int, default=5)
	parser.add_argument("--apply", action="store_true",
	                    help="Patch __CAP/targets.json with verified replacements")
	parser.add_argument("--review", action="store_true",
	                    help="Audit-only: send each target's current selector to Gemini, print prompt + response + validation. No mutation.")
	args = parser.parse_args()

	def _select(targets):
		return [t for t in targets if args.name in t.name] if args.name else list(targets)

	if args.review:
		return review_mode(_select(TARGETS))

	for itr in range(1, args.max_iter + 1):
		print(f"\n=== iteration {itr}/{args.max_iter} ===")
		current = _select(TARGETS)
		broken: List[Tuple[Target, List[str]]] = []
		for t in current:
			r = check_target(t)
			if r["page_status"] != "ok":
				print(f"  SKIP {t.name}: {r['page_status']}")
				continue
			fails = _failing_selectors(r)
			if fails:
				broken.append((t, fails))
				print(f"  BROKEN {t.name}: {len(fails)} selector(s)")
			else:
				print(f"  OK     {t.name}")

		if not broken:
			print("\nall targets passing")
			return 0

		# proposals grouped by target so we patch the right JSON entry.
		all_proposals: List[Tuple[str, List[Tuple[str, str]]]] = []
		total = 0
		for t, fails in broken:
			html = _fetch_html(t.url, t.delay_wait)
			if html is None:
				continue
			html = _scrub_html(html)
			per_target: List[Tuple[str, str]] = []
			for old in fails:
				proposed = _llm_propose(t, old, html)
				if not proposed:
					print(f"  - {t.name}: no LLM proposal for {old}")
					continue
				if _validate(t.url, proposed, t.delay_wait):
					print(f"  + {t.name}\n      old: {old}\n      new: {proposed}")
					per_target.append((old, proposed))
					total += 1
				else:
					print(f"  x {t.name}: proposal failed validation\n      old: {old}\n      tried: {proposed}")
			if per_target:
				all_proposals.append((t.name, per_target))

		if not all_proposals:
			print("no validated proposals this iteration; bailing")
			return 1

		if not args.apply:
			print(f"\n(dry run; {total} validated proposal(s) across {len(all_proposals)} target(s) — pass --apply to write)")
			return 0

		applied = 0
		for name, repls in all_proposals:
			applied += _patch_targets_json(name, repls)
		print(f"  applied {applied}/{total} replacements to {CATALOG_PATH}")
		importlib.reload(targets_module)
		TARGETS = targets_module.TARGETS

	print(f"\nhit max-iter {args.max_iter} without converging")
	return 1


if __name__ == "__main__":
	sys.exit(main())
