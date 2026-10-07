# -*- coding: utf-8 -*-
"""Съёмка кадров прототипа KMG-HSE-RISK: локальный http.server на 8093, Chrome headless,
1920×1080, scale 1. Для каждой страницы собираются ошибки консоли и pageerror.
Запуск: python снять_кадры.py  (из любой папки; кадры/ в корне репо)."""
import threading, http.server, functools, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

КОРЕНЬ = os.path.dirname(os.path.abspath(__file__))
КАДРЫ = os.path.join(КОРЕНЬ, 'кадры')
ПОРТ = 8093
СТРАНИЦЫ = [
    ('index.html',          '01_обзор.png'),
    ('смена.html',          '02_смена.png'),
    ('карта.html',          '03_карта.png'),
    ('эффект.html',         '04_эффект.png'),
    ('подрядчик.html',      '05_подрядчик.png'),
    ('дорожная_карта.html', '06_дорожная_карта.png'),
]

class Тихий(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/favicon.ico':  # Chrome запрашивает иконку; без неё был бы ложный 404 в консоли
            self.send_response(204); self.end_headers(); return
        super().do_GET()

def main():
    os.makedirs(КАДРЫ, exist_ok=True)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', ПОРТ), functools.partial(Тихий, directory=КОРЕНЬ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    всего_ошибок = 0
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel='chrome', headless=True)
            ctx = br.new_context(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1, locale='ru-RU')
            for файл, кадр in СТРАНИЦЫ:
                if not os.path.exists(os.path.join(КОРЕНЬ, файл)):
                    print(f'[пропуск] {файл}: файла нет'); continue
                ошибки = []
                pg = ctx.new_page()
                pg.on('console', lambda m, о=ошибки: о.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
                pg.on('pageerror', lambda e, о=ошибки: о.append('pageerror: ' + str(e)))
                url = f'http://127.0.0.1:{ПОРТ}/' + urllib.parse.quote(файл)
                pg.goto(url, wait_until='load')
                pg.wait_for_timeout(1500)  # шрифты Google или фолбэк
                if файл == 'смена.html':
                    # первый наряд выбран, панель с карточкой видна
                    pg.wait_for_selector('table.таблица tr.выбрана', timeout=5000)
                    pg.wait_for_selector('#панель h3', state='visible', timeout=5000)
                    первая = pg.eval_on_selector('table.таблица tbody tr', 'tr => tr.classList.contains("выбрана")')
                    if not первая:
                        pg.click('table.таблица tbody tr'); pg.wait_for_timeout(200)
                путь = os.path.join(КАДРЫ, кадр)
                pg.screenshot(path=путь)
                # отфильтровать шум о недоступности шрифтов без сети
                ошибки = [о for о in ошибки if 'fonts.googleapis.com' not in о and 'fonts.gstatic.com' not in о]
                всего_ошибок += len(ошибки)
                статус = 'ОК' if not ошибки else f'{len(ошибки)} ошибок'
                print(f'[{статус}] {файл} → {путь}')
                for о in ошибки: print('    ' + о)
                pg.close()
            br.close()
    finally:
        srv.shutdown()
    return всего_ошибок

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
