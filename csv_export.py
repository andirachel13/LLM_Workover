# exports/csv_exporter.py
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
from config import Config  # Import the Config class

class CSVExporter:
    """Export data to CSV format"""

    def __init__(self):
        # Config is a class with static properties, no need to instantiate
        # We'll access Config.COLUMN_MAPPING directly
        pass

    def export(self, data: List[Dict], filename: str = None) -> Tuple[str, str]:
        """Export data to CSV"""
        df = self._format_dataframe(data)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workover_data_{timestamp}.csv"

        csv_data = df.to_csv(index=False, encoding='utf-8-sig')

        return csv_data, filename

    def _format_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """Format data as DataFrame"""
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)

        # Rename columns using Config.COLUMN_MAPPING
        # Note: Make sure your data dict keys match the keys in COLUMN_MAPPING
        if hasattr(Config, 'COLUMN_MAPPING'):
            # Only rename columns that exist in the DataFrame
            column_mapping = {k: v for k, v in Config.COLUMN_MAPPING.items() 
                            if k in df.columns}
            if column_mapping:
                df = df.rename(columns=column_mapping)
        else:
            # Fallback if COLUMN_MAPPING is not defined
            print("Warning: COLUMN_MAPPING not found in Config")

        # Format duration - check both possible column names
        duration_columns = ["Durasi (Jam)", "durasi_jam"]
        for col in duration_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{float(x):.1f}" if pd.notnull(x) else "")
                break

        return df
