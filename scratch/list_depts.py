import pandas as pd
df = pd.read_parquet("data/processed/agg_territorial.parquet")
print(sorted(df["departamento_hecho"].unique()))
