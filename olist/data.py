import os
import pandas as pd


class Olist:
    def __init__(self, csv_path=None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_path = csv_path or os.path.join(root, "data")

    def get_data(self):
        files = [f for f in os.listdir(self.csv_path) if f.endswith(".csv")]
        keys = [f.replace("olist_", "").replace("_dataset", "").replace(".csv", "") for f in files]
        return {k: pd.read_csv(os.path.join(self.csv_path, f)) for k, f in zip(keys, files)}
