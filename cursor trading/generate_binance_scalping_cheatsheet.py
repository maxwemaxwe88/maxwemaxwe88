#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm

FONT_REG = "DejaVu"
FONT_BOLD = "DejaVu-Bold"

FONT_CANDIDATES = [
    (FONT_REG, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    (FONT_BOLD, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

PALETTE = {
    "navy": colors.HexColor("#0b1f3a"),
    "blue": colors.HexColor("#2c7be5"),
    "green": colors.HexColor("#3bb273"),
    "red": colors.HexColor("#f06449"),
    "orange": colors.HexColor("#f6ae2d"),
    "gray": colors.HexColor("#6c757d"),
    "light": colors.HexColor("#f5f7fb"),
    "border": colors.HexColor("#d4dbe7"),
}


def register_fonts() -> None:
    for name, path in FONT_CANDIDATES:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))
        else:
            raise FileNotFoundError(f"Font not found: {path}")


def draw_header(c: canvas.Canvas, title: str, subtitle: str) -> None:
    c.setFillColor(PALETTE["navy"])
    c.rect(0, PAGE_H - 2.8 * cm, PAGE_W, 2.8 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 20)
    c.drawString(MARGIN, PAGE_H - 1.4 * cm, title)
    c.setFont(FONT_REG, 10)
    c.drawString(MARGIN, PAGE_H - 2.1 * cm, subtitle)
    c.setFillColor(colors.black)


def draw_footer(c: canvas.Canvas, text: str) -> None:
    c.setFont(FONT_REG, 8)
    c.setFillColor(PALETTE["gray"])
    c.drawString(MARGIN, 0.75 * cm, text)
    c.setFillColor(colors.black)


def draw_section_title(c: canvas.Canvas, x: float, y: float, text: str) -> float:
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(PALETTE["navy"])
    c.drawString(x, y, text)
    c.setFillColor(colors.black)
    return y - 0.5 * cm


def draw_bullets(
    c: canvas.Canvas,
    x: float,
    y: float,
    lines: list[str],
    size: float = 9.5,
    leading: float = 0.48 * cm,
) -> float:
    c.setFont(FONT_REG, size)
    for line in lines:
        c.drawString(x, y, f"• {line}")
        y -= leading
    return y


def draw_arrow(
    c: canvas.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    size: float = 6,
) -> None:
    c.line(x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    left = (
        x2 - size * math.cos(angle - 0.4),
        y2 - size * math.sin(angle - 0.4),
    )
    right = (
        x2 - size * math.cos(angle + 0.4),
        y2 - size * math.sin(angle + 0.4),
    )
    c.line(x2, y2, left[0], left[1])
    c.line(x2, y2, right[0], right[1])


def draw_orderbook_diagram(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setStrokeColor(PALETTE["border"])
    c.setFillColor(colors.white)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=1)
    mid = x + w / 2
    c.setStrokeColor(PALETTE["border"])
    c.line(mid, y, mid, y + h)
    c.setFont(FONT_BOLD, 8)
    c.setFillColor(PALETTE["gray"])
    c.drawString(x + 0.3 * cm, y + h - 0.45 * cm, "BID")
    c.drawRightString(x + w - 0.3 * cm, y + h - 0.45 * cm, "ASK")

    levels = 7
    bar_h = (h - 1.2 * cm) / levels
    start_y = y + 0.35 * cm
    for idx in range(levels):
        y0 = start_y + idx * bar_h
        bid_w = (w * 0.45) * (0.35 + 0.55 * (levels - idx) / levels)
        ask_w = (w * 0.45) * (0.35 + 0.55 * (idx + 1) / levels)
        c.setFillColor(PALETTE["green"])
        c.rect(mid - bid_w, y0, bid_w - 2, bar_h * 0.6, fill=1, stroke=0)
        c.setFillColor(PALETTE["red"])
        c.rect(mid + 2, y0, ask_w - 2, bar_h * 0.6, fill=1, stroke=0)

    c.setStrokeColor(PALETTE["orange"])
    c.setLineWidth(1.5)
    draw_arrow(c, mid - 1.6 * cm, y + h * 0.6, mid + 1.6 * cm, y + h * 0.6, 5)
    c.setLineWidth(1)
    c.setFillColor(PALETTE["orange"])
    c.setFont(FONT_REG, 7)
    c.drawCentredString(mid, y + h * 0.62 + 0.15 * cm, "СПРЕД")
    c.setFillColor(colors.black)


def diagram_sweep(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    level_y = y + h * 0.52
    c.setStrokeColor(PALETTE["red"])
    c.setLineWidth(1.2)
    c.line(x + 0.3 * cm, level_y, x + w - 0.3 * cm, level_y)
    c.setStrokeColor(PALETTE["blue"])
    draw_arrow(c, x + 0.6 * cm, y + h * 0.25, x + w * 0.45, level_y, 5)
    draw_arrow(c, x + w * 0.45, level_y, x + w * 0.65, level_y + h * 0.2, 5)
    draw_arrow(c, x + w * 0.65, level_y + h * 0.2, x + w * 0.85, level_y - h * 0.1, 5)
    c.setLineWidth(1)


def diagram_absorption(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    level_y = y + h * 0.55
    c.setStrokeColor(PALETTE["green"])
    c.setLineWidth(3)
    c.line(x + 0.5 * cm, level_y, x + w - 0.5 * cm, level_y)
    c.setLineWidth(1)
    c.setStrokeColor(PALETTE["blue"])
    for offset in [0.9, 1.6, 2.3, 3.0]:
        draw_arrow(
            c,
            x + offset * cm,
            y + h * 0.2,
            x + offset * cm,
            level_y,
            4,
        )
    c.setStrokeColor(PALETTE["orange"])
    draw_arrow(c, x + w * 0.55, level_y, x + w * 0.8, y + h * 0.75, 5)


def diagram_imbalance(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    mid = x + w * 0.55
    c.setStrokeColor(PALETTE["border"])
    c.rect(x + 0.2 * cm, y + 0.2 * cm, w - 0.4 * cm, h - 0.4 * cm, stroke=1, fill=0)
    c.line(mid, y + 0.2 * cm, mid, y + h - 0.2 * cm)
    for idx in range(4):
        bar_h = (h - 1.2 * cm) / 4
        y0 = y + 0.35 * cm + idx * bar_h
        c.setFillColor(PALETTE["green"])
        c.rect(mid - (w * 0.45) * (0.6 + 0.1 * idx), y0, w * 0.2, bar_h * 0.55, fill=1, stroke=0)
        c.setFillColor(PALETTE["red"])
        c.rect(mid + 2, y0, w * 0.1, bar_h * 0.55, fill=1, stroke=0)
    c.setStrokeColor(PALETTE["blue"])
    draw_arrow(c, x + w * 0.4, y + h * 0.25, x + w * 0.8, y + h * 0.75, 5)


def diagram_ignition(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setStrokeColor(PALETTE["blue"])
    path = [
        (x + 0.4 * cm, y + h * 0.25),
        (x + w * 0.35, y + h * 0.35),
        (x + w * 0.5, y + h * 0.5),
        (x + w * 0.65, y + h * 0.7),
    ]
    for i in range(len(path) - 1):
        draw_arrow(c, path[i][0], path[i][1], path[i + 1][0], path[i + 1][1], 5)
    c.setStrokeColor(PALETTE["orange"])
    draw_arrow(c, x + w * 0.65, y + h * 0.7, x + w * 0.9, y + h * 0.9, 6)


def diagram_range(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    top = y + h * 0.8
    bot = y + h * 0.2
    c.setStrokeColor(PALETTE["gray"])
    c.setLineWidth(1.2)
    c.line(x + 0.3 * cm, top, x + w - 0.3 * cm, top)
    c.line(x + 0.3 * cm, bot, x + w - 0.3 * cm, bot)
    c.setStrokeColor(PALETTE["blue"])
    points = [
        (x + 0.5 * cm, bot + 0.2 * cm),
        (x + w * 0.35, top - 0.2 * cm),
        (x + w * 0.55, bot + 0.2 * cm),
        (x + w * 0.75, top - 0.2 * cm),
    ]
    for i in range(len(points) - 1):
        c.line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
    c.setLineWidth(1)


def diagram_exhaustion(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setStrokeColor(PALETTE["blue"])
    draw_arrow(c, x + 0.4 * cm, y + h * 0.25, x + w * 0.5, y + h * 0.65, 5)
    c.setStrokeColor(PALETTE["gray"])
    c.line(x + w * 0.5, y + h * 0.65, x + w * 0.7, y + h * 0.65)
    c.setStrokeColor(PALETTE["red"])
    draw_arrow(c, x + w * 0.7, y + h * 0.65, x + w * 0.85, y + h * 0.35, 5)


def diagram_bos(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    level = y + h * 0.58
    c.setStrokeColor(PALETTE["gray"])
    c.setLineWidth(1.2)
    c.line(x + 0.3 * cm, level, x + w - 0.3 * cm, level)
    c.setStrokeColor(PALETTE["blue"])
    points = [
        (x + 0.4 * cm, y + h * 0.25),
        (x + w * 0.35, y + h * 0.48),
        (x + w * 0.5, y + h * 0.38),
        (x + w * 0.62, level),
    ]
    for idx in range(len(points) - 1):
        c.line(points[idx][0], points[idx][1], points[idx + 1][0], points[idx + 1][1])
    c.setStrokeColor(PALETTE["green"])
    draw_arrow(c, x + w * 0.62, level, x + w * 0.78, level + h * 0.18, 5)
    c.setStrokeColor(PALETTE["orange"])
    draw_arrow(c, x + w * 0.78, level + h * 0.18, x + w * 0.88, level, 5)
    c.setStrokeColor(PALETTE["green"])
    draw_arrow(c, x + w * 0.88, level, x + w * 0.96, level + h * 0.22, 5)
    c.setLineWidth(1)


def diagram_choch(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    level = y + h * 0.52
    c.setStrokeColor(PALETTE["gray"])
    c.setLineWidth(1.2)
    c.line(x + 0.3 * cm, level, x + w - 0.3 * cm, level)
    c.setStrokeColor(PALETTE["red"])
    points = [
        (x + 0.4 * cm, y + h * 0.75),
        (x + w * 0.3, y + h * 0.55),
        (x + w * 0.45, y + h * 0.63),
        (x + w * 0.6, y + h * 0.42),
    ]
    for idx in range(len(points) - 1):
        c.line(points[idx][0], points[idx][1], points[idx + 1][0], points[idx + 1][1])
    c.setStrokeColor(PALETTE["green"])
    draw_arrow(c, x + w * 0.6, y + h * 0.42, x + w * 0.76, level + h * 0.2, 5)
    c.setStrokeColor(PALETTE["orange"])
    draw_arrow(c, x + w * 0.76, level + h * 0.2, x + w * 0.86, level, 5)
    c.setStrokeColor(PALETTE["green"])
    draw_arrow(c, x + w * 0.86, level, x + w * 0.96, level + h * 0.25, 5)
    c.setLineWidth(1)


def draw_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    bullets: list[str],
    diagram,
) -> None:
    c.setFillColor(PALETTE["light"])
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setStrokeColor(PALETTE["border"])
    c.roundRect(x, y, w, h, 8, fill=0, stroke=1)
    c.setFillColor(PALETTE["navy"])
    c.setFont(FONT_BOLD, 12)
    c.drawString(x + 0.5 * cm, y + h - 0.7 * cm, title)
    c.setFillColor(colors.black)
    draw_bullets(c, x + 0.5 * cm, y + h - 1.4 * cm, bullets, size=9.2)
    if diagram:
        diagram(c, x + w - 6.4 * cm, y + 0.5 * cm, 5.5 * cm, h - 1.0 * cm)


def page_one(c: canvas.Canvas) -> None:
    draw_header(
        c,
        "Скальпинг по стакану на Binance Futures",
        "Памятка: фильтры, структура, сетапы, риск-менеджмент",
    )
    left_x = MARGIN
    right_x = PAGE_W / 2 + 0.3 * cm
    left_y = PAGE_H - 3.3 * cm

    left_y = draw_section_title(c, left_x, left_y, "1) Контекст рынка")
    left_y = draw_bullets(
        c,
        left_x,
        left_y,
        [
            "Ликвидные пары: BTC/ETH/SOL",
            "Ликвидные часы и плотный стакан",
            "Структура 1–5м: тренд/диапазон",
            "Ключевые уровни и стенки видны",
            "Перед новостями — вне рынка",
        ],
    )
    left_y -= 0.3 * cm
    left_y = draw_section_title(c, left_x, left_y, "2) Риск и лимиты")
    draw_bullets(
        c,
        left_x,
        left_y,
        [
            "Риск 0.25–0.5% на сделку",
            "Дневной лимит убытка 1–2%",
            "Стоп за уровнем, без усреднения",
            "Лимит сделок и пауза после серии",
        ],
    )

    right_y = PAGE_H - 3.3 * cm
    right_y = draw_section_title(c, right_x, right_y, "3) Стакан и лента")
    right_y = draw_bullets(
        c,
        right_x,
        right_y,
        [
            "Импульс подтвержден серией принтов",
            "Поглощение: объем есть, цена стоит",
            "Дельта затухает — фиксируемся",
            "Спред не расширяется",
        ],
    )
    right_y -= 0.2 * cm
    draw_orderbook_diagram(c, right_x, right_y - 6.4 * cm, 8.0 * cm, 6.0 * cm)
    draw_footer(c, "Не является финансовой рекомендацией. Используйте стопы.")


def page_two(c: canvas.Canvas) -> None:
    draw_header(
        c,
        "Слом структуры (BOS / CHoCH)",
        "Ключевая идея: пробой swing + удержание + ретест",
    )
    top_y = PAGE_H - 3.2 * cm
    card_w = PAGE_W - 2 * MARGIN
    card_h = 6.0 * cm
    gap = 0.6 * cm
    y1 = top_y - card_h
    y2 = y1 - gap - card_h

    draw_card(
        c,
        MARGIN,
        y1,
        card_w,
        card_h,
        "BOS: слом в сторону тренда",
        [
            "Тренд подтвержден (HH/HL или LL/LH)",
            "Пробой последнего swing и удержание",
            "Ретест уровня + реакция ленты",
            "Стоп за уровнем, цель — стенка",
        ],
        diagram_bos,
    )
    draw_card(
        c,
        MARGIN,
        y2,
        card_w,
        card_h,
        "CHoCH: смена характера",
        [
            "Первый пробой против тренда",
            "Закрепление выше/ниже ключевого swing",
            "Ретест уровня дает вход",
            "Риск выше — размер позиции меньше",
        ],
        diagram_choch,
    )

    flow_y = 1.6 * cm
    flow_h = 5.8 * cm
    c.setFillColor(PALETTE["light"])
    c.roundRect(MARGIN, flow_y, card_w, flow_h, 8, fill=1, stroke=0)
    c.setStrokeColor(PALETTE["border"])
    c.roundRect(MARGIN, flow_y, card_w, flow_h, 8, fill=0, stroke=1)
    c.setFillColor(PALETTE["navy"])
    c.setFont(FONT_BOLD, 12)
    c.drawString(MARGIN + 0.5 * cm, flow_y + flow_h - 0.7 * cm, "Алгоритм слома структуры")
    c.setFillColor(colors.black)
    left_list = [
        "1) Отметить 2–3 свинга на 1–5м",
        "2) Выделить ключевой swing",
        "3) Ждать пробой и реакцию ленты",
        "4) Вход по ретесту/подтверждению",
    ]
    right_list = [
        "5) Стоп за уровнем, не внутри",
        "6) Цель у ближайшей ликвидности",
        "7) Нет подтверждения — пропуск",
        "8) Не торговать перед новостями",
    ]
    draw_bullets(
        c,
        MARGIN + 0.5 * cm,
        flow_y + flow_h - 1.4 * cm,
        left_list,
    )
    draw_bullets(
        c,
        MARGIN + card_w / 2 + 0.2 * cm,
        flow_y + flow_h - 1.4 * cm,
        right_list,
    )
    draw_footer(c, "BOS/CHoCH работают только при ясной структуре.")


def page_three(c: canvas.Canvas) -> None:
    draw_header(
        c,
        "Сетапы 1–3: быстрые сценарии",
        "Фокус: уровень → реакция → короткая цель",
    )
    top_y = PAGE_H - 3.2 * cm
    card_w = PAGE_W - 2 * MARGIN
    card_h = 5.2 * cm
    gap = 0.5 * cm
    y1 = top_y - card_h
    y2 = y1 - gap - card_h
    y3 = y2 - gap - card_h

    draw_card(
        c,
        MARGIN,
        y1,
        card_w,
        card_h,
        "1) Снятие ликвидности → возврат (sweep/reclaim)",
        [
            "Уровень виден в стакане + стопы за ним",
            "Прокол и быстрый возврат внутрь",
            "Стоп: за экстремум прокола",
            "Цель: стенка или середина диапазона",
        ],
        diagram_sweep,
    )
    draw_card(
        c,
        MARGIN,
        y2,
        card_w,
        card_h,
        "2) Iceberg absorption → разворот",
        [
            "Много рыночных, цена не проходит",
            "Лента замедляется, появляется отскок",
            "Стоп: сразу за уровнем",
            "Цель: откат 1–2 зоны",
        ],
        diagram_absorption,
    )
    draw_card(
        c,
        MARGIN,
        y3,
        card_w,
        card_h,
        "3) Дисбаланс → micro-breakout",
        [
            "Дисбаланс bid/ask + тонкий стакан",
            "Ускорение принтов в сторону перекоса",
            "Стоп: 1–2 тика за стенкой",
            "Цель: первая крупная стенка",
        ],
        diagram_imbalance,
    )
    draw_footer(c, "Совет: входить только при подтверждении ленты.")


def page_four(c: canvas.Canvas) -> None:
    draw_header(
        c,
        "Сетапы 4–6 + чеклист сделки",
        "Цель: быстрый выход, дисциплина, повторяемость",
    )
    top_y = PAGE_H - 3.2 * cm
    card_w = PAGE_W - 2 * MARGIN
    card_h = 5.2 * cm
    gap = 0.5 * cm
    y1 = top_y - card_h
    y2 = y1 - gap - card_h
    y3 = y2 - gap - card_h

    draw_card(
        c,
        MARGIN,
        y1,
        card_w,
        card_h,
        "4) Momentum ignition (разгон)",
        [
            "Тонкий стакан, серия агрессивных",
            "Импульс подтверждается лентой",
            "Стоп: за старт импульса",
            "Цель: быстрый выход у стенок",
        ],
        diagram_ignition,
    )
    draw_card(
        c,
        MARGIN,
        y2,
        card_w,
        card_h,
        "5) Range ping-pong (скальп диапазона)",
        [
            "Четкий боковик, стенки сверху/снизу",
            "Подход к стенке + замедление",
            "Стоп: за стенкой",
            "Цель: центр или противоположная стенка",
        ],
        diagram_range,
    )
    draw_card(
        c,
        MARGIN,
        y3,
        card_w,
        card_h,
        "6) Exhaustion fade (выдох импульса)",
        [
            "Сильный импульс без продолжения",
            "Принты уменьшаются, цена не идет",
            "Стоп: за экстремум",
            "Цель: возврат к VWAP/середине",
        ],
        diagram_exhaustion,
    )

    checklist_y = 1.7 * cm
    checklist_h = 7.2 * cm
    c.setFillColor(PALETTE["light"])
    c.roundRect(MARGIN, checklist_y, card_w, checklist_h, 8, fill=1, stroke=0)
    c.setStrokeColor(PALETTE["border"])
    c.roundRect(MARGIN, checklist_y, card_w, checklist_h, 8, fill=0, stroke=1)
    c.setFillColor(PALETTE["navy"])
    c.setFont(FONT_BOLD, 12)
    c.drawString(MARGIN + 0.5 * cm, checklist_y + checklist_h - 0.7 * cm, "Чеклист сделки")
    c.setFillColor(colors.black)
    left_list = [
        "Контекст ясен: тренд/диапазон",
        "Есть видимый уровень или стенка",
        "Лента подтверждает вход",
        "Стоп и цель известны до входа",
    ]
    right_list = [
        "Размер позиции рассчитан по риску",
        "Нет новостей/ивентов в ближайшее время",
        "Сделка в пределах дневного лимита",
        "Выход частями при сильном импульсе",
    ]
    draw_bullets(
        c,
        MARGIN + 0.5 * cm,
        checklist_y + checklist_h - 1.4 * cm,
        left_list,
    )
    draw_bullets(
        c,
        MARGIN + card_w / 2 + 0.2 * cm,
        checklist_y + checklist_h - 1.4 * cm,
        right_list,
    )
    draw_footer(c, "Контроль риска важнее поиска идеального входа.")


def build_pdf(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    register_fonts()
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setAuthor("Binance Futures Scalping Cheatsheet")
    c.setTitle("Скальпинг по стакану — памятка")
    c.setSubject("Сетапы и фильтры для скальпинга на Binance Futures")

    page_one(c)
    c.showPage()
    page_two(c)
    c.showPage()
    page_three(c)
    c.showPage()
    page_four(c)
    c.showPage()
    c.save()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Binance scalping cheatsheet PDF.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent
        / "binance-futures-orderbook-scalping-cheatsheet.pdf",
        help="Output PDF path",
    )
    args = parser.parse_args()
    build_pdf(args.output)


if __name__ == "__main__":
    main()
