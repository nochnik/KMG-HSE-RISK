# -*- coding: utf-8 -*-
"""Рендер HTML-ролика в MP4: покадрово, без записи экрана.

Страница обязана выставить window.__story = {duration, fps, width, height, renderAt(t), ready}
(так устроены и образец kmgd-showreel, и шаблон ролик.html). Скрипт зовёт renderAt(i/fps),
снимает скриншот и отдаёт PNG в ffmpeg. Время в ролике не «идёт», а задаётся — поэтому
тяжёлый кадр не тормозит видео, и ролик можно резать на куски и снимать параллельно.

Почему не render-parallel.js из образца: в архиве он не совпадает с HTML — снимает
вертикальный кадр 1080×1920 вместо 1920×1080 и ждёт класс has3d, который страница
не ставит (рендер падает сразу). К тому же Node-Playwright здесь не установлен,
а Python-Playwright + Chrome уже работают в ИСХОДНИКИ/аиан_в_mp4.py. Размер кадра
теперь берётся из __story, а не зашит в скрипт.

Запуск (страница должна открываться с локального сервера, через file:// модули и 3D не грузятся):
  python шаблон/рендер.py "http://localhost:8765/шаблон/ролик.html?render" выход.mp4
  python шаблон/рендер.py <url> выход.mp4 --потоков 6 --с 10 --по 20      — только кусок 10–20 c
  python шаблон/рендер.py <url> выход.mp4 --музыка музыка.wav           — сразу со звуком
"""
import sys, os, subprocess, tempfile, time, argparse
from multiprocessing import Process, Queue


def открыть(pw, url):
    # swiftshader — программный WebGL: в headless без него three.js (3D в образце) не стартует
    br = pw.chromium.launch(channel='chrome', headless=True,
                            args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    стр = br.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1)
    # python -m http.server держит очередь на 5 подключений: при 6 потоках часть получает
    # ERR_CONNECTION_REFUSED. Повтор + разнесённый старт потоков (см. main) это снимают.
    for попытка in range(5):
        try: стр.goto(url, wait_until='networkidle'); break
        except Exception:
            if попытка == 4: raise
            time.sleep(1 + попытка)
    п = стр.evaluate('async () => { await window.__story.ready; const s = window.__story; return {d: s.duration, fps: s.fps, w: s.width, h: s.height}; }')
    if (п['w'], п['h']) != (1920, 1080):
        стр.set_viewport_size({'width': п['w'], 'height': п['h']})
    return br, стр, п


def кусок(k, url, к0, к1, путь, очередь):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br, стр, п = открыть(pw, url)
        fps, w, h = п['fps'], п['w'], п['h']
        ff = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'png', '-i', '-',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                               '-r', str(fps), '-g', str(fps * 2), путь], stdin=subprocess.PIPE)
        for i in range(к0, к1):
            # renderAt может вернуть промис (образец ждёт перемотку видео-клипа); два rAF — чтобы браузер успел отрисовать
            стр.evaluate('async t => { await window.__story.renderAt(t); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); }', i / fps)
            ff.stdin.write(стр.screenshot(type='png', clip={'x': 0, 'y': 0, 'width': w, 'height': h}))
            if (i - к0) % 60 == 0: очередь.put(f'[п{k}] кадр {i - к0 + 1}/{к1 - к0}')
        ff.stdin.close(); ff.wait(); br.close()
        if ff.returncode: raise SystemExit(f'ffmpeg упал на куске {k}')


def main():
    ап = argparse.ArgumentParser()
    ап.add_argument('url'); ап.add_argument('выход')
    ап.add_argument('--потоков', type=int, default=max(1, min(6, (os.cpu_count() or 4) // 2)))
    ап.add_argument('--с', type=float, default=0); ап.add_argument('--по', type=float)
    ап.add_argument('--музыка', help='wav/mp3, кладётся с 0 c; длиннее видео — обрезается')
    а = ап.parse_args()

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br, _, п = открыть(pw, а.url); br.close()
    fps = п['fps']; конец = min(а.по or п['d'], п['d'])
    к0, к1 = round(а.с * fps), round(конец * fps); всего = к1 - к0
    n = max(1, min(а.потоков, всего // fps or 1)); шаг = -(-всего // n)
    print(f'{п["w"]}×{п["h"]}, {fps} к/с, {а.с:.1f}–{конец:.1f} c = {всего} кадров, потоков: {n}')

    t0 = time.time(); вр = tempfile.mkdtemp(prefix='рендер-'); очередь = Queue(); куски, проц = [], []
    for k in range(n):
        a, b = к0 + k * шаг, min(к1, к0 + (k + 1) * шаг)
        if a >= b: break
        путь = os.path.join(вр, f'к{k}.mp4'); куски.append(путь)
        р = Process(target=кусок, args=(k, а.url, a, b, путь, очередь)); р.start(); проц.append(р); time.sleep(1.5)
    while any(р.is_alive() for р in проц) or not очередь.empty():
        try: print(очередь.get(timeout=1))
        except Exception: pass
    if any(р.exitcode for р in проц): sys.exit('рендер упал — см. ошибки выше')

    список = os.path.join(вр, 'список.txt')
    open(список, 'w', encoding='utf-8').write('\n'.join(f"file '{к}'" for к in куски))
    немой = а.выход if not а.музыка else os.path.join(вр, 'немой.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', список, '-c', 'copy', '-movflags', '+faststart', немой], check=True)
    if а.музыка:
        # видео не перекодируется; звук — AAC 192k, обрезан по длине видео
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', немой, '-ss', str(а.с), '-i', а.музыка,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', а.выход], check=True)
    print(f'Готово: {а.выход}, {всего} кадров за {time.time() - t0:.0f} c')


if __name__ == '__main__':
    main()
