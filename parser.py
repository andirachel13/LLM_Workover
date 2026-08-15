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
            prompt = f"""
            Parse this drilling row into JSON: 
            "{row}"
            Return JSON with keys: 
            "waktu_mulai", "waktu_akhir", "durasi_jam", "peralatan_deskripsi", "interval_kedalaman", "kondisi_hasil"
            STRICT RULES: NO semicolons (;), NO pipes (|) anywhere in the text strings. 
            Use commas and periods only. If missing, "N/A". JSON only, no markdown.
            """
            response = model.generate_content(prompt)
            return self._extract_json(response.text)
        except Exception:
            return None

    def _extract_json(self, text: str) -> Dict:
        # Hapus markdown
        text = re.sub(r'```json\s*', '', text).strip()
        text = re.sub(r'\s*```', '', text).strip()
        
        try:
            data = json.loads(text)
        except:
            # Ambil kurung kurawal terakhir sebagai upaya terakhir
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                data = json.loads(text[start:end+1])
            else:
                return {}
        
        # Bersihkan ; dan |
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v.replace(';', ' ').replace('|', ' ').strip()
        return data
