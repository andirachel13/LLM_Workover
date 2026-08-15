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
            raise Exception(f"AI parsing error: {str(e)}")

    def _create_prompt(self, row: str) -> str:
        return f"""
        Parse this drilling workover data row into a JSON object.
        Row: "{row}"

        Return a valid JSON object with EXACTLY these keys:
        {{
            "waktu_mulai": "HH:MM format",
            "waktu_akhir": "HH:MM format",
            "durasi_jam": float,
            "peralatan_deskripsi": "string describing equipment",
            "interval_kedalaman": "string describing depth",
            "kondisi_hasil": "string describing condition/result"
        }}

        CRITICAL RULES FOR OUTPUT (STRICT):
        1. DO NOT use semicolons (;) or pipes (|) ANYWHERE in the strings.
        2. USE ONLY spaces, dots (.), and commas (,) if necessary.
        3. If information is missing, use "N/A" instead of empty string.
        4. Return ONLY the JSON object. NO explanations, NO markdown formatting (like ```json).
        """

    def _extract_json_from_response(self, response_text: str) -> Dict:
        text = response_text.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        text = re.sub(r'```', '', text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx+1]
                data = json.loads(text)
            else:
                raise ValueError("Gagal mengekstrak JSON dari respon AI")

        # PAKSA BERSIHKAN DATA
        for key in data:
            if isinstance(data[key], str):
                data[key] = data[key].replace(';', ' ')
                data[key] = data[key].replace('|', ' ')
                data[key] = re.sub(r'\s{2,}', ' ', data[key]).strip()
                
        return data
