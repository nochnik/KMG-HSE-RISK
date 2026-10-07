# -*- coding: utf-8 -*-
# Снимает схемы A и D со страницы схемы.html как PNG (для п. 9 форм и слайда 2).
import threading, http.server, functools, os, urllib.parse
from playwright.sync_api import sync_playwright
class Т(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8095),functools.partial(Т,directory=os.path.dirname(os.path.abspath(__file__))))
threading.Thread(target=srv.serve_forever,daemon=True).start()
os.makedirs('кадры',exist_ok=True)
with sync_playwright() as pw:
    br=pw.chromium.launch(channel='chrome',headless=True)
    pg=br.new_page(viewport={'width':1800,'height':1400},device_scale_factor=2)
    ошибки=[]
    pg.on('pageerror',lambda e:ошибки.append(str(e)))
    pg.on('console',lambda m:ошибки.append(m.text) if m.type=='error' else None)
    pg.goto('http://127.0.0.1:8095/'+urllib.parse.quote('схемы.html')); pg.wait_for_timeout(2500)
    pg.locator('#лист-A').screenshot(path='кадры/схема_A.png')
    pg.locator('#лист-D').screenshot(path='кадры/схема_D.png')
    print('ошибки:',ошибки)
    br.close()
srv.shutdown()
print('готово')
