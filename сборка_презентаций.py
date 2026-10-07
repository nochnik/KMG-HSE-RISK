# -*- coding: utf-8 -*-
"""Сборка презентаций A и D (16:9, 5 слайдов). Перезапускаемый."""
import os, winreg
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

BASE = r"C:\Users\Talap_obs\Documents\KMGD"
КАДРЫ = os.path.join(BASE, "KMG-HSE-RISK", "кадры")
OUT = os.path.join(BASE, "Конкурс_ПБ_2026")


def rgb(h):
    return RGBColor.from_string(h.lstrip("#"))


БУМАГА, ЧЕРНИЛА, ВТОРОЙ = "FFFFFF", "231F20", "55606B"   # айдентика КМГ: тёмно-серый логотипа
СИГНАЛ, ЗЕЛ, ЯНТ, КРАСН = "02AEF0", "1B8A4C", "D98E04", "C8102E"   # синий логотипа КМГ
КМГ_СВЕТ = "90D6F7"
ЛОГО = os.path.join(os.path.dirname(os.path.abspath(__file__)), "медиа", "лого_кмг.png")


def font_installed(name):
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            k = winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        except OSError:
            continue
        i = 0
        while True:
            try:
                n, _, _ = winreg.EnumValue(k, i)
            except OSError:
                break
            if name.lower() in n.lower():
                return True
            i += 1
    return False


ШРИФТ = "IBM Plex Sans" if font_installed("IBM Plex Sans") else "Segoe UI"
МОНО = "IBM Plex Mono" if font_installed("IBM Plex Mono") else "Consolas"
print("Шрифт:", ШРИФТ, "/", МОНО)

ФУТЕР = "Конкурс Председателя Правления КМГ по ПБ, ОТ и ОС · 2026 · ТОО «KMG Digital»"
АВТОР = "Аульбеков Адильжан · бизнес-аналитик (инженер) · Дирекция по продуктам · ТОО «KMG Digital»"
ИСТОЧНИК_A = "Годовой отчёт АО НК «КазМунайГаз» 2025; заседание Правительства 02.06.2026; сообщение компании за 1 полугодие 2026"
ИСТОЧНИК_D = ИСТОЧНИК_A + "; IOGP Safety performance indicators 2024"


def текст(slide, x, y, w, h, runs, size, color=ЧЕРНИЛА, bold=False, font=None,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = runs if isinstance(runs, list) else [runs]
    for i, t in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = t
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = font or ШРИФТ
        r.font.color.rgb = rgb(color)
    return tb


def новый(prs, n, title, sub=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(БУМАГА)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = rgb(СИГНАЛ)
    bar.line.fill.background()
    # логотип КМГ в правом верхнем углу (цветной, на белом)
    if os.path.exists(ЛОГО):
        s.shapes.add_picture(ЛОГО, Inches(10.55), Inches(0.3), height=Inches(0.42))
    текст(s, 0.55, 0.32, 9.8, 0.6, title, 32, bold=True)
    if sub:
        текст(s, 0.55, 0.92, 12.2, 0.4, sub, 18, ВТОРОЙ)
    текст(s, 0.55, 7.05, 11.6, 0.3, ФУТЕР, 12, ВТОРОЙ, align=PP_ALIGN.RIGHT)
    текст(s, 12.2, 7.05, 0.6, 0.3, str(n), 12, ВТОРОЙ, bold=True, align=PP_ALIGN.RIGHT)
    return s


ОТСУТСТВУЮТ = []


def кадр(s, names, x, y, maxw, maxh):
    """names: кандидаты (первый существующий). Возвращает нижнюю границу кадра."""
    path = next((os.path.join(КАДРЫ, n) for n in names
                 if os.path.exists(os.path.join(КАДРЫ, n))), None)
    for n in names:
        if not os.path.exists(os.path.join(КАДРЫ, n)):
            ОТСУТСТВУЮТ.append(n)
    ar = 1080 / 1920
    if path:
        with Image.open(path) as im:
            ar = im.height / im.width
    w = maxw
    h = w * ar
    if h > maxh:
        h = maxh
        w = h / ar
    x0 = x + (maxw - w) / 2
    if path:
        pic = s.shapes.add_picture(path, Inches(x0), Inches(y), Inches(w), Inches(h))
        pic.line.color.rgb = rgb(ЧЕРНИЛА)
        pic.line.width = Pt(1.5)
    else:
        print("ПРЕДУПРЕЖДЕНИЕ: нет кадра", names[0])
        r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x0), Inches(y), Inches(w), Inches(h))
        r.fill.solid()
        r.fill.fore_color.rgb = rgb("D0D5DD")
        r.line.color.rgb = rgb(ЧЕРНИЛА)
        r.line.width = Pt(1.5)
        tf = r.text_frame
        tf.text = "кадр: " + names[0]
        f = tf.paragraphs[0].runs[0].font
        f.size = Pt(24)
        f.name = ШРИФТ
        f.color.rgb = rgb(ВТОРОЙ)
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    return y + h


