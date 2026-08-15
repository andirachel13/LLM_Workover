# rule_parser.py

import re
from typing import Dict

class RuleParser:
    """Rule-based parser for drilling workover data (Improved)"""

    def parse_row(self, row: str) -> Dict:
        """Parse a single row using advanced Regex"""
        
        # 1. Ekstrak Waktu & Durasi (Menggunakan Regex yang lebih ketat)
        waktu_mulai, waktu_akhir = self._extract_times(row)
        durasi_jam = self._extract_duration(row)

        # 2. Ekstrak Interval/Kedalaman (Bagian Paling Kritis)
        depth_interval = self._extract_depth_interval(row)

        # 3. Ekstrak Kondisi/Hasil Utama (Mencari kata kunci khusus kondisi)
        # Contoh: "Pekerjaan terhenti", "SAND PUMP NOT GO DOWN", "CLEAN", "FORMATION"
        condition_result = self._extract_condition(row)

        # 4. Sisa teks adalah Deskripsi Peralatan
        # Metode: Hapus waktu, durasi, kedalaman, & kondisi dari teks asli. Sisanya adalah peralatan.
        equipment_description = row
        
        # Hapus waktu
        time_pattern = r'\d{1,2}:\d{2}'
        equipment_description = re.sub(time_pattern, '', equipment_description)
        
        # Hapus durasi (angka desimal + optional kata Jam)
        equipment_description = re.sub(r'\s*\d+\.?\d*\s*(?:Jam|jam|hours?|hrs?)?', '', equipment_description)
        
        # Hapus string kedalaman yang sudah diekstrak (jika ketemu di tengah kalimat)
        if depth_interval != "N/A":
            # Hapus secara spesifik agar tidak menghapus kata lain yang mirip
            escaped_depth = re.escape(depth_interval)
            equipment_description = re.sub(escaped_depth, '', equipment_description)
            
        # Hapus kondisi yang sudah diekstrak
        if condition_result != "N/A":
            escaped_cond = re.escape(condition_result)
            equipment_description = re.sub(escaped_cond, '', equipment_description)

        # Bersihkan sisa spasi ganda & karakter yang tidak perlu
        equipment_description = re.sub(r'\s{2,}', ' ', equipment_description).strip()
        equipment_description = re.sub(r'^\s*[|,;.]\s*', '', equipment_description) # Buang delimiter di awal

        if not equipment_description:
            equipment_description = "N/A"

        return {
            "waktu_mulai": waktu_mulai,
            "waktu_akhir": waktu_akhir,
            "durasi_jam": durasi_jam,
            "peralatan_deskripsi": equipment_description,
            "interval_kedalaman": depth_interval,
            "kondisi_hasil": condition_result
        }

    def _extract_times(self, row: str) -> tuple:
        """Extract start and end times (HH:MM)"""
        time_pattern = r'\b(\d{1,2}:\d{2})\b'
        times = re.findall(time_pattern, row)
        return (times[0] if len(times) > 0 else "N/A", 
                times[1] if len(times) > 1 else "N/A")

    def _extract_duration(self, row: str) -> float:
        """Extract duration (float) followed by 'jam' or decimal number"""
        # Cari pola: "X.X jam", "X.0 jam", atau angka desimal di dekat waktu
        duration_pattern = r'(\d+\.?\d*)\s*(?:Jam|jam|hours?|hrs?)'
        match = re.search(duration_pattern, row, re.IGNORECASE)
        
        if match:
            return float(match.group(1))
        
        # Fallback: cari angka desimal di baris (biasanya durasi)
        dec_pattern = r'\b(\d+\.\d+)\b'
        dec_match = re.search(dec_pattern, row)
        return float(dec_match.group(1)) if dec_match else 0.0

    def _extract_depth_interval(self, row: str) -> str:
        """Extract the interval/kedalaman section specifically"""
        # Pola Regex untuk Kedalaman/Interval:
        # 1. F/ 611' TO 618'   (Menggunakan F/ dan TO)
        # 2. @ 689'            (Menggunakan @)
        # 3. 486' - 610'       (Menggunakan range dengan tanda -)
        # 4. 23 FT SAND FILL... (Frasa kedalaman spesifik)
        
        depth_patterns = [
            r'F\/\s*\d+[\'"]?\s*TO\s*\d+[\'"]?',  # F/ 611' TO 618'
            r'@\s*\d+[\'"]?\s*(?:FT|ft)?',       # @ 689'
            r'\d+[\'"]?\s*-\s*\d+[\'"]?\s*(?:FT|ft)?', # 486' - 610'
            r'\d+\s*FT\s+FILL',                  # 23 FT SAND FILL
            r'TO\s*SAND\s*@\s*\d+',              # TOS @ 618'
            r'INTERVAL\s*:\s*[\d\s\'"-]+'        # INTVL : 486' - 610'
        ]
        
        for pattern in depth_patterns:
            match = re.search(pattern, row, re.IGNORECASE)
            if match:
                return match.group(0).strip()
                
        return "N/A"

    def _extract_condition(self, row: str) -> str:
        """Extract specific condition/result statements"""
        condition_keywords = [
            r'PEKERJAAN TERHENTI.*',
            r'SAND PUMP NOT GO DOWN',
            r'NOT GO DOWN',
            r'MUD & SAND FORMATION',
            r'CLEAN',
            r'RE RUN',
            r'WATER\s*:\s*\d+%\s*,\s*OIL\s*:\s*\d+%\s*,\s*SEDIMENT\s*:\s*\d+%',
            r'IFL\s*:.*BBLS'
        ]
        
        for pattern in condition_keywords:
            match = re.search(pattern, row, re.IGNORECASE)
            if match:
                return match.group(0).strip()
                
        return "N/A"
        return equipment, depth, condition
