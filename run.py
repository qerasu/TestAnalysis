import os
import sys
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from src.loader import load_all
from src.metrics import calc_metrics
from src.alerts import generate_alerts
from src.summary import generate_summary
from src.report import generate_report


def main():
    print("=" * 56)
    start = time.time()

    print("\n[1/5] Загрузка данных...")
    data = load_all()
    sales = data["sales"]
    returns = data["returns"]
    stock = data["stock"]
    campaign = data["campaign"]
    print(f"  ✓ sales:   {len(sales)} строк")
    print(f"  ✓ returns: {len(returns)} строк")
    print(f"  ✓ stock:   {len(stock)} позиций")

    print("\n[2/5] Расчёт KPI...")
    metrics = calc_metrics(sales, returns, stock)
    print(f"  ✓ Общая выручка:    {int(metrics['total_revenue']):,} ₽")
    print(f"  ✓ Продано:          {metrics['total_sales_count']:,} шт.")
    print(f"  ✓ % возвратов:      {metrics['overall_return_rate']:.1%}")
    print(f"  ✓ Топ-товар:        {metrics['top_products'][0]['название_товара']}")

    print("\n[3/5] Генерация алертов...")
    alerts = generate_alerts(metrics, sales)
    critical = sum(1 for a in alerts if a["priority"] == "critical")
    warning = sum(1 for a in alerts if a["priority"] == "warning")
    print(f"  ✓ Всего алертов:    {len(alerts)}")
    print(f"  ✓ Критических:      {critical}")
    print(f"  ✓ Предупреждений:   {warning}")
    if critical > 0:
        print("  ⚠️  Критические алерты:")
        for a in alerts:
            if a["priority"] == "critical":
                print(f"     • {a['message']}")

    print("\n[4/5] Формирование резюме...")
    summary_text = generate_summary(metrics, alerts, campaign)
    print("  ✓ Резюме сгенерировано")

    print("\n[5/5] Генерация HTML-отчёта...")
    output_path = generate_report(metrics, alerts, summary_text, campaign)
    elapsed = time.time() - start
    print(f"  ✓ Отчёт сохранён: {output_path}")
    print(f"\n⏱  Готово за {elapsed:.1f} сек.")
    print("=" * 56)

    abs_path = os.path.abspath(output_path)
    print(f"\n🌐 Открываем отчёт в браузере...")
    webbrowser.open(f"file://{abs_path}")
    print(f"   Если браузер не открылся, откройте вручную:")
    print(f"   {abs_path}")
    print()


if __name__ == "__main__":
    main()
