#!/usr/bin/env python3
"""Сборка выпуска «Курса живописи» в PDF.
Использование: python3 build_issue.py dayN.json out.pdf [папка_с_картинками]
Картинки берутся из папки (NNN.jpg) или скачиваются с сайта галереи."""
import json, os, sys, urllib.request, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak, KeepTogether, CondPageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PImage

SITE = "https://9251485302im-blip.github.io/gallery/img/"
F = {
    "serif": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "serif-i": "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    "serif-b": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
    "sans-b": "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf",
}
FALLBACK = {"serif": "DejaVuSerif.ttf", "serif-i": "DejaVuSerif-Italic.ttf", "serif-b": "DejaVuSerif-Bold.ttf",
            "sans": "DejaVuSans.ttf", "sans-b": "DejaVuSans-Bold.ttf"}
for k, p in F.items():
    if not os.path.exists(p):
        p = "/usr/share/fonts/truetype/dejavu/" + FALLBACK[k]
    pdfmetrics.registerFont(TTFont(k, p))

INK = colors.HexColor("#1f1b16"); DIM = colors.HexColor("#6f6658"); BRASS = colors.HexColor("#a8865a")
WASH = colors.HexColor("#f4efe6"); RULE = colors.HexColor("#d9cfbf")

S = {
 "kicker": ParagraphStyle("k", fontName="sans-b", fontSize=9, leading=12, textColor=BRASS, spaceAfter=4),
 "h1": ParagraphStyle("h1", fontName="serif-i", fontSize=30, leading=34, textColor=INK, spaceAfter=6),
 "meta": ParagraphStyle("m", fontName="sans", fontSize=10, leading=13, textColor=DIM),
 "intro": ParagraphStyle("i", fontName="serif", fontSize=12.5, leading=18, textColor=INK, alignment=TA_JUSTIFY),
 "num": ParagraphStyle("n", fontName="sans-b", fontSize=9, leading=12, textColor=BRASS),
 "author": ParagraphStyle("a", fontName="sans-b", fontSize=12, leading=15, textColor=INK),
 "title": ParagraphStyle("t", fontName="serif-i", fontSize=24, leading=28, textColor=INK, spaceBefore=2, spaceAfter=2),
 "cap": ParagraphStyle("c", fontName="sans", fontSize=9.5, leading=12.5, textColor=DIM),
 "sec": ParagraphStyle("s", fontName="sans-b", fontSize=9, leading=12, textColor=BRASS, spaceBefore=9, spaceAfter=2),
 "body": ParagraphStyle("b", fontName="serif", fontSize=11, leading=15.6, textColor=INK, alignment=TA_JUSTIFY),
 "look": ParagraphStyle("l", fontName="serif-i", fontSize=10.5, leading=14.5, textColor=INK),
 "q": ParagraphStyle("q", fontName="serif-i", fontSize=13, leading=18, textColor=INK, alignment=TA_CENTER),
 "src": ParagraphStyle("src", fontName="sans", fontSize=8.5, leading=11, textColor=DIM),
}

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get_img(code, imgdir):
    p = os.path.join(imgdir, code + ".jpg")
    if not os.path.exists(p):
        os.makedirs(imgdir, exist_ok=True)
        urllib.request.urlretrieve(SITE + code + ".jpg", p)
    return p

def build(data, out, imgdir):
    W, H = A4; M = 18 * mm
    def deco(c, doc):
        c.saveState()
        c.setFont("sans", 8); c.setFillColor(DIM)
        c.drawString(M, 11 * mm, "Курс живописи · День %d из %d" % (data["day"], data["total"]))
        c.drawRightString(W - M, 11 * mm, str(doc.page))
        c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, 14 * mm, W - M, 14 * mm)
        c.restoreState()
    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=16 * mm, bottomMargin=20 * mm,
                          title="Курс живописи · День %d — %s" % (data["day"], data["theme"]), author="")
    fr = Frame(M, 20 * mm, W - 2 * M, H - 36 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=deco)])
    cw = W - 2 * M
    d = datetime.date.fromisoformat(data["date"])
    months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
    st = []
    st.append(Paragraph("КУРС ЖИВОПИСИ · ДЕНЬ %d ИЗ %d" % (data["day"], data["total"]), S["kicker"]))
    st.append(Paragraph(esc(data["theme"]), S["h1"]))
    st.append(Paragraph("%d %s %d" % (d.day, months[d.month - 1], d.year) + " · три картины: " +
                        " · ".join(esc(p["author"].split()[-1] if p["author"].split()[-1] not in ("Старший","Младший") else p["author"].split()[-2]) for p in data["paintings"]), S["meta"]))
    st.append(Spacer(1, 10))
    st.append(Table([[""]], colWidths=[cw], rowHeights=[0.8], style=[("LINEABOVE", (0,0), (-1,-1), 0.8, BRASS)]))
    st.append(Spacer(1, 8))
    st.append(Paragraph(esc(data["intro"]), S["intro"]))
    # contents
    rows = []
    for i, p in enumerate(data["paintings"], 1):
        rows.append([Paragraph(str(i), S["num"]), Paragraph("<b>%s</b>, «%s», %s" % (esc(p["author"]), esc(p["title"]), esc(p["year"])), S["meta"])])
    st.append(Spacer(1, 10))
    st.append(Table(rows, colWidths=[8 * mm, cw - 8 * mm], style=[("VALIGN", (0,0), (-1,-1), "TOP"), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
    for i, p in enumerate(data["paintings"], 1):
        st.append(PageBreak())
        path = get_img(p["img"], imgdir)
        iw, ih = PImage.open(path).size
        maxw, maxh = cw, 118 * mm
        s = min(maxw / iw, maxh / ih)
        img = Image(path, width=iw * s, height=ih * s)
        frame = Table([[img]], colWidths=[cw], style=[("ALIGN", (0,0), (-1,-1), "CENTER"), ("BACKGROUND", (0,0), (-1,-1), WASH),
                                                     ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)])
        st.append(frame)
        st.append(Spacer(1, 8))
        st.append(Paragraph("КАРТИНА %d ИЗ %d" % (i, len(data["paintings"])), S["num"]))
        st.append(Paragraph("%s <font name='sans' size='10' color='#6f6658'>(%s)</font>" % (esc(p["author"]).upper(), esc(p["life"])), S["author"]))
        st.append(Paragraph("«%s»" % esc(p["title"]), S["title"]))
        st.append(Paragraph("%s · %s · %s" % (esc(p["year"]), esc(p["tech"]), esc(p["museum"])), S["cap"]))
        for head, text in p["sections"]:
            st.append(KeepTogether([Paragraph(esc(head).upper(), S["sec"]), Paragraph(esc(text), S["body"])]))
        if p.get("look"):
            st.append(Spacer(1, 8))
            st.append(Table([[Paragraph(esc(p["look"]), S["look"])]], colWidths=[cw],
                            style=[("BACKGROUND", (0,0), (-1,-1), WASH), ("LINEBEFORE", (0,0), (0,-1), 2, BRASS),
                                   ("LEFTPADDING", (0,0), (-1,-1), 10), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    st.append(CondPageBreak(60 * mm))
    st.append(Spacer(1, 16))
    if data.get("question"):
        st.append(Paragraph(esc(data["question"]), S["q"]))
        st.append(Spacer(1, 14))
    if data.get("sources"):
        st.append(Paragraph("ИСТОЧНИКИ", S["sec"]))
        for s_ in data["sources"]:
            st.append(Paragraph("— " + esc(s_), S["src"]))
    doc.build(st)

if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    build(data, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "/tmp/course_img")
    print("ok", sys.argv[2])
