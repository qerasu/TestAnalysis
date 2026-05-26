import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_sales():
    df = pd.read_csv(config.SALES_FILE, parse_dates=["дата"])
    df.columns = df.columns.str.strip()
    df["выручка"] = pd.to_numeric(df["выручка"], errors="coerce").fillna(0)
    df["продано_штук"] = pd.to_numeric(df["продано_штук"], errors="coerce").fillna(0)
    df["сессии"] = pd.to_numeric(df["сессии"], errors="coerce").fillna(0)
    return df


def load_returns():
    df = pd.read_csv(config.RETURNS_FILE, parse_dates=["дата"])
    df.columns = df.columns.str.strip()
    df["количество_возвратов"] = pd.to_numeric(
        df["количество_возвратов"], errors="coerce"
    ).fillna(0)
    return df


def load_stock():
    df = pd.read_csv(config.STOCK_FILE)
    df.columns = df.columns.str.strip()
    df["остаток"] = pd.to_numeric(df["остаток"], errors="coerce").fillna(0)
    return df


def load_campaign():
    with open(config.CAMPAIGN_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_all():
    return {
        "sales": load_sales(),
        "returns": load_returns(),
        "stock": load_stock(),
        "campaign": load_campaign(),
    }
