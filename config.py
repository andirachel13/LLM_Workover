# config.py

import streamlit as st

class Config:
    PAGE_CONFIG = {"page_title": "Drilling Workover Data Processor", "page_icon": "🛢️", "layout": "wide"}
    
    COLUMN_MAPPING = {
        "waktu_mulai": "Waktu Mulai",
        "waktu_akhir": "Waktu Akhir",
        "durasi_jam": "Durasi (Jam)",
        "peralatan_deskripsi": "Peralatan Utama & Deskripsi Operasi",
        "interval_kedalaman": "Interval/Kedalaman Operasi",
        "kondisi_hasil": "Kondisi Awal/Hasil Utama"
    }

    INPUT_FORMAT_GUIDE = "WaktuMulai WaktuAkhir Durasi Peralatan&Deskripsi Interval/Kedalaman Kondisi/Hasil"
    EXAMPLE_CODE = "06:00 09:00 3.0 Lanjutkan BAILING OF SAND (B.O.S.) L/D 3-3/4\" SAND PUMP B.O.S F/ 611' TO 618' Pekerjaan terhenti"

    @staticmethod
    def init_session_state():
        if "processed_data" not in st.session_state: st.session_state.processed_data = []
        if "raw_input" not in st.session_state: st.session_state.raw_input = ""
        if "api_key" not in st.session_state: st.session_state.api_key = ""
        if "use_ai" not in st.session_state: st.session_state.use_ai = False
