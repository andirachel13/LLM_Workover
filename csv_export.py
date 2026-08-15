# csv_export.py

import pandas as pd
from typing import List, Dict
from config import Config

class CSVExporter:
    """Exporter for CSV and Dataframe formatting"""

    def export(self, data: List[Dict]) -> tuple:
        """Export data as CSV string"""
        df = self._format_dataframe(data)
        csv_data = df.to_csv(index=False)
        filename = "drilling_workover_data.csv"
        return csv_data, filename

    def _format_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """Convert data to pandas DataFrame with proper formatting"""
        if not data:
            return pd.DataFrame()

        # 1. Konversi data list dictionary ke DataFrame
        df = pd.DataFrame(data)
        
        # 2. Ganti semua nilai NaN dengan string kosong agar tabel lebih bersih
        df = df.fillna('')
        
        # 3. Ubah nama kolom ke Bahasa Indonesia sesuai Config
        df = df.rename(columns=Config.COLUMN_MAPPING)

        # 4. PASTIKAN TIDAK ADA KARAKTER PEMISAH ANEH
        # Loop melalui semua kolom teks
        for col in df.columns:
            # Jika isi kolom adalah list (karena mungkin ada sisa logika penggabungan), ubah menjadi string biasa
            df[col] = df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)
            
            # HAPUS KARAKTER SAMPAH SEPERTI '|' ATAU ';' DI DALAM STRING
            df[col] = df[col].astype(str).str.replace('|', ' ')
            df[col] = df[col].astype(str).str.replace(';', ' ')
            df[col] = df[col].astype(str).str.replace('  ', ' ') # Hapus spasi ganda

        return df
