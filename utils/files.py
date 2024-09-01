import os
import pandas as pd


def append_data(data: pd.DataFrame, data_path):
    if not os.path.exists(data_path):
        open(data_path, "w").close()
    is_empty = os.path.getsize(data_path) == 0
    data.to_csv(data_path, index=False, mode="a", header=is_empty)

