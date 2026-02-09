# exports/csv_exporter.py

import pandas as pd
from datetime import datetime
from config import Config

class CSVExporter:
    """Export data to CSV format"""

    def __init__(self):
        self.config = Config

    def export(self, data: List[Dict], filename: str = None) -> tuple:
        """Export data to CSV"""
        df = self._format_dataframe(data)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workover_data_{timestamp}.csv"

        csv_data = df.to_csv(index=False, encoding='utf-8-sig')

        return csv_data, filename

    def _format_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """Format data as DataFrame"""
        df = pd.DataFrame(data)

        # Rename columns
        df = df.rename(columns=self.config.COLUMN_MAPPING)

        # Format duration
        if "Durasi (Jam)" in df.columns:
            df["Durasi (Jam)"] = df["Durasi (Jam)"].apply(lambda x: f"{x:.1f}")

        return df
