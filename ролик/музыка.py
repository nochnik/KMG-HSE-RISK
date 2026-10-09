# -*- coding: utf-8 -*-
# Музыка к ролику «Светофор наряда» (72 c) — синтез кодом (numpy/scipy), на базе _образец/kmgd-showreel/showreel_music.py.
# Темп 120 BPM: доля 0.5 c, такт 2 c, сетка от 9 c (конец интро). Все смены сцен (9, 19, 29, 39, 47, 55, 65 c)
# стоят на начале такта. Интро тише; «индекс» и «мастер» плотнее; «эффект» — только пэд и колокол (без бочки:
# речь о людях); финал — светлый ре-мажор. Нормализация до −14 LUFS (BS.1770, K-фильтр + гейтинг).
# Запуск: python музыка.py [выход.wav]
import sys, os, wave, numpy as np
from scipy.signal import butter, lfilter

SR = 48000; DUR = 72.0                                    # = DUR ролика (сумма длит в СЦЕНЫ ролик.html)
BEAT = .5; BAR = 2.0; G0 = 9.0
СТЫКИ = [9, 19, 29, 39, 47, 55, 65]                        # начала сцен 2..8
СЦЕНА = lambda t: sum(t >= s for s in СТЫКИ)              # 0 интро … 7 финал
N = int(SR * DUR); L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)
NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or at < 0: return
    sig = sig[:N - i] * gain
    L[i:i + len(sig)] += sig * min(1, 1 - pan); R[i:i + len(sig)] += sig * min(1, 1 + pan)
def env(n, a=.002, d=.2, c=4.0):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-c * t / d)
def lp(x, f, order=2): b, a = butter(order, min(f, SR / 2.2) / (SR / 2)); return lfilter(b, a, x)
def hp(x, f, order=2): b, a = butter(order, f / (SR / 2), 'high'); return lfilter(b, a, x)
def lps(x, fc, seg=2400):
    y = np.zeros_like(x); zi = np.zeros(2)
    for s in range(0, len(x), seg):
        b, a = butter(2, min(float(fc[s]), SR / 2.2) / (SR / 2)); y[s:s + seg], zi = lfilter(b, a, x[s:s + seg], zi=zi)
    return y
def saw(f, n): ph = np.cumsum(np.broadcast_to(f, (n,)) / SR) % 1; return 2 * ph - 1
def sine(f, n): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(f, (n,)) / SR))

# ---------- инструменты (как в образце) ----------
def kick(g=1):
    n = int(.5 * SR); t = np.arange(n) / SR; f = 46 + 120 * np.exp(-t * 30)
    return (sine(f, n) * env(n, .001, .45, 3.4) + .2 * hp(rng.standard_normal(n), 3000) * env(n, .0005, .012)) * g
def hat(open_=False):
    n = int((.25 if open_ else .07) * SR); return hp(rng.standard_normal(n), 7500, 4) * env(n, .0005, .22 if open_ else .05, 4)
def clap():
    n = int(.35 * SR); x = lp(hp(rng.standard_normal(n), 1000), 6000)
    e = sum(np.pad(env(n - int(o * SR), .0005, .16, 5), (int(o * SR), 0)) for o in (0, .012, .024)); return x * e * .6
def bass(m, dur):
    n = int(dur * SR); f = NOTE(m - 24); x = .6 * saw(f, n) + sine(f, n); return lp(x, 380) * env(n, .005, dur * 1.4, 2.2)
def pluck(m, dur=.25, bright=3200):
    n = int(dur * SR); f = NOTE(m); x = .6 * saw(f, n) + .4 * sine(f * 2, n); return lp(x, bright) * env(n, .002, .18, 4)
def bell(m, dur=2.5):
    n = int(dur * SR); f = NOTE(m); t = np.arange(n) / SR
    x = sine(f, n) + .45 * sine(f * 2.76, n) * np.exp(-t * 3) + .25 * sine(f * 5.4, n) * np.exp(-t * 6); return x * env(n, .002, dur, 3.2)
def pad(notes, dur, bright=1400):
    n = int(dur * SR); x = np.zeros(n)
    for m in notes:
        for det in (-.07, .07): x += saw(NOTE(m) * 2 ** (det / 12), n)
    t = np.arange(n) / SR; a = np.minimum(1, t / .6) * np.minimum(1, (dur - t) / .6)
    return lp(x / (len(notes) * 2), bright) * a
