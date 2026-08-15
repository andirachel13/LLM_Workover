# data_processor.py

import re
from parser import AIParser

class DataProcessor:
    def __init__(self, use_ai=False, api_key=None):
        self.ai_parser = AIParser(api_key) if use_ai and api_key else None

    def process_raw_data(self, raw_text):
        raw_text = raw_text.replace(';', ' ').replace('|', ' ').strip()
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

        results = []
        for row in rows:
            data = self.ai_parser.parse_row(row) if self.ai_parser else None
            if not data:
                # Fallback regex
                times = re.findall(r'\b(\d{1,2}:\d{2})\b', row)
                data = {
                    "waktu_mulai": times[0] if times else "N/A",
                    "waktu_akhir": times[1] if len(times)>1 else "N/A",
                    "durasi_jam": float(re.search(r'(\d+\.\d+)', row).group(1)) if re.search(r'(\d+\.\d+)', row) else 0.0,
                    "peralatan_deskripsi": " ".join([p for p in row.split() if not re.match(r'^\d{1,2}:\d{2}$|\d+\.\d+', p)])[:150],
                    "interval_kedalaman": re.search(r'F\/.*TO.*|@.*FT', row).group(0) if re.search(r'F\/.*TO.*|@.*FT', row) else "N/A",
                    "kondisi_hasil": "N/A"
                }
            # Clean data
            for k, v in data.items():
                if isinstance(v, str): data[k] = v.replace(';', ' ').replace('|', ' ')
            results.append(data)
        return results
