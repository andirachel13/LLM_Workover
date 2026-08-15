# rule_parse.py (updated)

import re
from typing import Dict

class RuleParser:
    """Rule-based parser for drilling workover data (Final Clean Version)"""

    def parse_row(self, row: str) -> Dict:
        # 1. Ekstrak Waktu
        waktu_mulai, waktu_akhir = self._extract_times(row)
        
        # 2. Ekstrak Durasi
        durasi_jam = self._extract_duration(row)
        
        # 3. Ekstrak Kedalaman (Prioritas tinggi)
        depth_interval = self._extract_depth_interval(row)
        
        # 4. Ekstrak Kondisi/Hasil (Prioritas sedang)
        condition_result = self._extract_condition(row)

        # 5. EKSTRAK DESKRIPSI (Metode Baru: Ambil Semua Sisa Teks dalam 1 Tempat)
        # Kita tidak menghapus dengan replace, tapi mencari pola deskripsi di awal baris
        equipment_description = self._extract_equipment_description(row, depth_interval, condition_result)

        return {
            "waktu_mulai": waktu_mulai,
            "waktu_akhir": waktu_akhir,
            "durasi_jam": durasi_jam,
            "peralatan_deskripsi": equipment_description,
            "interval_kedalaman": depth_interval,
            "kondisi_hasil": condition_result
        }

    def _extract_times(self, row: str) -> tuple:
        time_pattern = r'\b(\d{1,2}:\d{2})\b'
        times = re.findall(time_pattern, row)
        return (times[0] if len(times) > 0 else "N/A", 
                times[1] if len(times) > 1 else "N/A")

    def _extract_duration(self, row: str) -> float:
        duration_pattern = r'(\d+\.?\d*)\s*(?:Jam|jam|hours?|hrs?)'
        match = re.search(duration_pattern, row, re.IGNORECASE)
        if match:
            return float(match.group(1))
        dec_pattern = r'\b(\d+\.\d+)\b'
        dec_match = re.search(dec_pattern, row)
        return float(dec_match.group(1)) if dec_match else 0.0

    def _extract_depth_interval(self, row: str) -> str:
        depth_patterns = [
            r'F\/\s*\d+[\'"]?\s*TO\s*\d+[\'"]?',  
            r'@\s*\d+[\'"]?\s*(?:FT|ft)?',       
            r'\d+[\'"]?\s*-\s*\d+[\'"]?\s*(?:FT|ft)?', 
            r'\d+\s*FT\s+FILL',                  
            r'TO\s*SAND\s*@\s*\d+',              
            r'INTERVAL\s*:\s*[\d\s\'"-]+'        
        ]
        for pattern in depth_patterns:
            match = re.search(pattern, row, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return "N/A"

    def _extract_condition(self, row: str) -> str:
        # Pola kondisi yang jelas
        condition_patterns = [
            r'PEKERJAAN TERHENTI',
            r'SAND PUMP NOT GO DOWN',
            r'NOT GO DOWN',
            r'MUD & SAND FORMATION',
            r'RE RUN',
            r'CLEAN',
            r'WATER\s*:\s*\d+%\s*,\s*OIL\s*:\s*\d+%\s*,\s*SEDIMENT\s*:\s*\d+%',
            r'IFL\s*:.*BBLS'
        ]
        for pattern in condition_patterns:
            match = re.search(pattern, row, re.IGNORECASE)
            if match:
                return match.group(0).strip()
                
        # Jika ada kalimat perintah yang jelas (dimulai dengan TO, atau REPORTED), anggap sebagai kondisi awal
        report_pattern = r'(REPORTED TO .*?)(?:\.|\s+AND|\s+W/)'
        report_match = re.search(report_pattern, row, re.IGNORECASE)
        if report_match:
            return report_match.group(1).strip()
            
        return "N/A"

    def _extract_equipment_description(self, row: str, depth_str: str, condition_str: str) -> str:
        # STRATEGI BARU: Copy full text, lalu kita pangkas berdasarkan posisi kata kunci
        clean_desc = row.strip()

        # 1. Hapus waktu awal-akhir
        clean_desc = re.sub(r'\b\d{1,2}:\d{2}\b', '', clean_desc)
        
        # 2. Hapus durasi (beserta kata 'Jam' jika ada)
        clean_desc = re.sub(r'\b\d+\.?\d*\s*(?:Jam|jam|hours?|hrs?)\b', '', clean_desc)

        # 3. Hapus string kedalaman yang sudah diambil (hanya hapersis jika ada di tengah kalimat)
        if depth_str != "N/A":
            # Gunakan batas kata (\b) agar tidak salah hapus.
            escaped = re.escape(depth_str)
            clean_desc = re.sub(r'\s*' + escaped + r'\s*', ' ', clean_desc)

        # 4. Hapus string kondisi yang sudah diambil
        if condition_str != "N/A":
            escaped_cond = re.escape(condition_str)
            clean_desc = re.sub(r'\s*' + escaped_cond + r'\s*', ' ', clean_desc)

        # 5. Pembersihan Karakter Kotor (Hapus sisa titik koma, pipe, koma di awal/akhir kalimat)
        clean_desc = re.sub(r'^[;\|,\s]+', '', clean_desc)   # Hapus pemisah di AWAL
        clean_desc = re.sub(r'[;\|,\s]+$', '', clean_desc)   # Hapus pemisah di AKHIR
        clean_desc = re.sub(r'\s{2,}', ' ', clean_desc)      # Ubah double space jadi single space
        
        return clean_desc if clean_desc.strip() else "N/A"
