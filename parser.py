# parsers/ai_parser.py
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
        Parse this drilling workover data row into a CLEAN JSON object.
        Row: "{row}"

        Return a JSON object with EXACTLY these keys (use Indonesian for content):
        {{
            "waktu_mulai": "HH:MM",
            "waktu_akhir": "HH:MM",  
            "durasi_jam": float,
            "peralatan_deskripsi": "clean text without any ; or | characters",
            "interval_kedalaman": "depth string like F/ 611' TO 618'",
            "kondisi_hasil": "condition result"
        }}

        RULES (STRICT):
        1. REMOVE all semicolons (;) and pipes (|) from all strings.
        2. DO NOT add extra punctuation like commas in the middle of sentences.
        3. Return ONLY the JSON object. No markdown, no explanations, no code blocks.
        """

    def _extract_json_from_response(self, response_text: str) -> Dict:
        text = response_text.strip()
        
        # Bersihkan markdown JSON jika ada
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        text = re.sub(r'```', '', text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Jika JSON gagal di-load, coba ambil kurung kurawal pertama dan terakhir
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx+1]
                data = json.loads(text)
            else:
                raise ValueError("Gagal mengekstrak JSON dari respon AI")

        # Bersihkan data dari karakter aneh hasil AI
        for key in data:
            if isinstance(data[key], str):
                data[key] = data[key].replace(';', ' ').replace('|', ' ').strip()
        
        return data
