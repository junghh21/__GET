import os, sys, shutil
sys.path.append("../")
sys.path.append("./")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from PIL import Image
import io
import time

from __COMMON.telegram_req import telegram_send_photo

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

def capture_element_screen_by_xpath (driver, xpath, xpath_iframe=None, output_file=None, size_mod=None):
	iframe_loc = None
	try:    
		if xpath_iframe:
			iframe = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, xpath_iframe))
			)
			iframe_loc = iframe.location
			driver.switch_to.frame(iframe)
		element = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.XPATH, xpath))
		)
		driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
		time.sleep(5)
		# Capture screenshot of the element's area
		location = element.location
		size = element.size
		if size_mod != None:
			size['width'] += size_mod[0]
			size['height'] += size_mod[1]
		print(iframe_loc, location, size)
		png = driver.get_screenshot_as_png()
		if xpath_iframe:
			driver.switch_to.default_content()

		# Convert the screenshot to an image
		image = Image.open(io.BytesIO(png))

		left = location['x']
		top = location['y']
		right = location['x']
		bottom = location['y']
		if iframe_loc:
			left += iframe_loc['x']
			top += iframe_loc['y']
			right += iframe_loc['x']
			bottom += iframe_loc['y']
		top -= driver.execute_script('return window.pageYOffset')
		right += size['width']
		bottom = bottom - driver.execute_script('return window.pageYOffset') + size['height']

		# Crop the image to the bounding box
		print(f"Crop: {left=}, {top=}, {right=}, {bottom=}")
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
		print(element.text)
		summary = summary_text (element.text, "3가지 포인트 한글 헤드라인")
	except Exception as e:
		print(f"An error occurred: {e}")
		summary = ''
	return summary

def capture_element_screenshot(url, xpath, popup=None, popup_button=None, 
															xpath_iframe=None, output_file=None, width=None,
															click=None, click_wait=10,
															delay_wait=None,
															size_mod=None):
		options = Options()
		options.add_argument("--allow-running-insecure-content")
		options.add_argument("--disable-web-security")
		options.add_argument("--ignore-certificate-errors")
		#'''
		driver = webdriver.Chrome(options=options)
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
		
		if popup:
			try:
				element = WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.XPATH, popup))
				)
				actions = ActionChains(driver)
				element = driver.find_element(By.XPATH, popup_button)
				driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
				actions.click(element).perform()
				time.sleep(2)
			except:
				pass

		
		if click:
			for path in xpath:        
				element_image = capture_element_screen_by_xpath (driver, path, size_mod=size_mod)
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
			element_image = capture_element_screen_by_xpath (driver, path, xpath_iframe=xpath_iframe, size_mod=size_mod)
			output.append(element_image)
			
		time.sleep(1)
		driver.quit()
		
		if len(output) == 1:
			output = output[0]
		return output

# from g4f.client import Client
import g4f
def summary_text(content, cmd=""):
	import g4f
	response = g4f.ChatCompletion.create(
		model=g4f.models.gpt_4,
		messages=[{"role": "user", "content": "3 가지 포인트 단어 요약 : "+content}]
	)
	return response
	# client = Client()
	# response = client.chat.completions.create(
	# 		model="gpt-4o-mini",
	# 		messages=[{"role": "user", "content": content + cmd}],
	# 		web_search=False
	# )
	# return response.choices[0].message.content

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
	