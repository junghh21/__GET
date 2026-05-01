import os, sys, shutil
sys.path.append("../")
sys.path.append("./")
#sys.stdout.reconfigure(encoding='utf-8')

import threading
import schedule
import time
from datetime import datetime

from __CAP.cap_web import capture_element_screenshot, summary_element, capture_with_summary, concat_images
from __CAP.targets import BY_NAME as T
from __COMMON.telegram_req import telegram_send_photo, telegram_send_message
from PIL import Image

#########################################################
def job_0600():
	current_time = datetime.now().time()
	weekday = datetime.now().weekday()
	# if weekday == 5 or weekday == 6:
	# 	print("job_0600: Weekend")
	# 	return

	print("job_0600")
		# #
		# ny_mkt, ny_chart, ny_top = capture_element_screenshot(
		# 'https://www.nytimes.com/section/markets-overview',
		# ['//*[@id="app"]/div/div[2]', '//*[@id="app"]/div/div[3]', '//*[@id="app"]/div/div[5]'],
		# popup='//*[@id="complianceOverlay"]',
		# popup_button='//*[@id="complianceOverlay"]/div/div/button',
		# xpath_iframe = '//*[@id="site-content"]/iframe')
		# ny = concat_images(ny_mkt, ny_chart)
		# ny = concat_images(ny, ny_top)
		# telegram_send_photo(ny)

	try:
		t = T["hull-sentiment-meter"]
		sentiment_meter = capture_element_screenshot(t.url, t.xpath, delay_wait=t.delay_wait)
		canvas = Image.new('RGB', (sentiment_meter.size[0], sentiment_meter.size[1]), 'black')
		canvas.paste(sentiment_meter, (0, 0))
		sentiment_meter = sentiment_meter.resize((400, 200))
		telegram_send_photo(sentiment_meter)
	except:
		telegram_send_message('hulltacticalfunds capture failed')
	try:
		t = T["yahoo-finance-markets-id"]
		market = capture_element_screenshot(t.url, t.xpath)
		telegram_send_photo(market)
	except:
		telegram_send_message('finance.yahoo capture failed')
	try:
		t = T["finviz-sec-map"]
		map = capture_element_screenshot(t.url, t.xpath)
		telegram_send_photo(map)
	except:
		telegram_send_message('finviz capture failed')
	try:
		t = T["te-us-stock-market"]
		summary, image = capture_with_summary("시장", t.url, t.xpath[0], t.xpath[1], delay_wait=t.delay_wait)
		telegram_send_message(summary)
		telegram_send_photo(image)
	except:
		telegram_send_message('te market capture failed')
	try:
		t = T["cnn-fear-greed"]
		greed = capture_element_screenshot(t.url, t.xpath)
		telegram_send_photo(greed)
	except:
		telegram_send_message('fear-and-greed capture failed')
	try:
		telegram_send_message('VIX')
		t = T["cboe-vix"]
		one_month, intra = capture_element_screenshot(t.url, t.xpath, delay_wait=t.delay_wait, click=t.click)
		telegram_send_photo(one_month)
		telegram_send_photo(intra)
	except:
		telegram_send_message('VIX capture failed')

	telegram_send_message('https://www.tradingview.com/economic-calendar/?countries=us')
	try:
		t = T["te-natural-gas"]
		summary, image = capture_with_summary("NG", t.url, t.xpath[0], t.xpath[1], delay_wait=t.delay_wait)
		telegram_send_message(summary)
		telegram_send_photo(image)
	except:
		telegram_send_message('te ng capture failed')
	try:
		t = T["te-eu-natural-gas"]
		ttf = capture_element_screenshot(t.url, t.xpath, delay_wait=t.delay_wait)
		telegram_send_photo(ttf)
	except:
		telegram_send_message('te ttf capture failed')
	try:
		t = T["natgasweather-temp"]
		temp = capture_element_screenshot(t.url, t.xpath)
		telegram_send_photo(temp)
	except:
		telegram_send_message('natgasweather capture failed')
	try:
		t = T["eia-grid-generation"]
		gen = capture_element_screenshot(t.url, t.xpath, delay_wait=t.delay_wait)
		telegram_send_photo(gen)
	except:
		telegram_send_message('eia electricity capture failed')
	try:
		t = T["te-gold"]
		summary, image = capture_with_summary("Gold", t.url, t.xpath[0], t.xpath[1], delay_wait=t.delay_wait)
		telegram_send_message(summary)
		telegram_send_photo(image)
	except:
		telegram_send_message('te gold capture failed')
	try:
		t = T["te-us-bond-yield"]
		summary, image = capture_with_summary("Bond", t.url, t.xpath[0], t.xpath[1], delay_wait=t.delay_wait)
		telegram_send_message(summary)
		telegram_send_photo(image)
	except:
		telegram_send_message('te bond capture failed')

def job_1800():
	current_time = datetime.now().time()
	weekday = datetime.now().weekday()
	# if weekday == 5 or weekday == 6:
	# 	print("job_1800: Weekend")
	# 	return
	try:
		print("job_1800")
		job_0600()
		telegram_send_message('https://www.eia.gov/naturalgas/storage/dashboard/')
		telegram_send_message('https://www.eia.gov/naturalgas/weekly/')
	except Exception as e:
		print(f"job_1800 error: {e}")

#########################################################
if __name__ == "__main__":
	job_1800()
	exit()
	job_1800()

	schedule.every().day.at("00:00").do(job_0600)
	schedule.every().day.at("06:00").do(job_0600)
	schedule.every().day.at("18:00").do(job_1800)
	schedule.every(30).minutes.do(job_30min)
	while True:
		try:
			current_time = datetime.now().time()
			print("Current Time:", current_time)
			schedule.run_pending()
			time.sleep(60)
		except KeyboardInterrupt:
			break
