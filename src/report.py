import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _fmt_money(val):
    return f"{int(val):,}".replace(",", " ") + " ₽"


def _pct(val):
    return f"{val:.1%}"


def generate_report(metrics, alerts, summary_text, campaign):
    critical_count = sum(1 for a in alerts if a["priority"] == "critical")
    warning_count = sum(1 for a in alerts if a["priority"] == "warning")

    chart_labels = [r["название_товара"] for r in metrics["chart_data"]]
    chart_revenue = [r["total_revenue"] for r in metrics["chart_data"]]
    chart_returns = [round(r["return_rate"] * 100, 1) for r in metrics["chart_data"]]
    chart_stock = [r["остаток"] for r in metrics["chart_data"]]

    trend_dates = metrics["revenue_trend"]["dates"]
    trend_values = metrics["revenue_trend"]["values"]

    cat_labels = list(metrics["category_revenue"].keys())
    cat_values = list(metrics["category_revenue"].values())

    reason_labels = list(metrics["return_reasons"].keys())
    reason_values = list(metrics["return_reasons"].values())

    top_product = metrics["top_products"][0] if metrics["top_products"] else {}

    alerts_html = ""
    for a in alerts:
        cls = {
            "critical": "alert-critical",
            "warning": "alert-warning",
            "info": "alert-info",
        }.get(a["priority"], "alert-info")
        alerts_html += f'<div class="alert-item {cls}"><span class="alert-icon">{a["icon"]}</span><div class="alert-content"><span class="alert-cat">{a["category"]}</span><p>{a["message"]}</p></div></div>\n'

    top_products_rows = ""
    for i, p in enumerate(metrics["top_products"]):
        medal = ["🥇", "🥈", "🥉", "4.", "5."][i]
        top_products_rows += (
            f'<tr><td>{medal}</td><td><strong>{p["название_товара"]}</strong><br>'
            f'<small>{p["sku"]}</small></td>'
            f'<td class="num">{_fmt_money(p["total_revenue"])}</td>'
            f'<td class="num">{int(p["total_sold"]):,}</td>'
            f'<td class="num {"rate-bad" if p["return_rate"] >= config.RETURN_RATE_WARNING else ""}">'
            f'{_pct(p["return_rate"])}</td></tr>\n'
        )

    problem_rows = ""
    problematic = sorted(
        metrics["df"].to_dict("records"),
        key=lambda x: (-(x["return_rate"] >= config.RETURN_RATE_WARNING), x["total_revenue"]),
    )
    for p in problematic:
        is_high_ret = p["return_rate"] >= config.RETURN_RATE_WARNING
        is_low_sales = p["total_revenue"] <= metrics["df"]["total_revenue"].quantile(config.LOW_SALES_PERCENTILE)
        is_low_stock = p["остаток"] < config.LOW_STOCK_THRESHOLD
        if not (is_high_ret or is_low_sales or is_low_stock):
            continue
        tags = ""
        if is_high_ret:
            tags += '<span class="tag tag-red">Высокий % возвратов</span>'
        if is_low_sales:
            tags += '<span class="tag tag-orange">Низкие продажи</span>'
        if is_low_stock:
            tags += '<span class="tag tag-yellow">Низкий остаток</span>'
        problem_rows += (
            f'<tr><td><strong>{p["название_товара"]}</strong><br>'
            f'<small>{p["sku"]}</small></td>'
            f'<td class="num">{_fmt_money(p["total_revenue"])}</td>'
            f'<td class="num {"rate-bad" if is_high_ret else ""}">{_pct(p["return_rate"])}</td>'
            f'<td class="num">{int(p["остаток"]):,}</td>'
            f'<td>{tags}</td></tr>\n'
        )

    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Аналитический отчёт — {metrics["period_start"]} — {metrics["period_end"]}</title>
