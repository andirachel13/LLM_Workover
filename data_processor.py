# data_processor.py
import re
from typing import List, Dict
from parser import AIParser
from rule_parser import RuleParser

class DataProcessor:
    """Main data processing class"""

    def __init__(self, use_ai: bool = False, api_key: str = None):
        self.use_ai = use_ai
        self.api_key = api_key
        self.ai_parser = AIParser(api_key) if use_ai and api_key else None
        self.rule_parser = RuleParser()

    def process_raw_data(self, raw_text: str) -> List[Dict]:
        """Process raw text data into structured format"""

        # 1. BERSIHKAN KARAKTER SAMPAH
        raw_text = raw_text.replace(';', ' ')
        raw_text = raw_text.replace('|', ' ')
        raw_text = re.sub(r'(?<!\d),(?!\s*\d+%)', ' ', raw_text)
        raw_text = re.sub(r'\s{2,}', ' ', raw_text).strip()

        # 2. PISAHKAN MENJADI BARIS-BARIS LOGIS (PERBAIKAN UTAMA)
        rows = self._parse_raw_input_to_rows(raw_text)
        processed_rows = []

        for row in rows:
            # Hapus karakter aneh di awal/akhir baris
            row = row.strip(' .;:|,')

            if not row:
                continue

            if self.use_ai and self.ai_parser:
                try:
                    parsed_data = self.ai_parser.parse_row(row)
                except:
                    parsed_data = self.rule_parser.parse_row(row)
            else:
                parsed_data = self.rule_parser.parse_row(row)

            if parsed_data:
                processed_rows.append(parsed_data)

        return processed_rows

    def _parse_raw_input_to_rows(self, raw_text: str) -> List[str]:
        """Parse raw text into individual rows by grouping lines without time to the previous row"""
        lines = raw_text.strip().split('\n')
        grouped_rows = []
        current_row_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Periksa apakah baris dimulai dengan Waktu (misal: 06:00 atau 23:00)
            if re.match(r'^\d{1,2}:\d{2}', line):
                # Jika ada baris sebelumnya yang sedang dikumpulkan, simpan dulu
                if current_row_parts:
                    grouped_rows.append(' '.join(current_row_parts))
                
                # Mulai baris baru
                current_row_parts = [line]
            else:
                # Baris ini TIDAK punya waktu, artinya dia adalah lanjutan dari baris sebelumnya
                current_row_parts.append(line)

        # Jangan lupa simpan baris terakhir yang masih dalam antrian
        if current_row_parts:
            grouped_rows.append(' '.join(current_row_parts))

        return grouped_rows
