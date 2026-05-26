import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def calc_metrics(sales, returns, stock):
    by_sku = sales.groupby(["sku", "название_товара"]).agg(
        total_revenue=("выручка", "sum"),
        total_sold=("продано_штук", "sum"),
        total_sessions=("сессии", "sum"),
        sale_days=("дата", "nunique"),
    ).reset_index()

    returns_by_sku = returns.groupby("sku").agg(
        total_returns=("количество_возвратов", "sum")
    ).reset_index()

    df = by_sku.merge(returns_by_sku, on="sku", how="left")
    df["total_returns"] = df["total_returns"].fillna(0)

    df = df.merge(stock[["sku", "остаток", "склад"]], on="sku", how="left")

    df["return_rate"] = np.where(
        df["total_sold"] > 0,
        df["total_returns"] / df["total_sold"],
        0,
    )

    revenue_mean = df["total_revenue"].mean()
    revenue_std = df["total_revenue"].std()
    df["revenue_zscore"] = np.where(
        revenue_std > 0,
        (df["total_revenue"] - revenue_mean) / revenue_std,
        0,
    )

    total_revenue = sales["выручка"].sum()
    total_sales_count = int(sales["продано_штук"].sum())
    total_returns_count = int(returns["количество_возвратов"].sum())
    period_start = sales["дата"].min().strftime("%d.%m.%Y")
    period_end = sales["дата"].max().strftime("%d.%m.%Y")
    overall_return_rate = (
        total_returns_count / total_sales_count if total_sales_count > 0 else 0
    )

    top_products = df.nlargest(5, "total_revenue")[
        ["sku", "название_товара", "total_revenue", "total_sold", "return_rate"]
    ].to_dict("records")

    low_threshold = df["total_revenue"].quantile(config.LOW_SALES_PERCENTILE)
    low_sales = df[df["total_revenue"] <= low_threshold][
        ["sku", "название_товара", "total_revenue", "total_sold", "остаток"]
    ].to_dict("records")

    high_returns = df[df["return_rate"] >= config.RETURN_RATE_WARNING].sort_values(
        "return_rate", ascending=False
    )[["sku", "название_товара", "return_rate", "total_returns", "total_sold"]].to_dict(
        "records"
    )

    anomalies = df[df["revenue_zscore"].abs() >= config.ANOMALY_ZSCORE][
        ["sku", "название_товара", "total_revenue", "revenue_zscore"]
    ].to_dict("records")

    chart_data = df.sort_values("total_revenue", ascending=False)[
        ["sku", "название_товара", "total_revenue", "total_sold", "return_rate", "остаток"]
    ].to_dict("records")

    return_reasons = (
        returns.groupby("причина_возврата")["количество_возвратов"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    daily_revenue = (
        sales.groupby("дата")["выручка"]
        .sum()
        .reset_index()
        .sort_values("дата")
    )
    daily_revenue["дата_str"] = daily_revenue["дата"].dt.strftime("%d.%m")
    revenue_trend = {
        "dates": daily_revenue["дата_str"].tolist(),
        "values": daily_revenue["выручка"].tolist(),
    }

    category_revenue = (
        sales.groupby("категория")["выручка"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    return {
        "total_revenue": total_revenue,
        "total_sales_count": total_sales_count,
        "total_returns_count": total_returns_count,
        "overall_return_rate": overall_return_rate,
        "period_start": period_start,
        "period_end": period_end,
        "top_products": top_products,
        "low_sales": low_sales,
        "high_returns": high_returns,
        "anomalies": anomalies,
        "chart_data": chart_data,
        "return_reasons": return_reasons,
        "revenue_trend": revenue_trend,
        "category_revenue": category_revenue,
        "df": df,
    }
