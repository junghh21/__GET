import os, sys, shutil
sys.path.append("../")
sys.path.append("./")
sys.stdout.reconfigure(encoding='utf-8')

import threading
import schedule
import time
from datetime import datetime

from __CAP.cap_web import capture_element_screenshot, summary_element, capture_with_summary, concat_images
from __COMMON.telegram_req import telegram_send_photo, telegram_send_message
from PIL import Image

#########################################################
# def job_0600():
# 	current_time = datetime.now().time()
# 	weekday = datetime.now().weekday()
# 	if weekday == 5 or weekday == 6:
# 		print("job_0600: Weekend")
# 		return

# 	try:
# 		print("job_0600")
# 		#
# 		ny_mkt, ny_chart, ny_top = capture_element_screenshot(
# 		'https://www.nytimes.com/section/markets-overview',
# 		['//*[@id="app"]/div/div[2]', '//*[@id="app"]/div/div[3]', '//*[@id="app"]/div/div[5]'],
# 		popup='//*[@id="complianceOverlay"]',
# 		popup_button='//*[@id="complianceOverlay"]/div/div/button',
# 		xpath_iframe = '//*[@id="site-content"]/iframe')
# 		ny = concat_images(ny_mkt, ny_chart)
# 		ny = concat_images(ny, ny_top)
# 		telegram_send_photo(ny)

# 		#
# 		sentiment_meter = capture_element_screenshot(
# 			'https://www.hulltacticalfunds.com/market-sentiment-meter/',
# 			'//*[@id="__layout"]/div/div[2]/div[6]/div/div/div',
# 			delay_wait=5)
# 		canvas = Image.new('RGB', (sentiment_meter.size[0], sentiment_meter.size[1]), 'black')
# 		canvas.paste(sentiment_meter, (0, 0))
# 		sentiment_meter = sentiment_meter.resize((400, 200))
# 		telegram_send_photo (sentiment_meter)
# 		#
# 		market = capture_element_screenshot(
# 			'https://finance.yahoo.com/',
# 			'//*[@id="nimbus-app"]/aside/section/div[1]/div/div[2]/ul/li[1]/div/div/section/ul')
# 		telegram_send_photo (market)
# 		#
# 		map = capture_element_screenshot(
# 			'https://finviz.com/map.ashx?t=sec',
# 			['//*[@id="canvas-wrapper"]/canvas[1]'])
# 		telegram_send_photo (map)
# 		#
# 		summary, image = capture_with_summary("시장",
# 			'https://tradingeconomics.com/united-states/stock-market',
# 			'//*[@id="description"]',
# 			'//*[@id="UpdatePanelChart"]',
# 			delay_wait=10)
# 		telegram_send_message(summary)
# 		telegram_send_photo (image)
# 		#
# 		greed = capture_element_screenshot(
# 			'https://edition.cnn.com/markets/fear-and-greed',
# 			'/html/body/div[1]/section[4]/section[1]/section[1]/div/section/div[1]/div[2]/div[1]/div/div[1]/div[1]/div')
# 		telegram_send_photo (greed)
# 		#
# 		one_month, intra = capture_element_screenshot(
# 			'https://www.cboe.com/tradable_products/vix/',
# 			'//*[@id="charts-tile"]/div/div/div[2]/div[1]',
# 			delay_wait=10,
# 			click='//*[@id="charts-tile"]/div/div/div[2]/div[2]/div[1]/div[1]')
# 		telegram_send_photo (one_month)
# 		telegram_send_photo (intra)
# 		#
# 		telegram_send_message('https://www.tradingview.com/economic-calendar/?countries=us')
# 		#
# 		summary, image = capture_with_summary("NG",
# 			'https://tradingeconomics.com/commodity/natural-gas',
# 			'//*[@id="description"]',
# 			'//*[@id="UpdatePanelChart"]',
# 			delay_wait=10)
# 		telegram_send_message(summary)
# 		telegram_send_photo (image)
# 		ttf = capture_element_screenshot(
# 			'https://tradingeconomics.com/commodity/eu-natural-gas',
# 			'//*[@id="UpdatePanelChart"]',
# 			delay_wait=10)
# 		telegram_send_photo (ttf)
# 		temp = capture_element_screenshot(
# 			'https://natgasweather.com/',
# 			'//*[@id="post-2813"]/div/div/section[3]/div/div[2]/div/div[2]/div/img')
# 		telegram_send_photo (temp)
# 		power = capture_element_screenshot(
# 			'https://poweroutage.us//',
# 			'//*[@id="ContinentalMap"]/div[2]/canvas',
# 			delay_wait=5)
# 		telegram_send_photo (power)
# 		gen = capture_element_screenshot(
# 			'https://www.eia.gov/electricity/gridmonitor/dashboard/daily_generation_mix/US48/US48/',
# 			'/html/body/div[1]/div[2]/div/app-root/app-dashboard/div/div/div/div[2]/app-grid/div[2]/div/div/gridster/gridster-item[1]/div/app-visualization',
# 			delay_wait=5)
# 		telegram_send_photo (gen)
# 		#
# 		summary, image = capture_with_summary("Gold",
# 			'https://tradingeconomics.com/commodity/gold',
# 			'//*[@id="description"]',
# 			'//*[@id="UpdatePanelChart"]',
# 			delay_wait=10)
# 		telegram_send_message(summary)
# 		telegram_send_photo (image)
# 		#
# 		summary, image = capture_with_summary("Bond",
# 			'https://tradingeconomics.com/united-states/government-bond-yield',
# 			'//*[@id="description"]',
# 			'//*[@id="UpdatePanelChart"]',
# 			delay_wait=10)
# 		telegram_send_message(summary)
# 		telegram_send_photo (image)

