import yfinance as yf
import pandas as pd
import os

# 1) Descarga
ticker = "^GSPC"
raw = yf.download(
    ticker,
    start="1990-01-01",
    end="2024-12-31",
    interval="1d",
    auto_adjust=False,
    progress=False,
)

# 2) Si lo que devuelve tiene MultiIndex en columnas, lo aplanamos tomando el nivel 0
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)

# 3) Resetear índice para convertir la fecha en columna
df = raw.reset_index()

# 4) Eliminar fila 0 o 1 que corresponda al ticker
#    (si en df.loc[0,'Date'] no hay un Timestamp, la quitamos)
if not isinstance(df.loc[0, 'Date'], pd.Timestamp):
    df = df.drop(index=0).reset_index(drop=True)

# 5) Seleccionar únicamente las columnas de interés y reordenar
df = df[['Date', 'Close', 'High', 'Low', 'Open', 'Volume']]

# 6) Crear carpeta y guardar
os.makedirs("Files", exist_ok=True)
out_file = os.path.join("Files", "sp500_historico.csv")
df.to_csv(out_file, index=False)

print("Primeras filas del CSV resultante:")
print(df.head())