def whoosh(dur=.8):
    n = int(dur * SR); k = np.linspace(0, 1, n); y = lps(rng.standard_normal(n), 300 + 7000 * k); return y * np.sin(np.pi * k) ** 2 * .5
def impact(g=1, dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    return (sine(34 + 70 * np.exp(-t * 8), n) * env(n, .001, dur, 2.6) + hp(rng.standard_normal(n), 2500) * env(n, .001, 1.6, 4) * .3) * g
def riser(dur, g=.4):
    n = int(dur * SR); k = np.linspace(0, 1, n); y = lps(rng.standard_normal(n), 300 + 9000 * k ** 2)
    return (lp(saw(NOTE(50) * 2 ** (k * 2), n) * .15, 2000) + y) * k ** 2 * g

# Гармония: Dm – B♭ – F – C по тактам
CH = [(50, [62, 65, 69]), (46, [58, 62, 65]), (53, [60, 65, 69]), (48, [60, 64, 67])]
def chord_at(t): return CH[int(((t - G0) // BAR) % 4)] if t >= G0 else CH[0]

# ---------- интро 0–7: тёмный дрон, колокол на каждое число (0.4 / 2.4 / 4.4), подводка ----------
n = int(G0 * SR); tt = np.arange(n) / SR
add(lps(saw(NOTE(38), n) + saw(NOTE(45) * 1.003, n), 250 + 1200 * (tt / G0) ** 2) * np.minimum(1, tt / 2.0) * .18, 0)
add(pad([62, 65, 69, 74], G0 + .5, 800), 0, .2)
for at, m in [(.4, 74), (2.4, 77), (4.4, 69)]: add(bell(m, 3.0), at, .22); add(impact(.25, 1.2), at)
add(riser(1.6, .32), G0 - 1.6)
add(impact(.9), G0)

# ---------- основная часть 7–53: ритм по долям, плотность по сценам ----------
ПЛОТН = {1: 1, 2: 2, 3: 2, 4: 1, 5: 1}                    # контуры, индекс, мастер, фото, дпб
for b in np.arange(G0, 55 - 1e-6, BEAT):
    сц = СЦЕНА(b + 1e-3); пл = ПЛОТН[сц]; bi = int(round((b - G0) / BEAT)); root, notes = chord_at(b + .01)
    if not (сц == 4 and bi % 2): add(kick(.75 if пл == 1 else .9), b)      # фото: бочка только на сильных долях
    if bi % 2 == 1 and пл == 2: add(clap(), b, .32)
    add(hat(), b + BEAT / 2, .1, .3)
    if пл == 2: add(hat(), b + BEAT / 4, .05, -.3); add(hat(), b + 3 * BEAT / 4, .05, .35)
    add(bass(root, BEAT * .45), b + BEAT / 2, .5)
    arp = [notes[0] + 12, notes[2] + 12, notes[1] + 12, notes[2]]
    for j, m in enumerate(arp): add(pluck(m, .2, 2400 if пл == 1 else 3600), b + j * BEAT / 4, .07 if пл == 1 else .1, (-.45, .45)[j % 2])
for bar in np.arange(G0, 53 - 1e-6, BAR):
    root, notes = chord_at(bar + .01); add(pad(notes + [notes[0] + 12], BAR + .3, 1300 if ПЛОТН[СЦЕНА(bar + 1e-3)] == 1 else 1800), bar, .15)
# акценты под события в кадре: бейджи «событие», факторы индекса, нажатие мастера, рамки фотопроверки, урок ДПБ
for k in range(4): add(pluck(81, .3, 4200), 7 + 2.3 + k * .5, .12, (-.3, .3)[k % 2])
for k in range(5): add(bell([74, 77, 81, 84, 86][k], 1.2), 17 + 2.7 + k * .75, .1, (k % 3 - 1) * .3)
add(bell(86, 2.0), 27 + 7.95, .16); add(impact(.3, 1.2), 27 + 7.95)
for k, f in enumerate([.2, .28, .78, .88]): add(pluck(76 if k < 3 else 70, .25, 4000), 37 + 1.2 + 3 * f, .12)
add(whoosh(1.2), 45 + 3.2, .6); add(bell(81, 1.8), 45 + 4.5, .14)
# переходы: вжух перед стыком и мягкий удар на стыке
for t in СТЫКИ[1:]: add(whoosh(.9), t - .75, .8); add(impact(.32, 1.4), t)

# ---------- эффект 53–63: только пэд и колокол, без бочки ----------
for bar in np.arange(55, 65 - 1e-6, BAR):
    root, notes = chord_at(bar + .01); add(pad(notes + [notes[0] + 12, notes[1] + 12], BAR + .4, 1000), bar, .2)
    add(bass(root, BAR * .9), bar, .25)
for at, m in [(55.4, 74), (59.6, 77), (60.4, 81), (61.8, 72)]: add(bell(m, 3.5), at, .2 if at < 61 else .12, (-.2, .2)[int(at) % 2])

# ---------- финал 63–70: светлый ре-мажор, логотип ----------
add(pad([62, 66, 69, 74, 78], DUR - 65, 2200), 65, .26)
add(bass(50, 4.0), 65, .35)
for j, m in enumerate([74, 78, 81, 86]): add(bell(m, 4.5), 65.3 + j * .09, .15, (-.3, .3)[j % 2])
add(kick(.6), 65.3); add(bell(62, 4), 66.6, .1)

# ---------- реверб, громкость, затухание ----------
def reverb(x, sec=2.0, mix=.22, seed=1):
    r = np.random.default_rng(seed); k = int(sec * SR); ir = lp(r.standard_normal(k) * np.exp(-np.arange(k) / SR * 3.2), 6000)
    nf = 1 << (len(x) + k - 1).bit_length(); y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:len(x)]
    return x + mix * y * (np.max(np.abs(x)) / (np.max(np.abs(y)) + 1e-9))
L, R = reverb(L, seed=1), reverb(R, seed=2)
fade = np.ones(N); a = int((DUR - 1.4) * SR); fade[a:] = np.linspace(1, 0, N - a) ** 2
fade[:int(.05 * SR)] = np.linspace(0, 1, int(.05 * SR))
mx = np.stack([L * fade, R * fade], 1); mx = np.tanh(mx / (np.max(np.abs(mx)) * .75)) * .9

def lufs(x):
    """Интегральная громкость по ITU-R BS.1770-4 (K-фильтр 48 кГц, блоки 400 мс, гейты −70 и −10 LU)."""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, .73248077421585]
    b2, a2 = [1, -2, 1], [1, -1.99004745483398, .99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(.4 * SR), int(.1 * SR)
    ms = np.array([np.mean(y[i:i + blk] ** 2, axis=0).sum() for i in range(0, len(y) - blk, hop)])
    g = ms[-.691 + 10 * np.log10(ms + 1e-12) > -70]
    rel = -.691 + 10 * np.log10(g.mean()) - 10; g = g[(-.691 + 10 * np.log10(g + 1e-12)) > rel]
    return -.691 + 10 * np.log10(g.mean())

from scipy.signal import resample_poly
from scipy.ndimage import minimum_filter1d, uniform_filter1d
def лимитер(x, потолок=.84):
    """Ограничитель по true peak: пик ищется на 4× передискретизации, усиление сглаживается (5 мс), без щелчков."""
    tp = np.abs(resample_poly(x, 4, 1, axis=0)).max(axis=1)[:len(x) * 4].reshape(-1, 4).max(axis=1)
    g = np.minimum(1, потолок / (tp + 1e-9)); g = minimum_filter1d(g, 480); g = uniform_filter1d(g, 240)
    return x * g[:, None]
def тп(x): return 20 * np.log10(np.abs(resample_poly(x, 4, 1, axis=0)).max())

for _ in range(6):                                        # подгонка к −14 LUFS при true peak не выше −1 dBTP
    mx = лимитер(mx * 10 ** ((-14 - lufs(mx)) / 20))
print(f'LUFS {lufs(mx):.2f}, true peak {тп(mx):.2f} dBTP')
выход = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'музыка.wav')
with wave.open(выход, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mx, -1, 1) * 32767).astype('<i2').tobytes())
print('музыка готова', выход, DUR, 'c')