# 	except Exception as e:
# 		print(f"job_0600 error: {e}")

#########################################################
def job_30min():
	current_time = datetime.now().time()
	weekday = datetime.now().weekday()
	# if weekday == 5 or weekday == 6:
	# 	print("job_30min: Weekend")
	# 	return

	try:
		print("job_30min")
		#
		telegram_send_message('S&P Futures')
		snp_fut = capture_element_screenshot(
			'https://www.tradingview.com/symbols/CME_MINI-ES1!/',
			'//*[@id="symbol-overview-page-section"]/div/div/div[1]/div[2]/div/div[1]',
			size_mod=(250, 110)
		)
		snp_fut = snp_fut.resize((int(snp_fut.width), int(snp_fut.width*9/16)))
		telegram_send_photo (snp_fut)
		#
		telegram_send_message('VIX')
		one_month, intra = capture_element_screenshot(
			'https://www.cboe.com/tradable_products/vix/',
			'/html/body/main/div/div/section[1]/div/div[3]/div[2]/div[1]/div[1]/div',
			delay_wait=10,
			click='/html/body/main/div/div/section[1]/div/div[3]/div[2]/div[1]/div[2]/div/div/button[1]')
		telegram_send_photo (one_month)
		telegram_send_photo (intra)
		#
		term = capture_element_screenshot(
			'http://vixcentral.com/',
			'//*[@id="container1"]')
		telegram_send_photo (term)
		#
		telegram_send_message('NG Futures')
		ng_fut = capture_element_screenshot(
			'https://www.tradingview.com/symbols/NYMEX-NG1!/',
			'//*[@id="symbol-overview-page-section"]/div/div/div[1]/div[2]/div/div[1]',
			size_mod=(250, 110)
		)
		ng_fut = ng_fut.resize((int(ng_fut.width), int(ng_fut.width*9/16)))
		telegram_send_photo (ng_fut)
	except Exception as e:
		print(f"job_30min error: {e}")

import requests
import json
from selectolax.parser import HTMLParser

