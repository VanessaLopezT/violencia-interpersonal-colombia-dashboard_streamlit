import pandas as pd

# Export a small sample (2.000 filas) for evidence/inspection
N = 10000

df = pd.read_csv(
	"data/processed/dataset_limpio.csv",
	encoding="utf-8-sig",
	low_memory=False,
	nrows=N,
)

df.to_excel("data/processed/dataset_limpio_2k.xlsx", index=False)