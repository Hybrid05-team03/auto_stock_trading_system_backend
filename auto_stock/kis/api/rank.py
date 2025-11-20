import pandas as pd
import os
from django.conf import settings

def load_top10_symbols():
    path = os.path.join(settings.BASE_DIR, "data", "data.txt")
    df = pd.read_csv(path, sep="\t", dtype=str, header=None)
    df.columns = ["code", "name"]
    return df.to_dict(orient="records")