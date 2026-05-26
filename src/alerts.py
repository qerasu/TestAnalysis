import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

PRIORITY_CRITICAL = "critical"
PRIORITY_WARNING = "warning"
PRIORITY_INFO = "info"


def generate_alerts(metrics, sales):
    alerts = []
    df = metrics["df"]

    for row in metrics["high_returns"]:
        rate = row["return_rate"]
        if rate >= config.RETURN_RATE_THRESHOLD:
            alerts.append({
                "priority": PRIORITY_CRITICAL,
                "icon": "🔴",
                "category": "Возвраты",
                "sku": row["sku"],
                "product": row["название_товара"],
                "message": (
                    f"{row['название_товара']} ({row['sku']}): критически высокий % возвратов "
                    f"— {rate:.1%} ({int(row['total_returns'])} из {int(row['total_sold'])} шт.)"
                ),
            })
        elif rate >= config.RETURN_RATE_WARNING:
            alerts.append({
                "priority": PRIORITY_WARNING,
                "icon": "🟡",
                "category": "Возвраты",
                "sku": row["sku"],
                "product": row["название_товара"],
                "message": (
                    f"{row['название_товара']} ({row['sku']}): повышенный % возвратов "
                    f"— {rate:.1%} ({int(row['total_returns'])} из {int(row['total_sold'])} шт.)"
                ),
            })

    critical_stock = df[df["остаток"] < config.CRITICAL_STOCK_THRESHOLD]
    for _, row in critical_stock.iterrows():
        alerts.append({
            "priority": PRIORITY_CRITICAL,
            "icon": "🔴",
            "category": "Остатки",
            "sku": row["sku"],
            "product": row["название_товара"],
            "message": (
                f"{row['название_товара']} ({row['sku']}): критически низкий остаток "
                f"— {int(row['остаток'])} шт. на складе {row.get('склад', '—')}"
            ),
        })

    low_stock = df[
        (df["остаток"] >= config.CRITICAL_STOCK_THRESHOLD)
        & (df["остаток"] < config.LOW_STOCK_THRESHOLD)
    ]
    for _, row in low_stock.iterrows():
        alerts.append({
            "priority": PRIORITY_WARNING,
            "icon": "🟡",
            "category": "Остатки",
            "sku": row["sku"],
            "product": row["название_товара"],
            "message": (
                f"{row['название_товара']} ({row['sku']}): низкий остаток "
                f"— {int(row['остаток'])} шт. на складе {row.get('склад', '—')}"
            ),
        })

    zero_days = (
        sales[sales["продано_штук"] == 0]
        .groupby("sku")
        .size()
        .reset_index(name="zero_days")
    )
    zero_days = zero_days.merge(
        df[["sku", "название_товара", "остаток"]], on="sku", how="left"
    )
    problematic_zero = zero_days[
        (zero_days["zero_days"] >= config.ZERO_SALES_WITH_STOCK_THRESHOLD)
        & (zero_days["остаток"] > 0)
    ]
    for _, row in problematic_zero.iterrows():
        alerts.append({
            "priority": PRIORITY_WARNING,
            "icon": "🟠",
            "category": "Продажи",
            "sku": row["sku"],
            "product": row["название_товара"],
            "message": (
                f"{row['название_товара']} ({row['sku']}): {int(row['zero_days'])} дней без продаж "
                f"при остатке {int(row['остаток'])} шт."
            ),
        })

    for row in metrics["low_sales"]:
        alerts.append({
            "priority": PRIORITY_INFO,
            "icon": "🔵",
            "category": "Продажи",
            "sku": row["sku"],
            "product": row["название_товара"],
            "message": (
                f"{row['название_товара']} ({row['sku']}): низкие продажи "
                f"— выручка {int(row['total_revenue']):,} ₽, {int(row['total_sold'])} шт."
            ),
        })

    for row in metrics["anomalies"]:
        direction = "аномально высокая" if row["revenue_zscore"] > 0 else "аномально низкая"
        alerts.append({
            "priority": PRIORITY_INFO,
            "icon": "⚠️",
            "category": "Аномалии",
            "sku": row["sku"],
            "product": row["название_товара"],
            "message": (
                f"{row['название_товара']} ({row['sku']}): {direction} выручка "
                f"— {int(row['total_revenue']):,} ₽ (Z-score: {row['revenue_zscore']:.1f})"
            ),
        })

    priority_order = {PRIORITY_CRITICAL: 0, PRIORITY_WARNING: 1, PRIORITY_INFO: 2}
    alerts.sort(key=lambda x: priority_order.get(x["priority"], 3))

    return alerts
