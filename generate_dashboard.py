"""
generate_dashboard.py
----------------------
Builds a self-contained, interactive HTML dashboard from the aggregated
weather data produced by weather_analysis.py.

Usage:
    python weather_analysis.py --input Weather_Data.csv --output dashboard_data.json
    python generate_dashboard.py --input dashboard_data.json --output weather_dashboard.html
"""

import argparse
import base64
import json

# --------------------------------------------------------------------------- #
# HTML / CSS / JS TEMPLATE
# The `__DATA_JSON__` placeholder is replaced with the real aggregated data
# at build time. Chart.js is loaded from CDN; everything else is self
# contained so the resulting file works fully offline once generated.
# --------------------------------------------------------------------------- #
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toronto Weather Analytics — 2012</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" integrity="sha384-jb8JQMbMoBUzgWatfe6COACi2ljcDdZQ2OxczGA3bGNeWe+6DChMTBJemed7ZnvJ" crossorigin="anonymous"></script>
<style>
:root{
  --bg-page:#f4f6f8;
  --bg-card:#ffffff;
  --bg-header:#10263d;
  --accent:#2f7ed8;
  --accent2:#f2994a;
  --accent3:#27ae60;
  --accent4:#9b59b6;
  --text-primary:#1b2733;
  --text-secondary:#6b7785;
  --text-on-dark:#ffffff;
  --positive:#27ae60;
  --negative:#e0524d;
  --radius:12px;
  --gap:18px;
  --border:#e6e9ec;
}
*{box-sizing:border-box;}
body{
  margin:0;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:var(--bg-page);
  color:var(--text-primary);
}
.dashboard-container{max-width:1320px;margin:0 auto;padding:20px;}
.dashboard-header{
  background:linear-gradient(135deg,var(--bg-header),#1c3d5e);
  color:var(--text-on-dark);
  padding:22px 28px;
  border-radius:var(--radius);
  margin-bottom:var(--gap);
  display:flex;
  justify-content:space-between;
  align-items:center;
  flex-wrap:wrap;
  gap:12px;
}
.dashboard-header h1{font-size:21px;font-weight:700;margin:0 0 4px 0;}
.dashboard-header p{margin:0;font-size:13px;color:rgba(255,255,255,0.75);}
.header-right{display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
.header-logo{background:#fff;border-radius:8px;padding:5px 12px;display:flex;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,0.25);}
.header-logo img{height:50px;width:auto;display:block;}
.filters{display:flex;gap:12px;align-items:center;flex-wrap:wrap;}
.filter-group{display:flex;align-items:center;gap:6px;}
.filter-group label{font-size:12px;color:rgba(255,255,255,0.75);}
.filter-group select{
  padding:7px 10px;border:1px solid rgba(255,255,255,0.25);border-radius:6px;
  background:rgba(255,255,255,0.12);color:#fff;font-size:13px;
}
.filter-group select option{background:#1c3d5e;color:#fff;}

.kpi-row{display:grid;grid-template-columns:repeat(6,1fr);gap:var(--gap);margin-bottom:var(--gap);}
.kpi-card{
  background:var(--bg-card);border-radius:var(--radius);padding:16px 18px;
  box-shadow:0 1px 3px rgba(0,0,0,0.08);border-left:4px solid var(--accent);
}
.kpi-card.warm{border-left-color:var(--accent2);}
.kpi-card.cold{border-left-color:#2f80c8;}
.kpi-card.wet{border-left-color:var(--accent3);}
.kpi-card.wind{border-left-color:var(--accent4);}
.kpi-label{font-size:11.5px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;}
.kpi-value{font-size:24px;font-weight:700;line-height:1.1;}
.kpi-sub{font-size:12px;color:var(--text-secondary);margin-top:4px;}

.chart-row{display:grid;grid-template-columns:2fr 1fr;gap:var(--gap);margin-bottom:var(--gap);}
.chart-row.thirds{grid-template-columns:1fr 1fr 1fr;}
.chart-row.halves{grid-template-columns:1fr 1fr;}
.chart-container{
  background:var(--bg-card);border-radius:var(--radius);padding:18px 20px;
  box-shadow:0 1px 3px rgba(0,0,0,0.08);
}
.chart-container h3{font-size:14px;font-weight:600;margin:0 0 4px 0;color:var(--text-primary);}
.chart-container .subtitle{font-size:12px;color:var(--text-secondary);margin:0 0 14px 0;}
.chart-container canvas{max-height:280px;}

.table-section{
  background:var(--bg-card);border-radius:var(--radius);padding:18px 20px;
  box-shadow:0 1px 3px rgba(0,0,0,0.08);overflow-x:auto;margin-bottom:var(--gap);
}
.table-section h3{font-size:14px;font-weight:600;margin:0 0 12px 0;}
.data-table{width:100%;border-collapse:collapse;font-size:13px;}
.data-table thead th{
  text-align:left;padding:9px 10px;border-bottom:2px solid var(--border);
  color:var(--text-secondary);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px;
  cursor:pointer;user-select:none;white-space:nowrap;
}
.data-table thead th:hover{color:var(--text-primary);background:#f8f9fa;}
.data-table tbody td{padding:8px 10px;border-bottom:1px solid #f0f0f0;}
.data-table tbody tr:hover{background:#f8f9fa;}
.badge{padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge.hot{background:#fdecea;color:#c0392b;}
.badge.cold{background:#eaf2fb;color:#2266aa;}
.badge.wind{background:#f3ecfa;color:#8e44ad;}

.summary-section{
  background:var(--bg-card);border-radius:var(--radius);padding:22px 26px;
  box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:var(--gap);line-height:1.65;font-size:14px;
}
.summary-section h3{font-size:15px;margin:0 0 12px 0;}
.summary-section ul{margin:8px 0 0 0;padding-left:20px;}
.summary-section li{margin-bottom:6px;}

.dashboard-footer{
  text-align:center;color:var(--text-secondary);font-size:12px;padding:10px 0 4px;
}

@media (max-width:1100px){
  .kpi-row{grid-template-columns:repeat(3,1fr);}
  .chart-row,.chart-row.thirds,.chart-row.halves{grid-template-columns:1fr;}
}
</style>
</head>
<body>
<div class="dashboard-container">

  <header class="dashboard-header">
    <div class="header-title">
      <h1>Toronto Weather Analytics — 2012</h1>
      <p>Hourly climate dataset · 8,784 observations · Jan 1 - Dec 31, 2012 (leap year)</p>
    </div>
    <div class="header-right">
      <div class="filters">
        <div class="filter-group">
          <label>Season</label>
          <select id="seasonFilter">
            <option value="all">All Year</option>
            <option value="Winter">Winter</option>
            <option value="Spring">Spring</option>
            <option value="Summer">Summer</option>
            <option value="Fall">Fall</option>
          </select>
        </div>
      </div>
      <div class="header-logo">
        <img src="__LOGO_BASE64__" alt="Dabel Tech logo">
      </div>
    </div>
  </header>

  <section class="kpi-row" id="kpiRow"></section>

  <section class="chart-row">
    <div class="chart-container">
      <h3>Monthly Temperature Trend</h3>
      <p class="subtitle">Average / max / min °C by month — shows strong seasonal cycle</p>
      <canvas id="monthlyTempChart"></canvas>
    </div>
    <div class="chart-container">
      <h3>Weather Condition Mix</h3>
      <p class="subtitle">Share of hours by primary condition</p>
      <canvas id="conditionChart"></canvas>
    </div>
  </section>

  <section class="chart-row thirds">
    <div class="chart-container">
      <h3>Diurnal Temperature Pattern</h3>
      <p class="subtitle">Avg temp by hour of day</p>
      <canvas id="hourlyChart"></canvas>
    </div>
    <div class="chart-container">
      <h3>Precipitation Hours by Season</h3>
      <p class="subtitle">Count of hours with rain/snow/drizzle/etc.</p>
      <canvas id="seasonPrecipChart"></canvas>
    </div>
    <div class="chart-container">
      <h3>Humidity vs Wind Speed</h3>
      <p class="subtitle">Monthly averages</p>
      <canvas id="humidityWindChart"></canvas>
    </div>
  </section>

  <section class="chart-row">
    <div class="chart-container">
      <h3>Daily Temperature Range (Full Year)</h3>
      <p class="subtitle">Daily min-max band with average line</p>
      <canvas id="dailyRangeChart"></canvas>
    </div>
    <div class="chart-container">
      <h3>Variable Correlations</h3>
      <p class="subtitle">Pearson r vs Temperature</p>
      <canvas id="corrChart"></canvas>
    </div>
  </section>

  <section class="table-section">
    <h3>Monthly Summary</h3>
    <table class="data-table" id="monthlyTable">
      <thead>
        <tr>
          <th data-key="MonthName">Month</th>
          <th data-key="avg_temp">Avg Temp (°C)</th>
          <th data-key="max_temp">Max Temp (°C)</th>
          <th data-key="min_temp">Min Temp (°C)</th>
          <th data-key="avg_humidity">Avg Humidity (%)</th>
          <th data-key="avg_wind">Avg Wind (km/h)</th>
          <th data-key="avg_pressure">Avg Pressure (kPa)</th>
          <th data-key="precip_hours">Precip Hours</th>
          <th data-key="clear_hours">Clear Hours</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </section>

  <section class="table-section">
    <h3>Notable Extreme Hours</h3>
    <table class="data-table" id="extremesTable">
      <thead><tr><th>Type</th><th>Date/Time</th><th>Value</th><th>Condition</th></tr></thead>
      <tbody></tbody>
    </table>
  </section>

  <section class="summary-section" id="summarySection"></section>

  <footer class="dashboard-footer">
    Source: Environment Canada hourly climate station data (2012). Dashboard generated with Python (pandas) + Chart.js.
  </footer>
</div>

<script>
const DATA = __DATA_JSON__;

const COLORS = {
  temp:'#e0524d', tempFill:'rgba(224,82,77,0.12)',
  max:'#f2994a', min:'#2f80c8',
  humidity:'#2f7ed8', wind:'#9b59b6', pressure:'#27ae60',
  precip:'#2f80c8', clear:'#f2c94c', fog:'#95a5a6'
};
const COND_COLORS = ['#f2c94c','#95a5a6','#7f8c8d','#f2994a','#2f7ed8','#2c3e50','#9b59b6','#27ae60','#bdbdbd'];

let charts = {};

function fmt(v, d=1){ return Number(v).toFixed(d); }

function renderKPIs(){
  const k = DATA.kpis;
  const cards = [
    {cls:'', label:'Avg Temperature', value:`${fmt(k.avg_temp)}°C`, sub:`Range: ${k.min_temp}°C to ${k.max_temp}°C`},
    {cls:'warm', label:'Max Temperature', value:`${fmt(k.max_temp,1)}°C`, sub:new Date(k.max_temp_date).toLocaleString()},
    {cls:'cold', label:'Min Temperature', value:`${fmt(k.min_temp,1)}°C`, sub:new Date(k.min_temp_date).toLocaleString()},
    {cls:'', label:'Avg Humidity', value:`${fmt(k.avg_humidity)}%`, sub:'Annual average'},
    {cls:'wind', label:'Avg Wind Speed', value:`${fmt(k.avg_wind)} km/h`, sub:`Peak gust: ${k.max_wind} km/h`},
    {cls:'wet', label:'Precipitation Hours', value:`${fmt(k.pct_precip_hours)}%`, sub:`Clear: ${fmt(k.pct_clear_hours)}% · Fog: ${fmt(k.pct_fog_hours)}%`},
  ];
  document.getElementById('kpiRow').innerHTML = cards.map(c => `
    <div class="kpi-card ${c.cls}">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      <div class="kpi-sub">${c.sub}</div>
    </div>`).join('');
}

function filterBySeason(season){
  if(season === 'all') return DATA;
  const monthsBySeason = { Winter:[12,1,2], Spring:[3,4,5], Summer:[6,7,8], Fall:[9,10,11] };
  const months = monthsBySeason[season];
  return { ...DATA, monthly: DATA.monthly.filter(m => months.includes(m.Month)), daily: DATA.daily };
}

function destroyCharts(){
  Object.values(charts).forEach(c => c && c.destroy());
  charts = {};
}

function renderMonthlyTempChart(monthly){
  const ctx = document.getElementById('monthlyTempChart').getContext('2d');
  charts.monthlyTemp = new Chart(ctx, {
    type:'line',
    data:{
      labels: monthly.map(m=>m.MonthName),
      datasets:[
        {label:'Max Temp', data:monthly.map(m=>m.max_temp), borderColor:COLORS.max, backgroundColor:'transparent', borderWidth:1.5, borderDash:[4,3], pointRadius:2, tension:0.3},
        {label:'Avg Temp', data:monthly.map(m=>m.avg_temp), borderColor:COLORS.temp, backgroundColor:COLORS.tempFill, borderWidth:3, fill:true, pointRadius:3, tension:0.3},
        {label:'Min Temp', data:monthly.map(m=>m.min_temp), borderColor:COLORS.min, backgroundColor:'transparent', borderWidth:1.5, borderDash:[4,3], pointRadius:2, tension:0.3},
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:true,
      plugins:{legend:{position:'bottom', labels:{boxWidth:12,font:{size:11}}}},
      scales:{ y:{title:{display:true,text:'°C'}, grid:{color:'#f0f0f0'}}, x:{grid:{display:false}} }
    }
  });
}

function renderConditionChart(){
  const dist = DATA.condition_distribution;
  const labels = Object.keys(dist);
  const values = Object.values(dist);
  const ctx = document.getElementById('conditionChart').getContext('2d');
  charts.condition = new Chart(ctx, {
    type:'doughnut',
    data:{ labels, datasets:[{ data: values, backgroundColor: COND_COLORS, borderWidth:1, borderColor:'#fff' }]},
    options:{
      responsive:true, maintainAspectRatio:true, cutout:'55%',
      plugins:{ legend:{ position:'bottom', labels:{boxWidth:10,font:{size:10.5}} } }
    }
  });
}

function renderHourlyChart(){
  const h = DATA.hourly;
  const ctx = document.getElementById('hourlyChart').getContext('2d');
  charts.hourly = new Chart(ctx, {
    type:'line',
    data:{
      labels: h.map(x=>x.Hour+':00'),
      datasets:[{ label:'Avg Temp °C', data:h.map(x=>x.avg_temp), borderColor:COLORS.temp, backgroundColor:COLORS.tempFill, fill:true, tension:0.35, pointRadius:0, borderWidth:2 }]
    },
    options:{
      responsive:true, maintainAspectRatio:true,
      plugins:{legend:{display:false}},
      scales:{ y:{title:{display:true,text:'°C'}, grid:{color:'#f0f0f0'}}, x:{ticks:{maxTicksLimit:8}, grid:{display:false}} }
    }
  });
}

function renderSeasonPrecipChart(){
  const s = DATA.seasonal;
  const ctx = document.getElementById('seasonPrecipChart').getContext('2d');
  charts.seasonPrecip = new Chart(ctx, {
    type:'bar',
    data:{
      labels: s.map(x=>x.Season),
      datasets:[{ label:'Precip Hours', data:s.map(x=>x.precip_hours), backgroundColor:COLORS.precip, borderRadius:4 }]
    },
    options:{
      responsive:true, maintainAspectRatio:true,
      plugins:{legend:{display:false}},
      scales:{ y:{title:{display:true,text:'Hours'}, grid:{color:'#f0f0f0'}}, x:{grid:{display:false}} }
    }
  });
}

function renderHumidityWindChart(monthly){
  const ctx = document.getElementById('humidityWindChart').getContext('2d');
  charts.humidityWind = new Chart(ctx, {
    data:{
      labels: monthly.map(m=>m.MonthName),
      datasets:[
        { type:'bar', label:'Avg Humidity %', data: monthly.map(m=>m.avg_humidity), backgroundColor:'rgba(47,126,216,0.55)', borderRadius:4, yAxisID:'y' },
        { type:'line', label:'Avg Wind km/h', data: monthly.map(m=>m.avg_wind), borderColor:COLORS.wind, backgroundColor:COLORS.wind, borderWidth:2.5, tension:0.3, pointRadius:3, yAxisID:'y1' },
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:true,
      plugins:{legend:{position:'bottom', labels:{boxWidth:12,font:{size:11}}}},
      scales:{
        y:{ position:'left', title:{display:true,text:'Humidity %'}, grid:{color:'#f0f0f0'} },
        y1:{ position:'right', title:{display:true,text:'Wind km/h'}, grid:{display:false} },
        x:{ grid:{display:false} }
      }
    }
  });
}

function renderDailyRangeChart(){
  const d = DATA.daily;
  const ctx = document.getElementById('dailyRangeChart').getContext('2d');
  charts.dailyRange = new Chart(ctx, {
    type:'line',
    data:{
      labels: d.map(x=>x.Date),
      datasets:[
        { label:'Daily Max', data:d.map(x=>x.max_temp), borderColor:'rgba(242,153,74,0.5)', backgroundColor:'rgba(242,153,74,0.08)', pointRadius:0, borderWidth:1, fill:'+1', tension:0.2 },
        { label:'Daily Min', data:d.map(x=>x.min_temp), borderColor:'rgba(47,128,200,0.5)', backgroundColor:'rgba(47,128,200,0.08)', pointRadius:0, borderWidth:1, fill:false, tension:0.2 },
        { label:'Daily Avg', data:d.map(x=>x.avg_temp), borderColor:COLORS.temp, pointRadius:0, borderWidth:1.5, tension:0.2 },
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:true, animation:false,
      plugins:{legend:{position:'bottom', labels:{boxWidth:12,font:{size:11}}}},
      scales:{
        y:{title:{display:true,text:'°C'}, grid:{color:'#f0f0f0'}},
        x:{ ticks:{ maxTicksLimit:12, callback:function(val,idx){ const lbl=this.getLabelForValue(val); return lbl.slice(5); } }, grid:{display:false} }
      }
    }
  });
}

function renderCorrChart(){
  const c = DATA.correlation.Temp_C;
  const labels = Object.keys(c).filter(k=>k!=='Temp_C');
  const values = labels.map(k=>c[k]);
  const ctx = document.getElementById('corrChart').getContext('2d');
  charts.corr = new Chart(ctx, {
    type:'bar',
    data:{
      labels: labels,
      datasets:[{
        label:'Correlation with Temp',
        data: values,
        backgroundColor: values.map(v => v >= 0 ? 'rgba(39,174,96,0.75)' : 'rgba(224,82,77,0.75)'),
        borderRadius:4
      }]
    },
    options:{
      indexAxis:'y',
      responsive:true, maintainAspectRatio:true,
      plugins:{legend:{display:false}},
      scales:{ x:{min:-1,max:1, grid:{color:'#f0f0f0'}}, y:{grid:{display:false}} }
    }
  });
}

function renderMonthlyTable(monthly){
  const tbody = document.querySelector('#monthlyTable tbody');
  tbody.innerHTML = monthly.map(m => `
    <tr>
      <td>${m.MonthName}</td>
      <td>${fmt(m.avg_temp)}</td>
      <td>${fmt(m.max_temp)}</td>
      <td>${fmt(m.min_temp)}</td>
      <td>${fmt(m.avg_humidity)}</td>
      <td>${fmt(m.avg_wind)}</td>
      <td>${fmt(m.avg_pressure,2)}</td>
      <td>${m.precip_hours}</td>
      <td>${m.clear_hours}</td>
    </tr>`).join('');
}

let sortState = {key:null, asc:true};
document.querySelectorAll('#monthlyTable thead th').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.key;
    sortState.asc = sortState.key === key ? !sortState.asc : true;
    sortState.key = key;
    const sorted = [...currentMonthly].sort((a,b) => {
      const av=a[key], bv=b[key];
      if(typeof av === 'string') return sortState.asc ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortState.asc ? av-bv : bv-av;
    });
    renderMonthlyTable(sorted);
  });
});

function renderExtremesTable(){
  const rows = [];
  const hottest = [...DATA.daily].sort((a,b)=>b.max_temp-a.max_temp).slice(0,3);
  const coldest = [...DATA.daily].sort((a,b)=>a.min_temp-b.min_temp).slice(0,3);
  hottest.forEach(d => rows.push({type:'Hottest Day', badge:'hot', dt:d.Date, val:`${d.max_temp}°C`}));
  coldest.forEach(d => rows.push({type:'Coldest Day', badge:'cold', dt:d.Date, val:`${d.min_temp}°C`}));
  const k = DATA.kpis;
  rows.push({type:'Peak Wind Gust', badge:'wind', dt:'Full Year', val:`${k.max_wind} km/h`});
  const tbody = document.querySelector('#extremesTable tbody');
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><span class="badge ${r.badge}">${r.type}</span></td>
      <td>${r.dt}</td>
      <td>${r.val}</td>
      <td>—</td>
    </tr>`).join('');
}

let currentMonthly = DATA.monthly;

function renderSummary(){
  const k = DATA.kpis;
  document.getElementById('summarySection').innerHTML = `
    <h3>Analysis Summary</h3>
    <p>The 2012 hourly weather record for this station (8,784 observations, complete with no gaps or missing values) shows a
    classic humid continental climate profile consistent with Toronto, Ontario.</p>
    <ul>
      <li><b>Strong seasonality:</b> average temperature swings from about <b>-7.4°C in January</b> to roughly <b>21-22°C in summer</b>,
      an annual range of <b>${fmt(k.annual_temp_range)}°C</b> between the single hottest (${fmt(k.max_temp)}°C, June) and coldest (${fmt(k.min_temp)}°C, January) hours recorded.</li>
      <li><b>Predominantly dry/clear conditions:</b> roughly <b>${fmt(k.pct_clear_hours)}%</b> of all hours were clear or mainly clear, while only
      <b>${fmt(k.pct_precip_hours)}%</b> had active precipitation (rain, snow, drizzle, or freezing variants) and <b>${fmt(k.pct_fog_hours)}%</b> had fog/haze.</li>
      <li><b>Winter is the wettest/foggiest season</b> by hour-count (highest precipitation hours), while summer is driest despite being warmest —
      typical of a continental pattern where winter precipitation is more persistent (snow) even if less intense.</li>
      <li><b>Humidity and wind are inversely related to visibility:</b> humidity correlates at r ≈ -0.63 with visibility, and pressure drops are associated
      with higher wind speeds (r ≈ -0.36) — both physically expected relationships that validate data integrity.</li>
      <li><b>Dew point tracks temperature almost perfectly</b> (r ≈ 0.93), as expected physically, while pressure and temperature show a mild negative relationship,
      reflecting more low-pressure (stormy) systems arriving in cooler months.</li>
      <li><b>Diurnal cycle:</b> temperatures trough in the early morning (~5-6 AM) and peak in mid-afternoon (~3-4 PM), a normal solar heating pattern.</li>
    </ul>
    <p style="margin-top:12px;"><b>Data quality:</b> the dataset was already clean — zero nulls, zero duplicate timestamps, complete hourly coverage across the full
    leap year, and no out-of-range values (humidity 0-100%, non-negative wind/visibility). Cleaning consisted of standardizing column names, parsing the datetime field,
    and deriving categorical/time features (season, hour, primary weather condition, precipitation/fog flags) to support this analysis.</p>
  `;
}

function renderAll(season){
  const filtered = filterBySeason(season);
  currentMonthly = filtered.monthly;
  destroyCharts();
  renderKPIs();
  renderMonthlyTempChart(filtered.monthly);
  renderConditionChart();
  renderHourlyChart();
  renderSeasonPrecipChart();
  renderHumidityWindChart(filtered.monthly);
  renderDailyRangeChart();
  renderCorrChart();
  renderMonthlyTable(filtered.monthly);
  renderExtremesTable();
  renderSummary();
}

document.getElementById('seasonFilter').addEventListener('change', (e) => {
  renderAll(e.target.value);
});

renderAll('all');
</script>
</body>
</html>
"""


def _load_logo_data_uri(logo_path: str | None) -> str:
    """Read a logo image file and return a base64 data: URI for embedding.
    Returns an empty string (hides the logo) if no path is given or the file
    is missing, so the dashboard still builds without a logo."""
    if not logo_path:
        return ""
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = logo_path.rsplit(".", 1)[-1].lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "svg": "image/svg+xml"}.get(ext, "image/png")
        return f"data:{mime};base64,{b64}"
    except FileNotFoundError:
        return ""


def build_html(data: dict, logo_path: str | None = None) -> str:
    """Inject the aggregated data JSON (and optional logo) into the template."""
    json_str = json.dumps(data)
    html = TEMPLATE.replace("__DATA_JSON__", json_str)
    logo_uri = _load_logo_data_uri(logo_path)
    html = html.replace("__LOGO_BASE64__", logo_uri)
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate the weather dashboard HTML file.")
    parser.add_argument("--input", default="dashboard_data.json", help="Path to aggregated JSON (from weather_analysis.py)")
    parser.add_argument("--output", default="weather_dashboard.html", help="Path to write the final HTML dashboard")
    parser.add_argument("--logo", default=None, help="Path to a logo image (PNG/JPG/SVG) to embed top-right in the header")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    html = build_html(data, logo_path=args.logo)

    with open(args.output, "w") as f:
        f.write(html)

    print(f"Dashboard written to {args.output} ({len(html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
