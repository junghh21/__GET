import os, sys
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


def _shoot_xpath(page, xpath, frame_xpath=None, size_mod=None, output_file=None):
	try:
		if frame_xpath:
			target = page.frame_locator(_selector(frame_xpath)).locator(_selector(xpath)).first
		else:
			target = page.locator(_selector(xpath)).first
		target.scroll_into_view_if_needed(timeout=10000)
		page.wait_for_timeout(2000)
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


import g4f
def summary_text(content, cmd=""):
	response = g4f.ChatCompletion.create(
		model=g4f.models.gpt_4,
		messages=[{"role": "user", "content": "3 가지 포인트 단어 요약 : " + content}]
	)
	return response


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
