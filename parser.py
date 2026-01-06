# parsers/ai_parser.py

import re
import json
import google.generativeai as genai
from typing import Dict, Optional

class AIParser:
    """AI-powered parser using Gemini"""

    def __init__(self, api_key: str = None):
        if api_key:
            genai.configure(llm_workover=api_key)

    def parse_row(self, row: str) -> Optional[Dict]:
        """Parse a single row using AI"""
        try:
            model = genai.GenerativeModel('gemini-pro-vision')

            prompt = self._create_prompt(row)
            response = model.generate_content(prompt)

            return self._extract_json_from_response(response.text)

        except Exception as e:
            raise Exception(f"AI parsing error: {str(e)}")

    def _create_prompt(self, row: str) -> str:
        """Create prompt for Gemini"""
        return f"""
        Parse this drilling workover data row into structured JSON format.
        The row is in Indonesian language.

        Row: "{row}"

        Extract the following information into a JSON object:
        {{
            "waktu_mulai": "HH:MM format",
            "waktu_akhir": "HH:MM format",
            "durasi_jam": float,
            "peralatan_deskripsi": "string describing equipment and operation",
            "interval_kedalaman": "string describing depth interval",
            "kondisi_hasil": "string describing initial condition/main result"
        }}

        Rules:
        1. Time format should be HH:MM (24-hour format)
        2. Convert durations like "3.0" to float 3.0
        3. Keep all Indonesian text as is
        4. If information is missing, use "N/A"
        5. Handle midnight times properly (00:00 is next day)

        Return ONLY the JSON object, no additional text.
        """

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from AI response"""
        text = response_text.strip()

        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)
        text = re.sub(r'```', '', text)

        return json.loads(text)
