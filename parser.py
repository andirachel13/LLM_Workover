# parser.py

import re
import json
import google.generativeai as genai
from typing import Dict, Optional

class AIParser:
    def __init__(self, api_key: str = None):
        if api_key:
            genai.configure(api_key=api_key)

    def parse_row(self, row: str) -> Optional[Dict]:
        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = self._create_prompt(row)
            response = model.generate_content(prompt)
            return self._extract_json(response.text)
        except Exception as e:
            print(f"AI Error: {e}")
            return None

    def _create_prompt(self, row: str) -> str:
        """Membuat prompt yang memaksa AI mengembalikan JSON yang valid"""
        return f"""
        Parse this drilling workover data row into a JSON object.
        Row: "{row}"

        You MUST return a SINGLE, VALID JSON object with these exact 6 keys:
        - "waktu_mulai": string HH:MM format
        - "waktu_akhir": string HH:MM format
        - "durasi_jam": float number
        - "peralatan_deskripsi": string (describe the equipment or action)
        - "interval_kedalaman": string (look for depth like F/ 611' TO 618' or @ 689')
        - "kondisi_hasil": string (look for condition like SAND PUMP NOT GO DOWN, MUD & SAND, CLEAN, or N/A)

        CRITICAL RULES (FAILURE WILL CAUSE ERROR):
        1. DO NOT use ';' or '|' characters anywhere in the strings. Use spaces instead.
        2. DO NOT write any explanation, text, markdown, or code blocks. ONLY the raw JSON object.
        3. Example output: {{"waktu_mulai": "06:00", "waktu_akhir": "10:00", "durasi_jam": 4.0, "peralatan_deskripsi": "TGSM TOPIC BAILING OF SAND", "interval_kedalaman": "F/ 611' TO 618'", "kondisi_hasil": "SAND PUMP NOT GO DOWN"}}
        """

    def _extract_json(self, text: str) -> Dict:
        """Fungsi pengaman untuk mengambil JSON murni dari respon AI"""
        text = text.strip()

        # 1. Hapus markdown (```json ... ```)
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        text = re.sub(r'```', '', text)

        # 2. Cari tanda kurung kurawal pertama dan terakhir secara brute-force
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and start < end:
            json_str = text[start:end+1]
        else:
            # Jika tidak ada kurung kurawal, kembalikan kosong agar memicu fallback
            return {}

        # 3. Load JSON dan bersihkan karakter sisa
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return {}

        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v.replace(';', ' ').replace('|', ' ').strip()
        return data
