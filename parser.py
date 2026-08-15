# parser.py

import re
import json
import google.generativeai as genai
from typing import Dict, Optional

class AIParser:
    """AI-powered parser using Gemini"""

    def __init__(self, api_key: str = None):
        if api_key:
            genai.configure(api_key=api_key)

    def parse_row(self, row: str) -> Optional[Dict]:
        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = self._create_prompt(row)
            response = model.generate_content(prompt)
            return self._extract_json_from_response(response.text)
        except Exception as e:
            # Tangkap error dan kembalikan None agar tidak crash
            print(f"AI parsing fallback due to: {e}")
            return None

    def _create_prompt(self, row: str) -> str:
        return f"""
        Parse this drilling workover data row into a JSON object.
        Row: "{row}"

        Return a valid JSON object with EXACTLY these keys:
        {{
            "waktu_mulai": "HH:MM",
            "waktu_akhir": "HH:MM",
            "durasi_jam": float,
            "peralatan_deskripsi": "string describing the equipment or operation",
            "interval_kedalaman": "string describing the depth interval (e.g., F/ 611' TO 618')",
            "kondisi_hasil": "string describing the result or condition"
        }}

        VERY IMPORTANT RULES:
        1. DO NOT use semicolons (;) or pipes (|) anywhere in your strings.
        2. If a value is missing, use "N/A".
        3. Return ONLY the JSON object. No markdown, no code blocks (no ```json or ```), no explanation.
        """

    def _extract_json_from_response(self, response_text: str) -> Dict:
        text = response_text.strip()
        
        # 1. Bersihkan markdown JSON jika ada
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        text = re.sub(r'```', '', text)

        # 2. Load JSON dengan aman
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Jika AI gagal membuat JSON, ambil kurung kurawal terakhir
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx+1]
                data = json.loads(text)
            else:
                # Jika benar-benar gagal, lempar error ke atas
                raise ValueError("AI output is not valid JSON")

        # 3. PAKSA BERSIHKAN DATA DARI TANDA ; DAN |
        for key in data:
            if isinstance(data[key], str):
                data[key] = data[key].replace(';', ' ')
                data[key] = data[key].replace('|', ' ')
                data[key] = re.sub(r'\s{2,}', ' ', data[key]).strip()
                
        return data
