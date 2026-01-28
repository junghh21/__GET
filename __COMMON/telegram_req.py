
import io
import requests
from PIL import Image

from __COMMON.globals import *

def telegram_send_photo(img):
  if isinstance(img, Image.Image):
    io_buf = io.BytesIO()
    img.save(io_buf, format='PNG')
    io_buf.seek(0)
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    response = requests.post(url, data={'chat_id': chat_id}, files={'photo': io_buf.getvalue()})
    print(response.json())

def telegram_send_message(message, token=None, c_id=None):
  if not token:
    token = bot_token
  if not c_id:
    c_id = chat_id
  url = f"https://api.telegram.org/bot{token}/sendMessage"
  response = requests.post(url, data={'chat_id': c_id, 'text': message})
  print(response.json())