def титул(prs, title, sub, nums, источник):
    s = новый(prs, 1, title)
    текст(s, 0.55, 1.15, 12.2, 1.0, sub, 18, ВТОРОЙ)
    текст(s, 0.55, 2.35, 12.2, 0.4, АВТОР, 16, ЧЕРНИЛА)
    for i, (big, col, cap) in enumerate(nums):
        x = 0.55 + i * 4.15
        текст(s, x, 3.3, 4.0, 1.1, big, 56, col, bold=True, font=МОНО)
        текст(s, x, 4.55, 3.8, 1.3, cap, 17, ЧЕРНИЛА)
    текст(s, 0.55, 6.45, 12.2, 0.5, "Источник: " + источник, 11, ВТОРОЙ)


def со_кадром(prs, n, title, names, caption):
    s = новый(prs, n, title)
    низ = кадр(s, names, 0.55, 1.05, 12.2, 5.35)
    текст(s, 0.55, низ + 0.12, 12.2, 0.8, caption, 14, ВТОРОЙ)


def два_кадра(prs, n, title, left, right, caption):
    """Слева широкий кадр страницы, справа узкий кадр панели."""
    s = новый(prs, n, title)
    низ1 = кадр(s, left, 0.55, 1.05, 7.9, 5.35)
    низ2 = кадр(s, right, 8.7, 1.05, 4.05, 5.35)
    текст(s, 0.55, max(низ1, низ2) + 0.12, 12.2, 0.8, caption, 14, ВТОРОЙ)


def эффект(prs, n, items, head):
    s = новый(prs, n, "Эффект")
    кадр(s, ["04_эффект.png"], 0.55, 1.15, 7.6, 5.5)
    x, w = 8.45, 4.4
    текст(s, x, 1.15, w, 0.5, head, 18, ЧЕРНИЛА, bold=True)
    tb = s.shapes.add_textbox(Inches(x), Inches(1.75), Inches(w), Inches(5.1))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, t in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        r = p.add_run()
        r.text = "• " + t
        r.font.size = Pt(16)
        r.font.name = ШРИФТ
        r.font.color.rgb = rgb(ЧЕРНИЛА)


СПРАВКА = [
    ("ЭНД", "электронный наряд-допуск: оформление, инструктаж с ЭЦП, контроль ГВС, закрытие без бумаги; ИИ проверяет мероприятия. ОМГ (ОПЭ), 2026 — КБМ, ММГ"),
    ("TUMAR", "компьютерное зрение на бригадах ПРС/КРС (КМГ Инжиниринг): СИЗ, опасная зона при СПО, гидроключ; сигнал бригаде, журнал. ОСК 60 бригад, тираж ОМГ, ОМС, КБМ, ЭМГ; к 2027 — 242 бригады"),
    ("«Управление поездками»", "заявки на транспорт и GPS-мониторинг с уведомлениями о скорости и резком торможении. 7 ДЗО, 3 000+ единиц техники"),
    ("«Қорғау»", "карточки работников об опасных условиях и действиях. ДПБ КМГ, все ДЗО"),
    ("Реестр инцидентов", "база происшествий и актов расследования; развитие реестров рисков и инцидентов — план ДПБ на 2026"),
    ("АСДЦ", "Аналитическая система Диспетчерского центра КМГ (с 2015): единая платформа производственных данных ДЗО, включая инциденты и ЧС"),
    ("KMG AISAP", "цифровая платформа закупок группы: потребность, маркетинг цен, тендер, договор"),
]


def справка(prs, n, подзаголовок):
    """Слайд для комиссий ДЗО: что такое системы-источники. Новых систем не требуется."""
    s = новый(prs, n, "Справочно: системы-источники", подзаголовок)
    for i, (имя, что) in enumerate(СПРАВКА):
        col, row = i % 2, i // 2
        x = 0.55 + col * 6.2
        y = 1.5 + row * 1.35
        текст(s, x, y, 5.9, 0.4, имя, 18, СИГНАЛ, bold=True)
        текст(s, x, y + 0.38, 5.9, 0.95, что, 13, ЧЕРНИЛА)


def сохранить(prs, name):
    path = os.path.join(OUT, name + ".pptx")
    prs.save(path)
    print("pptx:", path)
    return path


def новая():
    p = Presentation()
    p.slide_width = Inches(13.333)
    p.slide_height = Inches(7.5)
    return p


# ---------- A ----------
A = новая()
титул(A, "Индекс риска работ повышенной опасности",
      "ИИ-оценка наряда-допуска и бригады до начала работ на опережающих индикаторах · для собственных и подрядных бригад",
      [("10,38", КРАСН, "FAR подрядных организаций, 2025 (IOGP 0,84)"),
       ("1 из 3", ЯНТ, "несчастных случаев — на работах повышенной опасности"),
       ("3", КРАСН, "смертельных случая в ДЗО за 1 полугодие 2026")], ИСТОЧНИК_A)
