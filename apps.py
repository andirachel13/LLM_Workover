# app.py

import streamlit as st
import pandas as pd
from config import Config
from data_processor import DataProcessor

def main():
    # Inisialisasi state
    if "processed_data" not in st.session_state: st.session_state.processed_data = []
    if "raw_input" not in st.session_state: st.session_state.raw_input = ""
    if "api_key" not in st.session_state: st.session_state.api_key = ""
    if "use_ai" not in st.session_state: st.session_state.use_ai = True

    st.set_page_config(page_title="Drilling Workover", layout="wide")
    st.title("🛢️ Drilling Workover Data Processor")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        st.session_state.api_key = st.text_input("Kunci API Gemini:", type="password", placeholder="AIzaSy...", value=st.session_state.api_key)
        st.session_state.use_ai = st.checkbox("Gunakan AI untuk parsing", value=st.session_state.use_ai)
        st.markdown("---")
        st.header("📋 Format Input")
        st.markdown("Contoh: `06:00 09:00 3.0 Lanjutkan B.O.S... Pekerjaan terhenti`")
        st.code("06:00 09:00 3.0\nLanjutkan BAILING OF SAND (B.O.S.)\nL/D 3-3/4\" SAND PUMP.\nB.O.S F/ 611' TO 618'\nPekerjaan terhenti")

    # Tabs
    tab1, tab2 = st.tabs(["📥 Input Data", "📊 Tabel Hasil"])
    
    with tab1:
        st.subheader("Masukkan Data Workover")
        raw_input = st.text_area("Tempel data:", height=400, placeholder="06:00 09:00 3.0...", value=st.session_state.raw_input)
        st.session_state.raw_input = raw_input
        
        if st.button("🔄 Proses Data", type="primary"):
            if raw_input.strip():
                processor = DataProcessor(use_ai=st.session_state.use_ai, api_key=st.session_state.api_key)
                processed = processor.process_raw_data(raw_input)
                
                # Sanitasi data sebelum disimpan
                clean_data = []
                for row in processed:
                    clean_row = {k: (str(v).replace(';', ' ').replace('|', ' ').strip() if isinstance(v, str) else v) for k, v in row.items()}
                    clean_data.append(clean_row)
                
                st.session_state.processed_data = clean_data
                st.success(f"✅ {len(clean_data)} baris diproses!")
                st.rerun()
    
    with tab2:
        st.subheader("Tabel Data Terstruktur")
        if st.session_state.processed_data:
            df = pd.DataFrame(st.session_state.processed_data).fillna('')
            df = df.rename(columns={
                "waktu_mulai": "Waktu Mulai", "waktu_akhir": "Waktu Akhir", "durasi_jam": "Durasi (Jam)",
                "peralatan_deskripsi": "Peralatan", "interval_kedalaman": "Interval", "kondisi_hasil": "Kondisi"
            })
            # Final Guard: Bersihkan dataframe 1x lagi
            for col in df.columns:
                if col != "Durasi (Jam)":
                    df[col] = df[col].astype(str).str.replace(';', ' ').str.replace('|', ' ').str.replace('  ', ' ')
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data.")

if __name__ == "__main__":
    main()