<meta name="description" content="Автоматически сгенерированный операционный отчёт по продажам, возвратам и остаткам товаров.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0a0e1a;
    --surface: #111827;
    --surface2: #1a2236;
    --border: rgba(255,255,255,0.07);
    --accent: #6366f1;
    --accent2: #8b5cf6;
    --accent3: #06b6d4;
    --green: #10b981;
    --red: #ef4444;
    --orange: #f59e0b;
    --yellow: #eab308;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --radius: 16px;
    --radius-sm: 8px;
    --glow: 0 0 40px rgba(99,102,241,0.15);
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.6;
  }}

  /* --- header --- */
  .header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border-bottom: 1px solid var(--border);
    padding: 40px 0 32px;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 30% 50%, rgba(99,102,241,0.12) 0%, transparent 70%),
                radial-gradient(ellipse at 70% 50%, rgba(139,92,246,0.08) 0%, transparent 70%);
    pointer-events: none;
  }}
  .header-inner {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 32px;
    position: relative;
  }}
  .header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 100px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 500;
    color: #a5b4fc;
    margin-bottom: 16px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }}
  .header h1 {{
    font-size: clamp(24px, 4vw, 42px);
    font-weight: 800;
    background: linear-gradient(135deg, #fff 30%, #a5b4fc 70%, #c4b5fd 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 8px;
  }}
  .header-meta {{
    color: var(--text-muted);
    font-size: 14px;
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    margin-top: 16px;
  }}
  .header-meta span {{ display: flex; align-items: center; gap: 6px; }}

  /* --- layout --- */
  .container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 32px;
  }}
  .section {{ margin: 40px 0; }}
  .section-title {{
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  /* --- KPI cards --- */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-top: 32px;
  }}
  .kpi-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: var(--glow);
  }}
  .kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: var(--radius) var(--radius) 0 0;
  }}
  .kpi-card.accent::before {{ background: linear-gradient(90deg, var(--accent), var(--accent2)); }}
  .kpi-card.green::before {{ background: linear-gradient(90deg, var(--green), #34d399); }}
  .kpi-card.red::before {{ background: linear-gradient(90deg, var(--red), #f97316); }}
  .kpi-card.cyan::before {{ background: linear-gradient(90deg, var(--accent3), #22d3ee); }}
  .kpi-card.orange::before {{ background: linear-gradient(90deg, var(--orange), var(--yellow)); }}
  .kpi-icon {{ font-size: 28px; margin-bottom: 12px; }}
  .kpi-label {{ font-size: 12px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }}
  .kpi-value {{ font-size: clamp(22px, 3vw, 30px); font-weight: 800; color: var(--text); white-space: nowrap; }}
  .kpi-sub {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}

  /* --- charts grid --- */
  .charts-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  .charts-grid.three {{ grid-template-columns: 2fr 1fr; }}
  @media (max-width: 900px) {{
    .charts-grid, .charts-grid.three {{ grid-template-columns: 1fr; }}
  }}
  .chart-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
  }}
  .chart-title {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 20px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .chart-wrap {{ position: relative; height: 260px; }}

  /* --- tables --- */
  .table-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }}
  .table-card table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .table-card th {{
    background: var(--surface2);
    padding: 12px 16px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    text-align: left;
  }}
  .table-card td {{
    padding: 13px 16px;
    font-size: 14px;
    border-top: 1px solid var(--border);
    vertical-align: middle;
  }}
  .table-card tr:hover td {{ background: rgba(255,255,255,0.02); }}
  .table-card small {{ color: var(--text-dim); font-size: 11px; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }}
  .rate-bad {{ color: var(--red) !important; font-weight: 700; }}

  /* --- alerts --- */
  .alerts-list {{ display: flex; flex-direction: column; gap: 10px; }}
  .alert-item {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 14px 18px;
    border-radius: var(--radius-sm);
    border-left: 3px solid;
    font-size: 14px;
    line-height: 1.5;
    transition: background 0.15s;
  }}
  .alert-item:hover {{ background: rgba(255,255,255,0.02); }}
  .alert-critical {{ background: rgba(239,68,68,0.07); border-color: var(--red); }}
  .alert-warning {{ background: rgba(245,158,11,0.07); border-color: var(--orange); }}
  .alert-info {{ background: rgba(99,102,241,0.07); border-color: var(--accent); }}
  .alert-icon {{ font-size: 18px; flex-shrink: 0; margin-top: 2px; }}
  .alert-content {{ flex: 1; }}
  .alert-cat {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-dim);
    display: block;
    margin-bottom: 2px;
  }}
  .alert-content p {{ color: var(--text); }}

  /* --- tags --- */
  .tag {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px 2px 2px 0;
  }}
  .tag-red {{ background: rgba(239,68,68,0.15); color: #fca5a5; }}
  .tag-orange {{ background: rgba(245,158,11,0.15); color: #fcd34d; }}
  .tag-yellow {{ background: rgba(234,179,8,0.15); color: #fde047; }}

  /* --- summary block --- */
  .summary-block {{
    background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.05) 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: var(--radius);
    padding: 28px 32px;
  }}
  .summary-block pre {{
    font-family: 'Inter', sans-serif;
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-muted);
  }}

  /* --- campaign block --- */
  .campaign-block {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }}
  .campaign-icon {{ font-size: 32px; flex-shrink: 0; }}
  .campaign-text h3 {{ font-size: 15px; font-weight: 700; margin-bottom: 6px; }}
  .campaign-text p {{ font-size: 13px; color: var(--text-muted); line-height: 1.6; }}

  /* --- footer --- */
  .footer {{
    margin-top: 60px;
    padding: 24px 0;
    border-top: 1px solid var(--border);
    text-align: center;
    font-size: 12px;
    color: var(--text-dim);
  }}
  .footer a {{ color: var(--accent); text-decoration: none; }}

  /* --- alerts summary bar --- */
  .alert-summary {{
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }}
  .alert-count-badge {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 600;
  }}
  .badge-critical {{ background: rgba(239,68,68,0.15); color: #fca5a5; }}
  .badge-warning {{ background: rgba(245,158,11,0.15); color: #fcd34d; }}
  .badge-info {{ background: rgba(99,102,241,0.15); color: #a5b4fc; }}
</style>
</head>
<body>

<header class="header">
  <div class="header-inner">
    <div class="header-badge">📊 Автоматический отчёт</div>
    <h1>Операционный дашборд</h1>
    <div class="header-meta">
      <span>📅 Период: <strong>{metrics["period_start"]} — {metrics["period_end"]}</strong></span>
      <span>🏭 Товаров: <strong>{len(metrics["chart_data"])}</strong></span>
      <span>⏱ Сгенерирован: <strong>{generated_at}</strong></span>
    </div>
  </div>
</header>

<main>
<div class="container">

  <!-- KPI CARDS -->
  <div class="kpi-grid">
    <div class="kpi-card accent">
      <div class="kpi-icon">💰</div>
      <div class="kpi-label">Общая выручка</div>
      <div class="kpi-value">{_fmt_money(metrics["total_revenue"])}</div>
      <div class="kpi-sub">за {metrics["period_start"]} — {metrics["period_end"]}</div>
    </div>
    <div class="kpi-card green">
      <div class="kpi-icon">📦</div>
      <div class="kpi-label">Продано единиц</div>
      <div class="kpi-value">{metrics["total_sales_count"]:,}</div>
      <div class="kpi-sub">всего транзакций</div>
    </div>
    <div class="kpi-card red">
      <div class="kpi-icon">↩️</div>
      <div class="kpi-label">Возвраты</div>
      <div class="kpi-value">{_pct(metrics["overall_return_rate"])}</div>
      <div class="kpi-sub">{metrics["total_returns_count"]:,} шт. возвращено</div>
    </div>
    <div class="kpi-card cyan">
      <div class="kpi-icon">🏆</div>
      <div class="kpi-label">Топ-товар</div>
      <div class="kpi-value" style="font-size:18px;">{top_product.get("название_товара","—")}</div>
      <div class="kpi-sub">{_fmt_money(top_product.get("total_revenue",0))}</div>
    </div>
    <div class="kpi-card orange">
      <div class="kpi-icon">🚨</div>
      <div class="kpi-label">Алертов</div>
      <div class="kpi-value">{len(alerts)}</div>
      <div class="kpi-sub">{critical_count} критических · {warning_count} предупреждений</div>
    </div>
  </div>

  <!-- CAMPAIGN -->
  <div class="section">
    <div class="section-title">📣 Маркетинговая акция</div>
    <div class="campaign-block">
      <div class="campaign-icon">🎯</div>
      <div class="campaign-text">
        <h3>{campaign.splitlines()[0]}</h3>
        <p>{"<br>".join(campaign.splitlines()[1:]).strip() or campaign}</p>
      </div>
    </div>
  </div>

  <!-- CHARTS ROW 1 -->
  <div class="section">
    <div class="section-title">📈 Динамика и структура</div>
    <div class="charts-grid three">
      <div class="chart-card">
        <div class="chart-title">Выручка по дням</div>
        <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Выручка по категориям</div>
        <div class="chart-wrap"><canvas id="catChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- CHARTS ROW 2 -->
  <div class="section">
    <div class="section-title">🔍 Товарный анализ</div>
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Выручка по товарам</div>
        <div class="chart-wrap"><canvas id="revenueChart"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">% возвратов по товарам</div>
        <div class="chart-wrap"><canvas id="returnChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- CHARTS ROW 3 -->
  <div class="section">
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Остатки на складах</div>
        <div class="chart-wrap"><canvas id="stockChart"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Причины возвратов</div>
        <div class="chart-wrap"><canvas id="reasonChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- TOP PRODUCTS TABLE -->
  <div class="section">
    <div class="section-title">🏆 Топ-5 товаров по выручке</div>
    <div class="table-card">
      <table>
        <thead><tr>
          <th>#</th><th>Товар</th><th>Выручка</th><th>Продано, шт.</th><th>% возвратов</th>
        </tr></thead>
        <tbody>{top_products_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- PROBLEM PRODUCTS TABLE -->
  <div class="section">
    <div class="section-title">⚠️ Проблемные позиции</div>
    <div class="table-card">
      <table>
        <thead><tr>
          <th>Товар</th><th>Выручка</th><th>% возвратов</th><th>Остаток</th><th>Проблемы</th>
        </tr></thead>
        <tbody>{problem_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- ALERTS -->
  <div class="section">
    <div class="section-title">🚨 Алерты</div>
    <div class="alert-summary">
      <div class="alert-count-badge badge-critical">🔴 Критические: {critical_count}</div>
      <div class="alert-count-badge badge-warning">🟡 Предупреждения: {warning_count}</div>
      <div class="alert-count-badge badge-info">🔵 Инфо: {len(alerts) - critical_count - warning_count}</div>
    </div>
    <div class="alerts-list">
      {alerts_html}
    </div>
  </div>

  <!-- SUMMARY -->
  <div class="section">
    <div class="section-title">📋 Итоговое резюме</div>
    <div class="summary-block">
      <pre>{summary_text}</pre>
    </div>
  </div>

</div>
</main>

<footer class="footer">
  <div class="container">
    Отчёт сгенерирован в {generated_at}
  </div>
</footer>

<script>
const COLORS = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#14b8a6','#f97316','#84cc16','#a78bfa','#67e8f9','#6ee7b7','#fcd34d','#fca5a5'];
const gridColor = 'rgba(255,255,255,0.05)';
const textColor = '#94a3b8';

const baseOpts = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor: '#1a2236', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 }} }},
  scales: {{
    x: {{ ticks: {{ color: textColor, font: {{ size: 11 }} }}, grid: {{ color: gridColor }} }},
    y: {{ ticks: {{ color: textColor, font: {{ size: 11 }} }}, grid: {{ color: gridColor }} }}
  }}
}};


new Chart(document.getElementById('trendChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(trend_dates, ensure_ascii=False)},
    datasets: [{{ label: 'Выручка', data: {json.dumps(trend_values)},
      borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.1)',
      fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#6366f1' }}]
  }},
  options: {{ ...baseOpts, plugins: {{ ...baseOpts.plugins, legend: {{ display: false }} }} }}
}});


new Chart(document.getElementById('catChart'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(cat_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(cat_values)}, backgroundColor: COLORS, borderWidth: 0, hoverOffset: 8 }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: true, position: 'right', labels: {{ color: textColor, font: {{ size: 12 }}, boxWidth: 12, padding: 12 }} }},
      tooltip: {{ backgroundColor: '#1a2236', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 }}
    }}
  }}
}});


