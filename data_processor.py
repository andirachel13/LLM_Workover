# data_processor.py

import re
import json
from typing import List, Dict
from parser import AIParser
from rule_parser import RuleParser  # Sebagai fallback (cadangan)

class DataProcessor:
    """Main data processing class"""

    def __init__(self, use_ai: bool = False, api_key: str = None):
        self.use_ai = use_ai
        self.api_key = api_key
        self.parser = AIParser(api_key) if use_ai and api_key else None
        self.rule_parser = RuleParser()

    def process_raw_data(self, raw_text: str) -> List[Dict]:
        # 1. Pembersihan Input Awal (Hapus karakter aneh agar AI tidak bingung)
        raw_text = raw_text.replace(';', ' ')
        raw_text = raw_text.replace('|', ' ')
        raw_text = re.sub(r'\s{2,}', ' ', raw_text).strip()

        # 2. Potong data per baris
        rows = self._parse_raw_input_to_rows(raw_text)
        processed_rows = []

        for row in rows:
            # Bersihkan baris dari titik koma/pipe yang tersisa
            row = row.strip(' .;:|,')

            if not row:
                continue

            # 3. KIRIM KE AI (WAJIB)
            if self.use_ai and self.parser:
                try:
                    parsed_data = self.parser.parse_row(row)
                except Exception as e:
                    # Jika AI gagal, pakai rule parser sebagai backup
                    print(f"AI Failed, using fallback: {e}")
                    parsed_data = self.rule_parser.parse_row(row)
            else:
                # Jika AI dimatikan (opsional), pakai rule parser
                parsed_data = self.rule_parser.parse_row(row)

            if parsed_data:
                # 4. PASTIKAN TIDAK ADA KARAKTER ANEH DARI HASIL AI
                # Ini adalah langkah pengamanan (Sanitasi) sebelum masuk tabel
                for key in ['peralatan_deskripsi', 'interval_kedalaman', 'kondisi_hasil']:
                    if key in parsed_data and isinstance(parsed_data[key], str):
                        parsed_data[key] = parsed_data[key].replace(';', ' ').replace('|', ' ').strip()

                processed_rows.append(parsed_data)

        return processed_rows

    def _parse_raw_input_to_rows(self, raw_text: str) -> List[str]:
        """Memecah teks menjadi baris logis berdasarkan waktu (format: 06:00)"""
        lines = raw_text.strip().split('\n')
        grouped_rows = []
        current_row_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.match(r'^\d{1,2}:\d{2}', line):
                if current_row_parts:
                    grouped_rows.append(' '.join(current_row_parts))
                current_row_parts = [line]
            else:
                current_row_parts.append(line)

        if current_row_parts:
            grouped_rows.append(' '.join(current_row_parts))

        return grouped_rows
