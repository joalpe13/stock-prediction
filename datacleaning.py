import csv
import logging
import chardet
import os
import re
import unicodedata
from datetime import datetime, timedelta

# ── Funciones auxiliares ─────────────────────────────────────────────────────

def clean_text(text):
    try:
        text = unicodedata.normalize('NFKC', text)
        return ''.join(c for c in text if c.isprintable()).strip()
    except:
        return text

def dms_to_decimal(dms_str):
    match = re.search(r'(\d+)[°\s]+(\d+)[′\']?\s*(\d+)?[″"]?', dms_str)
    if match:
        d, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)
        return round(d + m/60 + s/3600, 7)
    try:
        return float(dms_str.replace(',', '.'))
    except:
        return dms_str

def detect_file_encoding(file_path, sample_size=1000):
    with open(file_path, 'rb') as f:
        raw = f.read(sample_size)
    enc = chardet.detect(raw)['encoding'] or 'utf-8'
    return 'utf-8' if chardet.detect(raw)['confidence'] < 0.9 else enc

def normalize_date(date_str):
    try:
        if re.match(r'^\d{8}$', date_str):
            return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        date_str = date_str.replace('.', '-').replace('/', '-').strip()
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except:
        return date_str

def normalize_timestamp(ts_str):
    try:
        t = int(ts_str)
        return datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str

# ── Función principal de normalización de un fichero ──────────────────────────

def normalize_csv(input_path, output_dir):
    # Nombre de salida: input.csv -> input_normalized.csv
    base = os.path.basename(input_path)
    name, _ = os.path.splitext(base)
    output_path = os.path.join(output_dir, f"{name}_normalized.csv")

    enc = detect_file_encoding(input_path)
    logging.info(f"Procesando {base} (encoding={enc}) → {os.path.basename(output_path)}")

    with open(input_path, 'r', encoding=enc, newline='') as fin, \
         open(output_path, 'w', encoding='utf-8', newline='') as fout:

        reader = csv.reader(fin, delimiter=';', quotechar='"', skipinitialspace=True)
        writer = csv.writer(fout, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        header = next(reader, None)
        if not header:
            logging.error(f"{base}: archivo vacío o sin encabezado.")
            return
        writer.writerow(header)
        n_cols = len(header)

        for row in reader:
            # limpieza y padding/truncado
            clean = [ clean_text((v or "").replace('\n',' ').replace('\r',' ')) for v in row ]
            if len(clean) < n_cols:
                clean += [""] * (n_cols - len(clean))
            elif len(clean) > n_cols:
                clean = clean[:n_cols]

            # normaliza fechas, timestamps y coordenadas si existen
            for i, col in enumerate(header):
                v = clean[i]
                low = col.lower()
                if low == 'date':
                    clean[i] = normalize_date(v)
                elif 'time' in low:
                    clean[i] = normalize_timestamp(v)
                elif 'latitud' in low:
                    try: clean[i] = dms_to_decimal(v)
                    except: pass
                elif 'longitud' in low:
                    try:
                        dec = dms_to_decimal(v)
                        clean[i] = -abs(dec)  # long negativa si era positiva
                    except: pass

            writer.writerow(clean)

    logging.info(f"→ Guardado: {output_path}")

# ── Ejecutar en todos los CSV de la carpeta ──────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    input_directory  = "Files"
    output_directory = "processed_files"
    os.makedirs(output_directory, exist_ok=True)

    for fname in os.listdir(input_directory):
        if fname.lower().endswith(".csv"):
            normalize_csv(
                input_path  = os.path.join(input_directory, fname),
                output_dir  = output_directory
            )
