import os, sys, shutil
sys.path.append("../")
sys.path.append("./")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import io
import time

from __COMMON.telegram_req import telegram_send_photo

def capture_element_screen_by_xpath (driver, xpath, output_file=None):
  try:    
    element = WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.XPATH, xpath))
		)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    # Capture screenshot of the element's area
    location = element.location
    size = element.size
    png = driver.get_screenshot_as_png()

    # Convert the screenshot to an image
    image = Image.open(io.BytesIO(png))

    # Define the bounding box for the element
    left = location['x']
    top = location['y'] - driver.execute_script('return window.pageYOffset')
    right = location['x'] + size['width']
    bottom = location['y'] - driver.execute_script('return window.pageYOffset') + size['height']

    # Crop the image to the bounding box
    element_image = image.crop((left, top, right, bottom))
    if output_file:
      element_image.save(output_file)
  except:
  	element_image = None
    
  return element_image

def summary_element_text_by_xpath (driver, xpath):
  try:    
    element = WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.XPATH, xpath))
		)
    summary = summary_text (element.text, "3가지 포인트 한글 헤드라인")
  except Exception as e:
    print(f"An error occurred: {e}")
    summary = ''
  return summary

def capture_element_screenshot(url, xpath, output_file=None, width=None,
                               click=None, click_wait=10,
                               delay_wait=None):
    #'''
    driver = webdriver.Chrome()
    '''
    driver = webdriver.Edge()
    '''
    driver.get(url)
    
    if width:      
      window_size = driver.get_window_size()
      print(f"Window size: width={window_size['width']}, height={window_size['height']}")
      driver.set_window_size(width, window_size['height'])
    
    if delay_wait:
      time.sleep(delay_wait)
    if type(xpath) == str:    
      xpath = [xpath]
    output = []
    
    if click:
      for path in xpath:        
        element_image = capture_element_screen_by_xpath (driver, path)
        output.append(element_image)
      
      element = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, click))
			)
      actions = ActionChains(driver)
      element = driver.find_element(By.XPATH, click)
      driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
      actions.click(element).perform()
      time.sleep(click_wait)
        
    for path in xpath:
      element_image = capture_element_screen_by_xpath (driver, path)
      output.append(element_image)
      
    time.sleep(1)
    driver.quit()
    
    if len(output) == 1:
      output = output[0]
    return output

from g4f.client import Client
def summary_text(content, cmd=""):
	client = Client(provider="")
	response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[{"role": "user", "content": content + cmd}],
			web_search=False
	)
	return response.choices[0].message.content

def summary_element(title, url, xpath,
                    click=None, click_wait=10,
                    delay_wait=None):
    #'''
    driver = webdriver.Chrome()
    '''
    driver = webdriver.Edge()
    '''
    driver.get(url)
    
    if delay_wait:
      time.sleep(delay_wait)
      
    if click:
      element = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, click))
			)      
      actions = ActionChains(driver)
      element = driver.find_element(By.XPATH, click)
      driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
      actions.click(element).perform()
      time.sleep(click_wait)
      
    summary = summary_element_text_by_xpath (driver, xpath)
    summary = title+'\n'+summary
    
    driver.quit()
    return summary
  
def capture_with_summary(title, url, xpath_summary, xpath_capture,
                         click=None, click_wait=10,
                         delay_wait=None):
    #'''
    driver = webdriver.Chrome()
    '''
    driver = webdriver.Edge()
    '''
    driver.get(url)
    
    if delay_wait:
      time.sleep(delay_wait)
      
    if click:
      element = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, click))
			)      
      actions = ActionChains(driver)
      element = driver.find_element(By.XPATH, click)
      driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
      actions.click(element).perform()
      time.sleep(click_wait)
      
    summary = summary_element_text_by_xpath (driver, xpath_summary)
    summary = title+'\n'+summary
    element_image = capture_element_screen_by_xpath (driver, xpath_capture)        
      
    driver.quit()
    return summary, element_image
  