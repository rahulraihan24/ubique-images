#!/usr/bin/env python3
"""Render UBIQUE Facebook post images (1080x1080 JPG) from a JSON spec.

Usage: python3 render.py spec.json out.jpg

spec fields:
  template : navy | notebook | sunset | chalk | clean | split | mint
  kind     : quiz | tip | answer
  tag      : small label, e.g. "ক্লাস ৮ · শতকরা"
  title    : main question / heading
  options  : list of 4 strings (quiz only)
  body     : list of short lines (tip / answer)
  footer   : bottom-left line, e.g. "উত্তর কমেন্টে লেখো 👇"
"""
import json, os, sys, urllib.request, zipfile, io, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / "fonts"
FONT_ZIP = "https://github.com/notofonts/bengali/releases/download/NotoSansBengali-v2.003/NotoSansBengali-v2.003.zip"


def ensure_fonts():
    reg, bold = FONT_DIR / "NotoSansBengali-Regular.ttf", FONT_DIR / "NotoSansBengali-Bold.ttf"
    if reg.exists() and bold.exists():
        return reg, bold
    FONT_DIR.mkdir(exist_ok=True)
    data = urllib.request.urlopen(FONT_ZIP, timeout=60).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for n in z.namelist():
            if n.endswith("full/ttf/NotoSansBengali-Regular.ttf"):
                reg.write_bytes(z.read(n))
            if n.endswith("full/ttf/NotoSansBengali-Bold.ttf"):
                bold.write_bytes(z.read(n))
    return reg, bold


THEMES = {
    "navy":     dict(bg="#0f2a4a", fg="#ffffff", accent="#f5b700", accentFg="#0f2a4a", card="#1c4170", cardBorder="#2d5a92", muted="#c8d6ea"),
    "notebook": dict(bg="#fbf7ec", fg="#1d2a44", accent="#d94a3d", accentFg="#ffffff", card="#ffffff", cardBorder="#c9d6ee", muted="#5b6680"),
    "sunset":   dict(bg="linear-gradient(140deg,#ff8a3d 0%,#f2436f 100%)", fg="#ffffff", accent="#ffffff", accentFg="#e8435f", card="rgba(255,255,255,.18)", cardBorder="rgba(255,255,255,.45)", muted="#ffe6dc"),
    "chalk":    dict(bg="#1f3b2d", fg="#f4f1e6", accent="#ffd75e", accentFg="#1f3b2d", card="rgba(255,255,255,.06)", cardBorder="rgba(244,241,230,.55)", muted="#cfd8cc"),
    "clean":    dict(bg="#ffffff", fg="#14213d", accent="#2f6fed", accentFg="#ffffff", card="#f2f5fb", cardBorder="#f2f5fb", muted="#6b7690"),
    "split":    dict(bg="#ffffff", fg="#1b1b2f", accent="#6c3ce9", accentFg="#ffffff", card="#f4f0ff", cardBorder="#e2d8ff", muted="#6f6a85"),
    "mint":     dict(bg="#e7f7f1", fg="#0f3b33", accent="#0f8a6c", accentFg="#ffffff", card="#ffffff", cardBorder="#bfe6d8", muted="#4c6f66"),
}

LETTERS = ["ক", "খ", "গ", "ঘ"]


