import os, sys, shutil
sys.path.append("../")
sys.path.append("./")

import threading
import schedule
import time
from datetime import datetime

from __CAP.cap_web import capture_element_screenshot, summary_element, capture_with_summary
from __COMMON.telegram_req import telegram_send_photo, telegram_send_message
from PIL import Image

#########################################################
def job_0600():
  current_time = datetime.now().time()
  weekday = datetime.now().weekday()
  if weekday == 5 or weekday == 6:
    print("job_0600: Weekend")
    return
  
  try:    
    print("job_0600")
    #
    snp = capture_element_screenshot(
      'https://finviz.com', 
      ['//*[@id="chart-layout-c-2"]'])
    telegram_send_photo (snp)
    #
    market = capture_element_screenshot(
      'https://finance.yahoo.com/', 
      '//*[@id="nimbus-app"]/aside/section/div[1]/div/div[2]/ul/li[1]/div/div/section/ul')
    telegram_send_photo (market)
    #
    map = capture_element_screenshot(
      'https://finviz.com/map.ashx?t=sec', 
      ['//*[@id="canvas-wrapper"]/canvas[1]'])
    telegram_send_photo (map)
    #
    summary, image = capture_with_summary("시장",
      'https://tradingeconomics.com/united-states/stock-market',
      '//*[@id="description"]',
      '//*[@id="UpdatePanelChart"]',
      delay_wait=10)
    telegram_send_message(summary)
    telegram_send_photo (image)
    #
    greed = capture_element_screenshot(
      'https://edition.cnn.com/markets/fear-and-greed', 
      '/html/body/div[1]/section[4]/section[1]/section[1]/div/section/div[1]/div[2]/div[1]/div/div[1]/div[1]/div')
    telegram_send_photo (greed)
    #
    one_month, intra = capture_element_screenshot(
      'https://www.cboe.com/tradable_products/vix/', 
      '//*[@id="charts-tile"]/div/div/div[2]/div[1]',
      click='//*[@id="charts-tile"]/div/div/div[2]/div[2]/div[1]/div[1]')
    telegram_send_photo (one_month)
    telegram_send_photo (intra)
    #
    telegram_send_message('https://www.tradingview.com/economic-calendar/?countries=us')
    #
    summary, image = capture_with_summary("NG",
      'https://tradingeconomics.com/commodity/natural-gas',
      '//*[@id="description"]',
      '//*[@id="UpdatePanelChart"]',
      delay_wait=10)
    telegram_send_message(summary)
    telegram_send_photo (image)
    ttf = capture_element_screenshot(
      'https://tradingeconomics.com/commodity/eu-natural-gas',
      '//*[@id="UpdatePanelChart"]',
      delay_wait=10)
    telegram_send_photo (ttf)
    #
    summary, image = capture_with_summary("Gold",
      'https://tradingeconomics.com/commodity/gold',
      '//*[@id="description"]',
      '//*[@id="UpdatePanelChart"]',
      delay_wait=10)
    telegram_send_message(summary)
    telegram_send_photo (image)
    #
    summary, image = capture_with_summary("Bond",
      'https://tradingeconomics.com/united-states/government-bond-yield',
      '//*[@id="description"]',
      '//*[@id="UpdatePanelChart"]',
      delay_wait=10)
    telegram_send_message(summary)
    telegram_send_photo (image)
    
  except Exception as e:
    print(f"job_0600 error: {e}")

#########################################################
def job_30min():
  current_time = datetime.now().time()
  weekday = datetime.now().weekday()
  if weekday == 5 or weekday == 6:
    print("job_30min: Weekend")
    return
  
  try:    
    print("job_30min")
    #
    telegram_send_message('S&P Futures')
    snp_fut = capture_element_screenshot(
      'https://www.tradingview.com/symbols/CME_MINI-ES1!/', 
      '//*[@id="js-category-content"]/div[2]/div/section/div[1]/div[2]/div/div[1]')
    telegram_send_photo (snp_fut)
    #
    telegram_send_message('VIX')
    one_month, intra = capture_element_screenshot(
      'https://www.cboe.com/tradable_products/vix/', 
      '//*[@id="charts-tile"]/div/div/div[2]/div[1]',
      click='//*[@id="charts-tile"]/div/div/div[2]/div[2]/div[1]/div[1]')
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
      '//*[@id="js-category-content"]/div[2]/div/section/div[1]/div[2]/div/div[1]')
    telegram_send_photo (ng_fut)
  except Exception as e:
    print(f"job_30min error: {e}")

#########################################################
if __name__ == "__main__":
  job_30min()
  job_0600()
  
  schedule.every().day.at("00:00").do(job_0600)
  schedule.every().day.at("06:00").do(job_0600)
  schedule.every().day.at("18:00").do(job_0600)
  schedule.every(30).minutes.do(job_30min)
  while True:
    try:      
      current_time = datetime.now().time()
      print("Current Time:", current_time)      
      schedule.run_pending()
      time.sleep(60)
    except KeyboardInterrupt:
      break