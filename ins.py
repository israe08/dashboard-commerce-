import pandas as pd
df = pd.read_csv("sales_data_brut.csv", encoding="utf-8-sig")
print("Dimensions :", df.shape)
print("Colonnes :", df.columns.tolist())
print("Valeurs nulles :")
print(df.isna().sum())
print("IDs dupliques :", df["Ligne_ID"].duplicated().sum())
print("Commandes :", df["Commande_ID"].nunique())