со_кадром(A, 2, "Как работает контур", ["схема_A.png", "01_обзор.png"],
          "Четыре системы фиксируют нарушение по факту. Индекс отвечает заранее: какая работа и какая бригада сегодня в зоне риска. Решение принимает человек")
со_кадром(A, 3, "Экран мастера", ["02_смена.png"],
          "Светофор наряда: зелёный — обычный допуск, жёлтый — целевой инструктаж и ИИ-мероприятия, красный — эскалация в службу ПБ. Индекс не входит в KPI премирования")
эффект(A, 4, ["Снижение НС под контуром — 15 % (референсы 20–40 %)",
              "Смертельный НС: ~100 млн тг прямых выплат (10 годовых зарплат по колдоговору) + страховые, расследование, простой",
              "Одно ДЗО: ~68 млн тг в год предотвращённых потерь",
              "Четыре добывающих ДЗО: ~180 млн тг в год, ~360 млн тг за 3 года",
              "Затраты: ~120 млн тг в первый год, без капвложений",
              "Каждый предотвращённый смертельный случай — ещё 100+ млн тг"],
       "Оценка, параметры открыты")
со_кадром(A, 5, "Дорожная карта тиража", ["06_дорожная_карта.png"],
          "Пилот ОМГ (ЭНД + TUMAR + «Управление поездками» уже работают) → ММГ, КБМ → ЭМГ, ОСК → НПЗ. От ДЗО нужен только доступ к событиям систем")
pa = справка(A, 6, "Все уже работают в группе КМГ. Индекс читает их события, новых систем и оборудования не требуется")
сохранить(A, "Презентация_A")

# ---------- D ----------
D = новая()
титул(D, "Паспорт безопасности подрядчика в закупках",
      "Рейтинг A–D по производственной безопасности из данных систем группы · гейт допуска к работам повышенной опасности в KMG AISAP",
      [("10,38", КРАСН, "FAR подрядных организаций КМГ, 2025 (2024 — 3,86)"),
       ("82 %", ЯНТ, "смертельных и инвалидизирующих случаев в отрасли — подрядчики (IOGP)"),
       ("5 883", ЧЕРНИЛА, "ручных проверок ПБ подрядчиков за 2025 год, не связанных с допуском к тендеру")], ИСТОЧНИК_D)
со_кадром(D, 2, "Как это работает", ["схема_D.png", "05_подрядчик.png"],
          "Пять компонентов рейтинга: НС и FAR, нарушения TUMAR, ДТП и скорость, предписания, обучение. Класс обновляется ежемесячно и действует во всех ДЗО")
два_кадра(D, 3, "Паспорт и гейт в AISAP", ["05_подрядчик.png"], ["05б_паспорт.png", "05_подрядчик.png"],
          "A и B — допуск; C — допуск с планом улучшений и повторной оценкой через 6 месяцев; D — работы повышенной опасности закрыты. Рейтинг прозрачен подрядчику в личном кабинете")
эффект(D, 4, ["Прямое давление на FAR 10,38: подрядчики класса D не попадают на работы повышенной опасности",
              "Дорожная карта ДПБ по подрядчикам 2025–2027 требует измеримых KPI — паспорт их даёт",
              "Одно ДЗО: ~70 млн тг в год при снижении НС подрядчиков на 15 %",
              "Тираж на сервисные и добывающие ДЗО: 200+ млн тг в год",
              "Затраты: ~80 млн тг в первый год, без оборудования",
              "Предотвращение ответственности заказчика за последствия"],
       "Оценка, параметры открыты")
со_кадром(D, 5, "Дорожная карта", ["06_дорожная_карта.png"],
          "Пилот ОСК и ОТК (TUMAR и «Управление поездками» уже работают) → ОКК, ОМГ → все добывающие ДЗО. Гейт в AISAP обязателен для работ повышенной опасности с Q3 2027")
pd = справка(D, 6, "Все уже работают в группе КМГ. Паспорт считается из их данных, новых проверок не требуется")
сохранить(D, "Презентация_D")


# ---------- PDF ----------
def экспорт(paths):
    try:
        import win32com.client
    except ImportError:
        print("win32com недоступен — только pptx")
        return
    app = None
    try:
        app = win32com.client.Dispatch("PowerPoint.Application")
        for p in paths:
            pres = app.Presentations.Open(p, WithWindow=False)
            try:
                pdf = os.path.splitext(p)[0] + ".pdf"
                pres.SaveAs(pdf, 32)
                print("pdf:", pdf)
            finally:
                pres.Close()
    except Exception as e:
        print("COM не сработал, остаются только pptx:", e)
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass


экспорт([pa, pd])
print("Отсутствовали кадры:", sorted(set(ОТСУТСТВУЮТ)))
