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
            print(f"AI Fallback: {e}")
            return None

    def _create_prompt(self, row: str) -> str:
        return f"""
        Convert this drilling workover row into a JSON object.
        Row: "{row}"

        You MUST return a JSON with exactly these keys:
        - "waktu_mulai": "HH:MM"
        - "waktu_akhir": "HH:MM"
        - "durasi_jam": float
        - "peralatan_deskripsi": "Equipment and action descriptions"
        - "interval_kedalaman": "Depth intervals (e.g., F/ 611' TO 618' or @ 600' RT)"
        - "kondisi_hasil": "Conditions or results (e.g., SAND PUMP NOT GO DOWN, MUD & SAND FORMATION)"

        CRITICAL RULES:
        1. NO ';' and NO '|' inside strings.
        2. Return ONLY raw JSON. No explanations, no markdown, no code blocks.
        """

    def _extract_json(self, text: str) -> Dict:
        text = text.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        text = re.sub(r'```', '', text)

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
        else:
            return {}

        try:
            data = json.loads(json_str)
        except:
            return {}

        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v.replace(';', ' ').replace('|', ' ').strip()
        return data
