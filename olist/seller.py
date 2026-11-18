import numpy as np
import pandas as pd
from olist.data import Olist
from olist.order import Order
from olist.utils import SUBSCRIPTION_PER_MONTH, IT_ALPHA, IT_BETA, it_costs


class Seller:
    def __init__(self, data=None):
        self.data = data or Olist().get_data()
        self.order = Order(self.data)

    def get_seller_features(self):
        return self.data["sellers"][["seller_id", "seller_city", "seller_state"]].drop_duplicates()

    def get_seller_delay_wait_time(self):
        orders = self.order.get_orders()
        items = self.data["order_items"].copy()
        items["shipping_limit_date"] = pd.to_datetime(items["shipping_limit_date"])
        shipped = items.merge(orders[orders["order_status"] == "delivered"], on="order_id")
        one_day = pd.Timedelta(days=1)
        shipped["carrier_vs_limit"] = (shipped["order_delivered_carrier_date"] - shipped["shipping_limit_date"]) / one_day
        shipped["wait_time"] = (shipped["order_delivered_customer_date"] - shipped["order_purchase_timestamp"]) / one_day
        df = shipped.groupby("seller_id").agg(delay_to_carrier=("carrier_vs_limit", "mean"), wait_time=("wait_time", "mean")).reset_index()
        df["delay_to_carrier"] = df["delay_to_carrier"].clip(lower=0)
        return df

    def get_active_dates(self):
        orders = self.order.get_orders()[["order_id", "order_approved_at"]]
        df = self.data["order_items"].merge(orders, on="order_id").groupby("seller_id").agg(
            date_first_sale=("order_approved_at", "min"),
            date_last_sale=("order_approved_at", "max"),
        ).reset_index()
        df["months_on_olist"] = ((df["date_last_sale"] - df["date_first_sale"]) / pd.Timedelta(days=30)).round()
        return df

    def get_quantity(self):
        df = self.data["order_items"].groupby("seller_id").agg(
            n_orders=("order_id", "nunique"),
            quantity=("order_item_id", "count"),
        ).reset_index()
        df["quantity_per_order"] = df["quantity"] / df["n_orders"]
        return df

    def get_sales(self):
        items = self.order.get_order_items_economics()
        return items.groupby("seller_id").agg(sales=("price", "sum"), sales_fees=("sales_fee", "sum")).reset_index()

    def get_review_score(self):
        items = self.order.get_order_items_economics().dropna(subset=["review_score"])
        seller_orders = items.groupby(["seller_id", "order_id"]).agg(
            review_score=("review_score", "first"),
            cost_of_review=("cost_of_review_allocated", "sum"),
        ).reset_index()
        seller_orders["one_star"] = (seller_orders["review_score"] == 1).astype(int)
        seller_orders["five_star"] = (seller_orders["review_score"] == 5).astype(int)
        return seller_orders.groupby("seller_id").agg(
            share_of_one_stars=("one_star", "mean"),
            share_of_five_stars=("five_star", "mean"),
            review_score=("review_score", "mean"),
            cost_of_reviews=("cost_of_review", "sum"),
        ).reset_index()

    def get_training_data(self, alpha=IT_ALPHA, beta=IT_BETA):
        sellers = (
            self.get_seller_features()
            .merge(self.get_seller_delay_wait_time(), on="seller_id")
            .merge(self.get_active_dates(), on="seller_id")
            .merge(self.get_quantity(), on="seller_id")
            .merge(self.get_sales(), on="seller_id")
            .merge(self.get_review_score(), on="seller_id")
        )
        sellers["subscription_fees"] = sellers["months_on_olist"] * SUBSCRIPTION_PER_MONTH
        sellers["revenues"] = sellers["subscription_fees"] + sellers["sales_fees"]
        sellers["revenue_per_month"] = sellers["revenues"] / sellers["months_on_olist"].clip(lower=1)
        sellers["profits"] = sellers["revenues"] - sellers["cost_of_reviews"]

        n_sellers, n_items = len(sellers), sellers["quantity"].sum()
        seller_part = alpha * np.sqrt(n_sellers) / n_sellers
        item_part = beta * np.sqrt(n_items) / n_items
        sellers["operational_costs"] = seller_part + item_part * sellers["quantity"]
        sellers["net_contribution"] = sellers["revenues"] - (sellers["cost_of_reviews"] + sellers["operational_costs"])
        return sellers
