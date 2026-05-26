def generate_summary(metrics, alerts, campaign):
    total_revenue = metrics["total_revenue"]
    total_sales = metrics["total_sales_count"]
    total_returns = metrics["total_returns_count"]
    return_rate = metrics["overall_return_rate"]
    period_start = metrics["period_start"]
    period_end = metrics["period_end"]

    top = metrics["top_products"][0] if metrics["top_products"] else {}
    top_name = top.get("название_товара", "—")
    top_revenue = int(top.get("total_revenue", 0))

    critical_alerts = [a for a in alerts if a["priority"] == "critical"]
    warning_alerts = [a for a in alerts if a["priority"] == "warning"]

    cat_rev = metrics["category_revenue"]
    top_category = max(cat_rev, key=cat_rev.get) if cat_rev else "—"

    lines = [
        f"Отчётный период: {period_start} — {period_end}",
        "",
        f"За период зафиксировано продаж на сумму {int(total_revenue):,} ₽ "
        f"({total_sales:,} единиц товара). "
        f"Общий процент возвратов составил {return_rate:.1%} ({total_returns:,} шт.).",
        "",
        f"Лидер по выручке: {top_name} — {top_revenue:,} ₽.",
        f"Наиболее продаваемая категория: {top_category}.",
        "",
    ]

    if critical_alerts:
        lines.append(
            f"⚠️ Выявлено {len(critical_alerts)} критических проблем, требующих немедленного внимания:"
        )
        for a in critical_alerts[:3]:
            lines.append(f"  • {a['message']}")
        if len(critical_alerts) > 3:
            lines.append(f"  • ... и ещё {len(critical_alerts) - 3} критических алерта.")
        lines.append("")

    if warning_alerts:
        lines.append(f"Также зафиксировано {len(warning_alerts)} предупреждений.")
        lines.append("")

    lines.append(
        f"Акция: «{campaign.splitlines()[0]}» — "
        "рекомендуется усилить контроль за товарами с высоким % возвратов "
        "и обеспечить достаточный уровень остатков на складах."
    )

    return "\n".join(lines)
