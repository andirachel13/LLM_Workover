# data_processor.py

import re
from typing import List, Dict
from parser import AIParser  # Perbaikan: Import dari file parser.py (tanpa folder)

class DataProcessor:
    """Main data processing class"""

    def __init__(self, use_ai: bool = False, api_key: str = None):
        self.use_ai = use_ai
        self.api_key = api_key
        self.ai_parser = AIParser(api_key) if use_ai and api_key else None

    def process_raw_data(self, raw_text: str) -> List[Dict]:
        # 1. Pembersihan Awal
        raw_text = raw_text.replace(';', ' ').replace('|', ' ')
        raw_text = re.sub(r'\s{2,}', ' ', raw_text).strip()

        # 2. Pisahkan per baris logis
        rows = self._parse_raw_input_to_rows(raw_text)
        processed_rows = []

        for row in rows:
            row = row.strip(' .;:|,')
            if not row: continue

            # 3. Gunakan AI jika aktif
            if self.use_ai and self.ai_parser:
                try:
                    parsed_data = self.ai_parser.parse_row(row)
                except Exception:
                    # Jika AI gagal, gunakan parser manual sederhana sebagai backup
                    parsed_data = self._manual_fallback_parser(row)
            else:
                parsed_data = self._manual_fallback_parser(row)

            if parsed_data:
                # 4. Lapisan pengaman akhir
                for key in ['peralatan_deskripsi', 'interval_kedalaman', 'kondisi_hasil']:
                    if key in parsed_data and isinstance(parsed_data[key], str):
                        parsed_data[key] = parsed_data[key].replace(';', ' ').replace('|', ' ')
                        parsed_data[key] = re.sub(r'\s{2,}', ' ', parsed_data[key]).strip()
                processed_rows.append(parsed_data)

        return processed_rows

    def _parse_raw_input_to_rows(self, raw_text: str) -> List[str]:
        lines = raw_text.strip().split('\n')
        grouped_rows, current = [], []
        for line in lines:
            line = line.strip()
            if not line: continue
            if re.match(r'^\d{1,2}:\d{2}', line):
                if current: grouped_rows.append(' '.join(current))
                current = [line]
            else: current.append(line)
        if current: grouped_rows.append(' '.join(current))
        return grouped_rows

    def _manual_fallback_parser(self, row: str) -> Dict:
        """Parser manual cadangan jika AI gagal"""
        times = re.findall(r'\b(\d{1,2}:\d{2})\b', row)
        waktu_mulai = times[0] if len(times) > 0 else "N/A"
        waktu_akhir = times[1] if len(times) > 1 else "N/A"
        
        durasi_match = re.search(r'(\d+\.\d+)', row)
        durasi_jam = float(durasi_match.group(1)) if durasi_match else 0.0
        
        depth_match = re.search(r'F\/\s*\d+[\'"]?\s*TO\s*\d+[\'"]?', row) or \
                      re.search(r'@\s*\d+[\'"]?(?:\s*FT)?', row)
        kedalaman = depth_match.group(0) if depth_match else "N/A"
        
        condition_match = re.search(r'(PEKERJAAN TERHENTI|SAND PUMP NOT GO DOWN|MUD & SAND FORMATION|CLEAN)', row, re.IGNORECASE)
        kondisi = condition_match.group(0) if condition_match else "N/A"
        
        desc = row
        desc = re.sub(r'\b\d{1,2}:\d{2}\b', '', desc)
        desc = re.sub(r'\d+\.\d+\s*(?:Jam|jam)?', '', desc)
        if kedalaman != "N/A": desc = desc.replace(kedalaman, '')
        if kondisi != "N/A": desc = desc.replace(kondisi, '')
        desc = re.sub(r'\s{2,}', ' ', desc).strip()
        
        return {
            "waktu_mulai": waktu_mulai,
            "waktu_akhir": waktu_akhir,
            "durasi_jam": durasi_jam,
            "peralatan_deskripsi": desc[:200],
            "interval_kedalaman": kedalaman,
            "kondisi_hasil": kondisi
        }