new Chart(document.getElementById('revenueChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_labels, ensure_ascii=False)},
    datasets: [{{ label: 'Выручка', data: {json.dumps(chart_revenue)},
      backgroundColor: COLORS, borderRadius: 6, borderSkipped: false }}]
  }},
  options: {{ ...baseOpts, indexAxis: 'y', plugins: {{ ...baseOpts.plugins }} }}
}});


new Chart(document.getElementById('returnChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_labels, ensure_ascii=False)},
    datasets: [{{ label: '% возвратов', data: {json.dumps(chart_returns)},
      backgroundColor: {json.dumps(chart_returns)}.map(v => v >= 20 ? '#ef4444' : v >= 15 ? '#f59e0b' : '#6366f1'),
      borderRadius: 6, borderSkipped: false }}]
  }},
  options: {{
    ...baseOpts, indexAxis: 'y',
    plugins: {{ ...baseOpts.plugins }},
    scales: {{ ...baseOpts.scales, x: {{ ...baseOpts.scales.x, ticks: {{ ...baseOpts.scales.x.ticks, callback: v => v + '%' }} }} }}
  }}
}});


new Chart(document.getElementById('stockChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_labels, ensure_ascii=False)},
    datasets: [{{ label: 'Остаток', data: {json.dumps(chart_stock)},
      backgroundColor: {json.dumps(chart_stock)}.map(v => v < 20 ? '#ef4444' : v < 50 ? '#f59e0b' : '#10b981'),
      borderRadius: 6, borderSkipped: false }}]
  }},
  options: {{ ...baseOpts }}
}});


new Chart(document.getElementById('reasonChart'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(reason_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(reason_values)}, backgroundColor: ['#ef4444','#f59e0b','#8b5cf6','#06b6d4','#10b981'], borderWidth: 0, hoverOffset: 8 }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: true, position: 'right', labels: {{ color: textColor, font: {{ size: 12 }}, boxWidth: 12, padding: 12 }} }},
      tooltip: {{ backgroundColor: '#1a2236', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 }}
    }}
  }}
}});
</script>
</body>
</html>"""

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(config.OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    return config.OUTPUT_FILE
