"""
Assemble a single poster-style PNG that mimics the live HTML dashboard layout:
header + KPI cards + all 7 charts. This is what gets embedded in README.md so
it renders natively on the GitHub repo page (GitHub renders images, not JS).
"""
import json
from PIL import Image, ImageDraw, ImageFont

with open('../dashboard_data.json') as f:
    DATA = json.load(f)
kpis = DATA['kpis']

W = 1600
PAD = 30
HEADER_H = 150
KPI_H = 130
CHART_ROW_H = 480
CHART_ROW2_H = 420
FOOTER_H = 50

H = HEADER_H + KPI_H + CHART_ROW_H + CHART_ROW2_H + CHART_ROW_H + FOOTER_H + PAD*6

canvas = Image.new('RGB', (W, H), '#f4f6f8')
draw = ImageDraw.Draw(canvas)

def font(size, bold=False):
    try:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

f_title = font(30, bold=True)
f_sub = font(15)
f_kpi_label = font(13, bold=True)
f_kpi_val = font(26, bold=True)
f_kpi_sub = font(12)
f_footer = font(12)

y = 0
# ---- Header ----
draw.rectangle([0, 0, W, HEADER_H], fill='#10263d')
draw.text((PAD, 30), "Toronto Weather Analytics — 2012", font=f_title, fill='white')
draw.text((PAD, 75), "Hourly climate dataset · 8,784 observations · Jan 1 - Dec 31, 2012 (leap year)", font=f_sub, fill='#c9d6e3')

# logo top-right
try:
    logo = Image.open('../assets/dabeltech_logo_cleaned.png').convert('RGBA')
    logo_h = 90
    logo_w = int(logo.width * (logo_h/logo.height))
    logo_resized = logo.resize((logo_w, logo_h))
    chip_pad = 10
    chip = Image.new('RGB', (logo_w + chip_pad*2, logo_h + chip_pad*2), 'white')
    chip.paste(logo_resized, (chip_pad, chip_pad), logo_resized)
    canvas.paste(chip, (W - chip.width - PAD, (HEADER_H - chip.height)//2))
except Exception as e:
    print("logo skip:", e)

y = HEADER_H + PAD

# ---- KPI cards ----
kpi_cards = [
    ("AVG TEMPERATURE", f"{kpis['avg_temp']}°C", f"Range: {kpis['min_temp']}°C to {kpis['max_temp']}°C", '#2f7ed8'),
    ("MAX TEMPERATURE", f"{kpis['max_temp']}°C", kpis['max_temp_date'][:16], '#f2994a'),
    ("MIN TEMPERATURE", f"{kpis['min_temp']}°C", kpis['min_temp_date'][:16], '#2f80c8'),
    ("AVG HUMIDITY", f"{kpis['avg_humidity']}%", "Annual average", '#2f7ed8'),
    ("AVG WIND SPEED", f"{kpis['avg_wind']} km/h", f"Peak gust: {kpis['max_wind']} km/h", '#9b59b6'),
    ("PRECIPITATION HOURS", f"{kpis['pct_precip_hours']}%", f"Clear: {kpis['pct_clear_hours']}% · Fog: {kpis['pct_fog_hours']}%", '#27ae60'),
]
n = len(kpi_cards)
gap = 16
card_w = (W - PAD*2 - gap*(n-1)) / n
for i, (label, val, sub, color) in enumerate(kpi_cards):
    x0 = PAD + i*(card_w+gap)
    x1 = x0 + card_w
    draw.rounded_rectangle([x0, y, x1, y+KPI_H], radius=10, fill='white', outline='#e6e9ec')
    draw.rectangle([x0, y, x0+4, y+KPI_H], fill=color)
    draw.text((x0+18, y+16), label, font=f_kpi_label, fill='#6b7785')
    draw.text((x0+18, y+40), val, font=f_kpi_val, fill='#1b2733')
    draw.text((x0+18, y+80), sub, font=f_kpi_sub, fill='#6b7785')

y += KPI_H + PAD

# ---- Chart row 1: monthly temp (wide) + condition (narrow) ----
def paste_chart(path, x, y, w, h):
    im = Image.open(path)
    ratio = min(w/im.width, h/im.height)
    new_size = (int(im.width*ratio), int(im.height*ratio))
    im = im.resize(new_size)
    card = Image.new('RGB', (w, h), 'white')
    ox, oy = (w-new_size[0])//2, (h-new_size[1])//2
    card.paste(im, (ox, oy))
    canvas.paste(card, (x, y))
    draw.rectangle([x, y, x+w, y+h], outline='#e6e9ec')

w1 = int((W - PAD*2 - gap) * 0.62)
w2 = (W - PAD*2 - gap) - w1
paste_chart('chart_monthly_temp.png', PAD, y, w1, CHART_ROW_H)
paste_chart('chart_condition.png', PAD + w1 + gap, y, w2, CHART_ROW_H)
y += CHART_ROW_H + PAD

# ---- Chart row 2: hourly, season precip, humidity/wind (thirds) ----
w3 = (W - PAD*2 - gap*2) // 3
paste_chart('chart_hourly.png', PAD, y, w3, CHART_ROW2_H)
paste_chart('chart_season_precip.png', PAD + w3 + gap, y, w3, CHART_ROW2_H)
paste_chart('chart_humidity_wind.png', PAD + 2*(w3+gap), y, W - PAD - (PAD + 2*(w3+gap)), CHART_ROW2_H)
y += CHART_ROW2_H + PAD

# ---- Chart row 3: daily range (wide) + correlation (narrow) ----
paste_chart('chart_daily_range.png', PAD, y, w1, CHART_ROW_H)
paste_chart('chart_correlation.png', PAD + w1 + gap, y, w2, CHART_ROW_H)
y += CHART_ROW_H + PAD

# ---- Footer ----
draw.text((PAD, y+10), "Source: Environment Canada hourly climate station data (2012)  ·  dabelinfotech / toronto-weather-dashboard", font=f_footer, fill='#6b7785')

canvas.save('dashboard_snapshot.png', optimize=True)
print("Poster saved:", canvas.size)
