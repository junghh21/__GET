import os, sys, time
sys.path.append("../")
sys.path.append("./")

from playwright.sync_api import sync_playwright

from PIL import Image
import io


def concat_images(image1, image2, hor=None):
	if hor:
		total_width = image1.width + image2.width
		max_height = max(image1.height, image2.height)
		new_image = Image.new('RGB', (total_width, max_height))
		new_image.paste(image1, (0, 0))
		new_image.paste(image2, (image1.width, 0))
	else:
		total_height = image1.height + image2.height
		max_width = max(image1.width, image2.width)
		new_image = Image.new('RGB', (max_width, total_height))
		new_image.paste(image1, (0, 0))
		new_image.paste(image2, (0, image1.height))
	return new_image


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


def _make_context(browser, viewport_width=None):
	kwargs = {"user_agent": _USER_AGENT}
	if viewport_width:
		kwargs["viewport"] = {"width": int(viewport_width), "height": 1080}
	return browser.new_context(**kwargs)


def _hide_overlays(page, target_handle=None):
	"""Heuristically hide popup-like overlays right before a screenshot.

	An element is treated as an overlay (and hidden via display:none) if it
	is fixed/sticky positioned (or a <dialog>), covers >= 15% of the
	viewport, and has z-index >= 100. Elements that are DOM ancestors of
	the target are skipped so the capture target is never accidentally
	hidden.

	Pass an ElementHandle (from `locator.element_handle()`) as
	`target_handle` to enable the ancestor-skip safeguard.
	"""
	page.evaluate(
		"""(target) => {
			const docW = window.innerWidth, docH = window.innerHeight;
			const vpArea = docW * docH;
			let hidden = 0;
			for (const el of document.querySelectorAll('*')) {
				const cs = getComputedStyle(el);
				const overlayLike = cs.position === 'fixed' || cs.position === 'sticky' || el.tagName === 'DIALOG';
				if (!overlayLike) continue;
				const r = el.getBoundingClientRect();
				if (r.width * r.height < vpArea * 0.15) continue;
				const z = parseInt(cs.zIndex);
				if (!(z >= 100 || el.tagName === 'DIALOG')) continue;
				if (target && el.contains(target)) continue;  // DOM ancestor of target — keep
				el.style.setProperty('display', 'none', 'important');
				hidden++;
			}
			return hidden;
		}""",
		target_handle,
	)


def _shoot_xpath(page, xpath, frame_xpath=None, size_mod=None, output_file=None):
	try:
		if frame_xpath:
			target = page.frame_locator(_selector(frame_xpath)).locator(_selector(xpath)).first
		else:
			target = page.locator(_selector(xpath)).first
		target.scroll_into_view_if_needed(timeout=10000)
		page.wait_for_timeout(2000)
		# Hide popup/banner overlays that may cover the target before screenshot.
		# frame_xpath case: target lives inside an iframe; the ancestor-skip safeguard
		# can't traverse iframe boundaries, so we pass None and accept that outer-page
		# overlays are hidden by area/zIndex heuristic alone (iframe itself is rarely
		# fixed/sticky + viewport-spanning so usually fine).
		try:
			tgt = None if frame_xpath else target.element_handle()
			_hide_overlays(page, tgt)
		except Exception as e:
			print(f"  hide_overlays skipped: {e}")
		if size_mod:
			box = target.bounding_box()
			if box is None:
				return None
			clip = {
				"x": box["x"],
				"y": box["y"],
				"width": box["width"] + size_mod[0],
				"height": box["height"] + size_mod[1],
			}
			print(f"clip: {clip}")
			png = page.screenshot(clip=clip)
		else:
			png = target.screenshot()
		image = Image.open(io.BytesIO(png))
		if output_file:
			image.save(output_file)
		return image
	except Exception as e:
		print(f"_shoot_xpath error: {e}")
		return None


def _summary_xpath_text(page, xpath):
	try:
		text = page.locator(_selector(xpath)).first.inner_text(timeout=10000)
		print(text)
		return summary_text(text, "3가지 포인트 한글 헤드라인")
	except Exception as e:
		print(f"_summary_xpath_text error: {e}")
		return ""