def job_coin():
	W = "MdVtFbZSobabqiZL7P4Za4ZUZBWwm3VqSS"
	# Connect to the SSE endpoint
	response = requests.get("https://pool.rplant.xyz/api2/poolminer2/microbitcoin/MdVtFbZSobabqiZL7P4Za4ZUZBWwm3VqSS/TWRWdEZiWlNvYmFicWlaTDdQNFphNFpVWkJXd20zVnFTU3w=", stream=True)
	for line in response.iter_lines():
		if line:
			decoded_line = line.decode("utf-8")
			#print(decoded_line)
			data = json.loads(decoded_line[6:])
			if "miner" in data:
				#print(data["miner"])
				miner = json.loads(json.dumps(data["miner"], ensure_ascii=False))
				#print(miner)
				hr = miner["hr"]
				paid = miner["paid"]
				telegram_send_message (f"{W[-5:]}:  {hr}H/s ({paid:.0f})", "8490037832:AAHmmxVAkA5DqQjJno2O5Oqy2JEHgsDb9Dg", -1003016231971)
				break
	
	# W = "bJzPjHhEwjLPeTJGwePQ4KpDxLH1vvZoy4"
	# html = requests.get(f"https://leywapool.com/site/wallet_miners_results?address={W}").text
	# tree = HTMLParser(html)
	# e_hr = tree.css_first("div > div > table > tbody > tr > td:nth-child(4) > b")
	# try:
	# 	hr = float(e_hr.text().split()[0])
	# except:
	# 	hr = 0
	# html = requests.get(f"https://leywapool.com/site/wallet_results?address={W}").text
	# tree = HTMLParser(html)
	# e_paid = tree.css_first("div > div > table > tbody > tr:nth-child(6) > td:nth-child(4) > a")
	# paid = float(e_paid.text()[:-5])
	# telegram_send_message (f"{W}:  {hr} H/s ({paid:.0f})", "8490037832:AAHmmxVAkA5DqQjJno2O5Oqy2JEHgsDb9Dg", -1003016231971)

	html = requests.get(f"https://www.forbes.com/digital-assets/assets/microbitcoin-mbc/").text
	tree = HTMLParser(html)
	e_name1 = tree.css_first("body > div.main-content.main-content--universal-header.main-content--overflow-visible > main > div.profile-wrapper > div.profile-page-body > div.profile-content > div.profile-body-mobile > div > div.top-assets.fda-right-rail > div:nth-child(2) > div > div > div > div > a > div > span:nth-child(2)")
	name1 = e_name1.text().upper()
	e_price1 = tree.css_first("body > div.main-content.main-content--universal-header.main-content--overflow-visible > main > div.profile-wrapper > div.profile-page-body > div.profile-content > div.profile-body-mobile > div > div.top-assets.fda-right-rail > div:nth-child(2) > div > div > div > div > div > div")
	price1 = e_price1.text()
	e_name2 = tree.css_first("body > div.main-content.main-content--universal-header.main-content--overflow-visible > main > div.profile-wrapper > div.profile-page-body > div.profile-content > div.profile-body-mobile > div > div.top-assets.fda-right-rail > div:nth-child(3) > div > div > div > div > a > div > span:nth-child(2)")
	name2 = e_name2.text().upper()
	e_price2 = tree.css_first("body > div.main-content.main-content--universal-header.main-content--overflow-visible > main > div.profile-wrapper > div.profile-page-body > div.profile-content > div.profile-body-mobile > div > div.top-assets.fda-right-rail > div:nth-child(3) > div > div > div > div > div > div")
	price2 = e_price2.text()
	e_price = tree.css_first("#profile-header > section > div > div > div.header-number-info > span.header-rank")
	price = e_price.text()
	telegram_send_message (f"{name1}: {price1}", "8490037832:AAHmmxVAkA5DqQjJno2O5Oqy2JEHgsDb9Dg", -1003016231971)
	telegram_send_message (f"{name2}: {price2}", "8490037832:AAHmmxVAkA5DqQjJno2O5Oqy2JEHgsDb9Dg", -1003016231971)
	telegram_send_message (f"MBC: {price}", "8490037832:AAHmmxVAkA5DqQjJno2O5Oqy2JEHgsDb9Dg", -1003016231971)

# def job_1800():
# 	current_time = datetime.now().time()
# 	weekday = datetime.now().weekday()
# 	if weekday == 5 or weekday == 6:
# 		print("job_1800: Weekend")
# 		return
# 	try:
# 		print("job_1800")
# 		job_0600()
# 		telegram_send_message('https://www.eia.gov/naturalgas/storage/dashboard/')
# 		telegram_send_message('https://www.eia.gov/naturalgas/weekly/')
# 	except Exception as e:
# 		print(f"job_1800 error: {e}")

#########################################################
if __name__ == "__main__":
	try:
		job_30min()
	except:	
		pass
	try:
		job_coin()
	except:
		pass
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
