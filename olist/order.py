import numpy as np
import pandas as pd
from olist.data import Olist
from olist.utils import REVIEW_COSTS, SALES_FEE_RATE, haversine_distance


class Order:
    def __init__(self, data=None):
        self.data = data or Olist().get_data()

    def get_orders(self):
        orders = self.data["orders"].copy()
        for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
                    "order_delivered_customer_date", "order_estimated_delivery_date"]:
            orders[col] = pd.to_datetime(orders[col])
        return orders

    def get_wait_time(self, is_delivered=True):
        orders = self.get_orders()
        if is_delivered:
            orders = orders[orders["order_status"] == "delivered"].copy()
        one_day = pd.Timedelta(days=1)
        orders["wait_time"] = (orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]) / one_day
        orders["expected_wait_time"] = (orders["order_estimated_delivery_date"] - orders["order_purchase_timestamp"]) / one_day
        orders["delay_vs_expected"] = ((orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]) / one_day).clip(lower=0)
        return orders[["order_id", "wait_time", "expected_wait_time", "delay_vs_expected", "order_status"]]

    def get_review_score(self):
        reviews = self.data["order_reviews"].copy()
        reviews["cost_of_review"] = reviews["review_score"].map(REVIEW_COSTS)
        per_order = reviews.groupby("order_id").agg(
            review_score=("review_score", "mean"),
            cost_of_review=("cost_of_review", "mean"),
            n_reviews=("review_id", "count"),
        ).reset_index()
        per_order["dim_is_one_star"] = (per_order["review_score"] == 1).astype(int)
        per_order["dim_is_five_star"] = (per_order["review_score"] == 5).astype(int)
        return per_order

    def get_number_items(self):
        return self.data["order_items"].groupby("order_id").agg(number_of_items=("order_item_id", "count")).reset_index()

    def get_number_sellers(self):
        return self.data["order_items"].groupby("order_id").agg(number_of_sellers=("seller_id", "nunique")).reset_index()

    def get_price_and_freight(self):
        return self.data["order_items"].groupby("order_id").agg(price=("price", "sum"), freight_value=("freight_value", "sum")).reset_index()

    def get_distance_seller_customer(self):
        geo = self.data["geolocation"].groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]].first()
        sellers = self.data["sellers"].join(geo, on="seller_zip_code_prefix")[["seller_id", "geolocation_lat", "geolocation_lng"]]
        customers = self.data["customers"].join(geo, on="customer_zip_code_prefix")[["customer_id", "geolocation_lat", "geolocation_lng"]]
        orders = self.data["orders"].query("order_status == 'delivered'")[["order_id", "customer_id"]]
        df = (
            orders.merge(self.data["order_items"][["order_id", "seller_id"]], on="order_id")
            .merge(sellers, on="seller_id")
            .merge(customers, on="customer_id", suffixes=("_seller", "_customer"))
            .dropna()
        )
        df["distance_seller_customer"] = haversine_distance(
            df["geolocation_lng_seller"], df["geolocation_lat_seller"],
            df["geolocation_lng_customer"], df["geolocation_lat_customer"],
        )
        return df.groupby("order_id").agg(distance_seller_customer=("distance_seller_customer", "mean")).reset_index()

    def get_order_items_economics(self):
        items = self.data["order_items"].merge(self.data["orders"][["order_id", "order_status"]], on="order_id")
        items["is_delivered"] = items["order_status"] == "delivered"
        items["sales_fee"] = np.where(items["is_delivered"], items["price"] * SALES_FEE_RATE, 0.0)

        reviews = self.get_review_score()[["order_id", "review_score", "cost_of_review"]]
        items = items.merge(reviews, on="order_id", how="left")
        items["cost_of_review"] = items["cost_of_review"].fillna(0)
        items["item_share"] = 1 / items.groupby("order_id")["order_item_id"].transform("count")
        items["cost_of_review_allocated"] = items["cost_of_review"] * items["item_share"]
        return items

    def get_order_economics(self):
        items = self.get_order_items_economics()
        return items.groupby("order_id").agg(
            order_status=("order_status", "first"),
            number_of_items=("order_item_id", "count"),
            number_of_sellers=("seller_id", "nunique"),
            price=("price", "sum"),
            sales_fee=("sales_fee", "sum"),
            review_score=("review_score", "first"),
            cost_of_review=("cost_of_review_allocated", "sum"),
        ).reset_index()

    def get_training_data(self, is_delivered=True, with_distance_seller_customer=False):
        training = (
            self.get_wait_time(is_delivered)
            .merge(self.get_review_score(), on="order_id")
            .merge(self.get_number_items(), on="order_id")
            .merge(self.get_number_sellers(), on="order_id")
            .merge(self.get_price_and_freight(), on="order_id")
        )
        if with_distance_seller_customer:
            training = training.merge(self.get_distance_seller_customer(), on="order_id")
        return training.dropna()