def capture_element_screenshot(url, xpath, popup=None, popup_button=None,
                               xpath_iframe=None, output_file=None, width=None,
                               click=None, click_wait=10,
                               delay_wait=None,
                               size_mod=None):
	if isinstance(xpath, str):
		xpath = [xpath]
	output = []

	with sync_playwright() as p:
		browser = p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
		context = _make_context(browser, viewport_width=width)
		page = context.new_page()
		page.goto(url, wait_until="load", timeout=60000)

		if delay_wait:
			page.wait_for_timeout(int(delay_wait) * 1000)

		if popup:
			try:
				page.locator(_selector(popup)).first.wait_for(state="visible", timeout=10000)
				btn = page.locator(_selector(popup_button)).first
				btn.scroll_into_view_if_needed()
				btn.click()
				page.wait_for_timeout(2000)
			except Exception as e:
				print(f"popup dismiss skipped: {e}")

		if click:
			for path in xpath:
				output.append(_shoot_xpath(page, path, size_mod=size_mod))
			try:
				btn = page.locator(_selector(click)).first
				btn.scroll_into_view_if_needed(timeout=10000)
				btn.click()
				page.wait_for_timeout(int(click_wait) * 1000)
			except Exception as e:
				print(f"click error: {e}")

		for path in xpath:
			output.append(_shoot_xpath(page, path, frame_xpath=xpath_iframe, size_mod=size_mod))

		page.wait_for_timeout(1000)
		browser.close()

	if len(output) == 1:
		return output[0]
	return output


# Gemini 2.5 flash-lite free tier nominally 15 RPM, but per-process throttle
# can't see calls from other processes (e.g. fixer.py also throttles itself).
# 8s sustained = 7.5 RPM, half the cap, gives headroom for transient bursts.
_SUMMARY_GAP_S = 8.0
_summary_last_call_ts = 0.0


def _summary_throttle():
	global _summary_last_call_ts
	gap = time.monotonic() - _summary_last_call_ts
	if gap < _SUMMARY_GAP_S:
		time.sleep(_SUMMARY_GAP_S - gap)
	_summary_last_call_ts = time.monotonic()


def _gemini_summary(content, cmd):
	import requests
	api_key = os.environ.get("GEMINI_API_KEY")
	if not api_key:
		return ""
	endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent"
	prompt = (
		(cmd or "한국어 3줄 요약")
		+ ". 각 줄 50자 이내, 번호/불릿 없이 줄바꿈으로만 구분. 원문에 없는 사실 추가 금지.\n\n원문:\n"
		+ content
	)
	body = {"contents": [{"parts": [{"text": prompt}]}]}
	r = None
	for attempt, backoff in enumerate([15, 30, 60], start=1):
		_summary_throttle()
		try:
			r = requests.post(endpoint, params={"key": api_key}, json=body, timeout=60)
		except Exception as e:
			print(f"  gemini summary transport error (attempt {attempt}): {e}")
			return ""
		if r.status_code not in (429, 503):
			break
		print(f"  gemini summary http {r.status_code} (attempt {attempt}/3): backing off {backoff}s")
		time.sleep(backoff)
	if r is None or not r.ok:
		print(f"  gemini summary http {r.status_code if r else 'none'}: {(r.text[:200] if r else '')}")
		return ""
	try:
		return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
	except (KeyError, IndexError, ValueError) as e:
		print(f"  gemini summary parse error: {e}")
		return ""


def summary_text(content, cmd=""):
	"""Summarize the supplied prose. Gemini if GEMINI_API_KEY is set, g4f
	otherwise (legacy fallback). Returns "" on failure rather than raising,
	so callers can post a header-only message."""
	out = _gemini_summary(content, cmd)
	if out:
		return out
	try:
		import g4f
		return g4f.ChatCompletion.create(
			model=g4f.models.gpt_4,
			messages=[{"role": "user", "content": (cmd or "3 가지 포인트 단어 요약") + " : " + content}],
		)
	except Exception as e:
		print(f"  g4f fallback error: {e}")
		return ""


def summary_element(title, url, xpath,
                    click=None, click_wait=10,
                    delay_wait=None):
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
		page = _make_context(browser).new_page()
		page.goto(url, wait_until="load", timeout=60000)

		if delay_wait:
			page.wait_for_timeout(int(delay_wait) * 1000)

		if click:
			try:
				btn = page.locator(_selector(click)).first
				btn.scroll_into_view_if_needed(timeout=10000)
				btn.click()
				page.wait_for_timeout(int(click_wait) * 1000)
			except Exception as e:
				print(f"click error: {e}")

		summary = _summary_xpath_text(page, xpath)
		summary = title + "\n" + summary
		browser.close()
	return summary


def capture_with_summary(title, url, xpath_summary, xpath_capture,
                         click=None, click_wait=10,
                         delay_wait=None):
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
		page = _make_context(browser).new_page()
		page.goto(url, wait_until="load", timeout=60000)

		if delay_wait:
			page.wait_for_timeout(int(delay_wait) * 1000)

		if click:
			try:
				btn = page.locator(_selector(click)).first
				btn.scroll_into_view_if_needed(timeout=10000)
				btn.click()
				page.wait_for_timeout(int(click_wait) * 1000)
			except Exception as e:
				print(f"click error: {e}")

		summary = _summary_xpath_text(page, xpath_summary)
		summary = title + "\n" + summary
		element_image = _shoot_xpath(page, xpath_capture)
		browser.close()
	return summary, element_image
