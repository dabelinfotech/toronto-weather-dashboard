"""
Generate static matplotlib chart images from dashboard_data.json,
used to build both a poster-style PNG snapshot and a multi-page PDF report
of the Toronto Weather Dashboard (since GitHub can't render live JS charts).
"""
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.dpi': 150,
    'font.size': 10.5,
    'axes.titlesize': 12.5,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
})

TEMP = '#e0524d'
MAX_C = '#f2994a'
MIN_C = '#2f80c8'
HUM = '#2f7ed8'
WIND = '#9b59b6'
PRECIP = '#2f80c8'
POS = '#27ae60'
NEG = '#e0524d'
COND_COLORS = ['#f2c94c','#95a5a6','#7f8c8d','#f2994a','#2f7ed8','#2c3e50','#9b59b6','#27ae60','#bdbdbd']

with open('../dashboard_data.json') as f:
    DATA = json.load(f)

monthly = DATA['monthly']
hourly = DATA['hourly']
seasonal = DATA['seasonal']
daily = DATA['daily']
cond = DATA['condition_distribution']
corr = DATA['correlation']
kpis = DATA['kpis']

months = [m['MonthName'] for m in monthly]

# ---------- 1. Monthly temperature trend ----------
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(months, [m['max_temp'] for m in monthly], color=MAX_C, lw=1.5, ls='--', marker='o', ms=3, label='Max Temp')
ax.fill_between(months, [m['avg_temp'] for m in monthly], color=TEMP, alpha=0.12)
ax.plot(months, [m['avg_temp'] for m in monthly], color=TEMP, lw=3, marker='o', ms=4, label='Avg Temp')
ax.plot(months, [m['min_temp'] for m in monthly], color=MIN_C, lw=1.5, ls='--', marker='o', ms=3, label='Min Temp')
ax.set_title('Monthly Temperature Trend')
ax.set_ylabel('°C')
ax.legend(loc='upper center', ncol=3, frameon=False)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig('chart_monthly_temp.png', bbox_inches='tight')
plt.close()

# ---------- 2. Weather condition distribution ----------
fig, ax = plt.subplots(figsize=(5.2, 4.2))
labels = list(cond.keys())
values = list(cond.values())
wedges, _, autotexts = ax.pie(values, labels=None, autopct=lambda p: f'{p:.0f}%' if p > 3 else '',
                                colors=COND_COLORS[:len(values)], startangle=90,
                                wedgeprops=dict(width=0.42, edgecolor='white'))
ax.set_title('Weather Condition Mix')
ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=8.5)
plt.tight_layout()
plt.savefig('chart_condition.png', bbox_inches='tight')
plt.close()

# ---------- 3. Diurnal temperature pattern ----------
fig, ax = plt.subplots(figsize=(5.2, 4.0))
hrs = [h['Hour'] for h in hourly]
temps = [h['avg_temp'] for h in hourly]
ax.fill_between(hrs, temps, color=TEMP, alpha=0.15)
ax.plot(hrs, temps, color=TEMP, lw=2.2)
ax.set_title('Diurnal Temperature Pattern')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Avg Temp (°C)')
ax.set_xticks(range(0, 24, 4))
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig('chart_hourly.png', bbox_inches='tight')
plt.close()

# ---------- 4. Precipitation hours by season ----------
fig, ax = plt.subplots(figsize=(5.2, 4.0))
seasons = [s['Season'] for s in seasonal]
precip_hours = [s['precip_hours'] for s in seasonal]
bars = ax.bar(seasons, precip_hours, color=PRECIP, width=0.6)
for b in bars:
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+5, f'{int(b.get_height())}', ha='center', fontsize=9)
ax.set_title('Precipitation Hours by Season')
ax.set_ylabel('Hours')
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig('chart_season_precip.png', bbox_inches='tight')
plt.close()

# ---------- 5. Humidity vs wind (dual axis) ----------
fig, ax1 = plt.subplots(figsize=(8, 4.0))
ax2 = ax1.twinx()
ax1.bar(months, [m['avg_humidity'] for m in monthly], color=HUM, alpha=0.55, label='Avg Humidity %')
ax2.plot(months, [m['avg_wind'] for m in monthly], color=WIND, lw=2.5, marker='o', ms=4, label='Avg Wind km/h')
ax1.set_title('Humidity vs Wind Speed (Monthly Avg)')
ax1.set_ylabel('Humidity %')
ax2.set_ylabel('Wind km/h')
ax1.spines[['top']].set_visible(False)
ax2.spines[['top']].set_visible(False)
fig.legend(loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.02), frameon=False)
plt.tight_layout()
plt.savefig('chart_humidity_wind.png', bbox_inches='tight')
plt.close()

# ---------- 6. Daily temperature range (full year) ----------
fig, ax = plt.subplots(figsize=(9.5, 4.0))
dates = list(range(len(daily)))
maxs = [d['max_temp'] for d in daily]
mins = [d['min_temp'] for d in daily]
avgs = [d['avg_temp'] for d in daily]
ax.fill_between(dates, mins, maxs, color='#bcd4e8', alpha=0.5, label='Daily min-max range')
ax.plot(dates, avgs, color=TEMP, lw=1.3, label='Daily avg')
month_starts = []
month_labels = []
prev_month = None
for i, d in enumerate(daily):
    m = d['Date'][5:7]
    if m != prev_month:
        month_starts.append(i)
        month_labels.append(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m)-1])
        prev_month = m
ax.set_xticks(month_starts)
ax.set_xticklabels(month_labels)
ax.set_title('Daily Temperature Range (Full Year 2012)')
ax.set_ylabel('°C')
ax.legend(loc='upper left', frameon=False)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig('chart_daily_range.png', bbox_inches='tight')
plt.close()

# ---------- 7. Correlation with temperature ----------
fig, ax = plt.subplots(figsize=(5.2, 4.0))
c = corr['Temp_C']
labels = [k for k in c.keys() if k != 'Temp_C']
values = [c[k] for k in labels]
colors = [POS if v >= 0 else NEG for v in values]
bars = ax.barh(labels, values, color=colors)
for b, v in zip(bars, values):
    ax.text(v + (0.03 if v>=0 else -0.03), b.get_y()+b.get_height()/2, f'{v:.2f}',
            va='center', ha='left' if v>=0 else 'right', fontsize=9)
ax.axvline(0, color='#333', lw=0.8)
ax.set_xlim(-1, 1)
ax.set_title('Correlation with Temperature')
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig('chart_correlation.png', bbox_inches='tight')
plt.close()

print("All 7 charts generated.")
