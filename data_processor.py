# data_processor.py

import re
from parser import AIParser

class DataProcessor:
    def __init__(self, use_ai=False, api_key=None):
        self.ai_parser = AIParser(api_key) if use_ai and api_key else None

    def process_raw_data(self, raw_text):
        # 1. Pembersihan Awal
        raw_text = raw_text.replace(';', ' ').replace('|', ' ')
        raw_text = re.sub(r'\s{2,}', ' ', raw_text).strip()

        # 2. Pisahkan baris
        lines = raw_text.split('\n')
        rows, current = [], []
        for line in lines:
            line = line.strip()
            if not line: continue
            if re.match(r'^\d{1,2}:\d{2}', line):
                if current: rows.append(' '.join(current))
                current = [line]
            else: current.append(line)
        if current: rows.append(' '.join(current))

        # 3. Proses per baris
        results = []
        for row in rows:
            # Coba AI dulu
            data = self.ai_parser.parse_row(row) if self.ai_parser else None
            
            # FALLBACK: Jika AI gagal, pakai Regex manual
            if not data:
                data = self._manual_fallback_parser(row)

            if data:
                # Sanitasi akhir
                for k, v in data.items():
                    if isinstance(v, str):
                        data[k] = v.replace(';', ' ').replace('|', ' ').strip()
                results.append(data)

        return results

    def _manual_fallback_parser(self, row: str):
        """Parser regex cadangan jika AI error"""
        times = re.findall(r'\b(\d{1,2}:\d{2})\b', row)
        waktu_mulai = times[0] if times else "N/A"
        waktu_akhir = times[1] if len(times) > 1 else "N/A"
        
        durasi_match = re.search(r'(\d+\.\d+)', row)
        durasi_jam = float(durasi_match.group(1)) if durasi_match else 0.0
        
        depth_match = re.search(r'F\/.*TO.*|@.*FT|\d+\s*-\s*\d+', row)
        kedalaman = depth_match.group(0) if depth_match else "N/A"
        
        return {
            "waktu_mulai": waktu_mulai,
            "waktu_akhir": waktu_akhir,
            "durasi_jam": durasi_jam,
            "peralatan_deskripsi": " ".join([p for p in row.split() if not re.match(r'\d{1,2}:\d{2}|\d+\.\d+', p)])[:200],
            "interval_kedalaman": kedalaman,
            "kondisi_hasil": "N/A"
        }
