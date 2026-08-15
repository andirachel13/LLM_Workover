# data_processor.py

import re
from typing import List, Dict
from parser import AIParser

class DataProcessor:
    def __init__(self, use_ai: bool = False, api_key: str = None):
        self.ai_parser = AIParser(api_key) if use_ai and api_key else None

    def process_raw_data(self, raw_text: str) -> List[Dict]:
        # Pembersihan awal
        raw_text = raw_text.replace(';', ' ').replace('|', ' ')
        raw_text = re.sub(r'\s{2,}', ' ', raw_text).strip()

        # Ubah teks menjadi list baris berdasarkan waktu
        lines = raw_text.split('\n')
        rows, current = [], []
        for line in lines:
            line = line.strip()
            if not line: continue
            if re.match(r'^\d{1,2}:\d{2}', line):
                if current: rows.append(' '.join(current))
                current = [line]
            else:
                current.append(line)
        if current: rows.append(' '.join(current))

        results = []
        for row in rows:
            data = self.ai_parser.parse_row(row) if self.ai_parser else None

            # FALLBACK (Jika AI gagal total)
            if not data:
                data = self._regex_fallback(row)

            if data:
                # Pembersihan akhir (hapus ;, |, dan spasi ganda)
                for k, v in data.items():
                    if isinstance(v, str):
                        data[k] = re.sub(r'\s{2,}', ' ', v.replace(';', ' ').replace('|', ' ')).strip()
                results.append(data)

        return results

    def _regex_fallback(self, row: str) -> Dict:
        """Parser Regex jika AI gagal (Memastikan kolom Kedalaman dan Kondisi terisi)"""
        times = re.findall(r'\b(\d{1,2}:\d{2})\b', row)
        waktu_mulai = times[0] if times else "N/A"
        waktu_akhir = times[1] if len(times) > 1 else "N/A"
        
        durasi_match = re.search(r'(\d+\.\d+)', row)
        durasi_jam = float(durasi_match.group(1)) if durasi_match else 0.0
        
        # Cari Kedalaman yang spesifik
        depth_match = re.search(r'F\/\s*\d+[\'"]?\s*TO\s*\d+[\'"]?|@\s*\d+[\'"]?(?:\s*FT)?|\d+[\'"]?\s*-\s*\d+[\'"]?', row)
        kedalaman = depth_match.group(0) if depth_match else "N/A"
        
        # Cari Kondisi / Hasil
        condition_match = re.search(r'(SAND PUMP NOT GO DOWN|MUD & SAND FORMATION|CLEAN|RE RUN|SAND FILL|23 FT SAND FILL|PEKERJAAN TERHENTI)', row, re.IGNORECASE)
        kondisi = condition_match.group(0) if condition_match else "N/A"
        
        # Sisa teks sebagai Deskripsi
        desc = row
        desc = re.sub(r'\b\d{1,2}:\d{2}\b', '', desc)
        desc = re.sub(r'\d+\.\d+', '', desc)
        if kedalaman != "N/A": desc = desc.replace(kedalaman, '')
        if kondisi != "N/A": desc = desc.replace(kondisi, '')
        desc = re.sub(r'\s{2,}', ' ', desc).strip()
        
        return {
            "waktu_mulai": waktu_mulai,
            "waktu_akhir": waktu_akhir,
            "durasi_jam": durasi_jam,
            "peralatan_deskripsi": desc,
            "interval_kedalaman": kedalaman,
            "kondisi_hasil": kondisi
        }