def build_html(spec, reg, bold):
    t = THEMES.get(spec.get("template", "navy"), THEMES["navy"])
    e = lambda s: html.escape(str(s))
    kind = spec.get("kind", "quiz")
    title = e(spec.get("title", ""))
    tlen = len(spec.get("title", ""))
    tsize = 64 if tlen < 60 else 56 if tlen < 90 else 48 if tlen < 130 else 42

    content = ""
    if kind == "quiz":
        opts = spec.get("options", [])
        longest = max((len(o) for o in opts), default=0)
        cols = "1fr 1fr" if longest <= 14 else "1fr"
        osize = 46 if longest <= 14 else 40
        content = f'<div class="o" style="grid-template-columns:{cols}">' + "".join(
            f'<div style="font-size:{osize}px"><b>{LETTERS[i]}</b>{e(o)}</div>' for i, o in enumerate(opts)) + "</div>"
    else:
        lines = spec.get("body", [])
        bsize = 44 if sum(len(l) for l in lines) < 160 else 38
        content = '<div class="body">' + "".join(f'<p style="font-size:{bsize}px">{e(l)}</p>' for l in lines) + "</div>"

    deco = ""
    tpl = spec.get("template", "navy")
    if tpl == "notebook":
        deco = '<div class="lines"></div><div class="margin"></div>'
    elif tpl == "chalk":
        deco = '<div class="frame"></div>'
    elif tpl == "split":
        deco = '<div class="band"></div>'
    elif tpl == "clean":
        deco = '<div class="dot d1"></div><div class="dot d2"></div>'
    elif tpl in ("sunset", "mint", "navy"):
        deco = '<div class="ring"></div>'

    pad_left = 170 if tpl == "split" else 150 if tpl == "notebook" else 80

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:B;src:url('file://{reg}');}}
@font-face{{font-family:B;font-weight:700;src:url('file://{bold}');}}
*{{box-sizing:border-box}}
body{{margin:0;width:1080px;height:1080px;font-family:B,sans-serif;background:{t['bg']};color:{t['fg']};overflow:hidden;position:relative}}
.w{{position:relative;z-index:2;width:1080px;height:1080px;padding:80px 80px 70px {pad_left}px;display:flex;flex-direction:column}}
.tag{{display:inline-block;background:{t['accent']};color:{t['accentFg']};font-weight:700;font-size:32px;padding:10px 28px;border-radius:40px;align-self:flex-start}}
h1{{font-size:{tsize}px;line-height:1.45;margin:0 0 44px;font-weight:700}}
.o{{display:grid;gap:24px}}
.o div{{background:{t['card']};border:3px solid {t['cardBorder']};border-radius:22px;padding:22px 32px;line-height:1.4}}
.o b{{color:{t['accent'] if tpl not in ('sunset',) else '#fff3c4'};margin-right:16px}}
.body p{{margin:0 0 18px;line-height:1.5;padding-left:28px;border-left:6px solid {t['accent']}}}
.mid{{flex:1;display:flex;flex-direction:column;justify-content:center;padding:30px 0}}
.f{{display:flex;justify-content:space-between;align-items:center;font-size:31px;color:{t['muted']}}}
.f span{{font-weight:700;color:{t['fg']};font-size:40px;letter-spacing:3px}}
.lines{{position:absolute;inset:0;background:repeating-linear-gradient(#fbf7ec 0 62px,#cfdcf2 62px 64px);z-index:0}}
.margin{{position:absolute;top:0;bottom:0;left:118px;width:4px;background:#e8857a;z-index:1}}
.frame{{position:absolute;inset:34px;border:6px solid #8a6a43;border-radius:10px;box-shadow:inset 0 0 0 4px #5d4630;z-index:1}}
.band{{position:absolute;top:0;bottom:0;left:0;width:110px;background:{t['accent']};z-index:1}}
.dot{{position:absolute;border-radius:50%;z-index:0}}
.d1{{width:420px;height:420px;right:-140px;top:-140px;background:#e7efff}}
.d2{{width:260px;height:260px;left:-90px;bottom:-90px;background:#fff1d6}}
.ring{{position:absolute;width:520px;height:520px;right:-200px;bottom:-200px;border-radius:50%;border:70px solid rgba(255,255,255,.07);z-index:0}}
</style></head><body>{deco}<div class="w">
<div class="tag">{e(spec.get('tag',''))}</div>
<div class="mid"><h1>{title}</h1>
{content}</div>
<div class="f"><div>{e(spec.get('footer',''))}</div><span>UBIQUE</span></div>
</div></body></html>"""


def render(spec, out):
    reg, bold = ensure_fonts()
    from playwright.sync_api import sync_playwright
    tmp = Path(out).with_suffix(".html")
    tmp.write_text(build_html(spec, reg, bold), encoding="utf-8")
    png = Path(out).with_suffix(".png")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1080})
        pg.goto(f"file://{tmp.resolve()}")
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(png))
        b.close()
    from PIL import Image
    Image.open(png).convert("RGB").save(out, quality=88, optimize=True)
    tmp.unlink(); png.unlink()


if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
    print("saved", sys.argv[2])
