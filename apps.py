# app.py

import streamlit as st
import os
import pandas as pd
from config import Config
from data_processor import DataProcessor

# Setup halaman
st.set_page_config(page_title="Drilling Workover Data Processor", layout="wide")

def init_session():
    if "processed_data" not in st.session_state: st.session_state.processed_data = []
    if "raw_input" not in st.session_state: st.session_state.raw_input = ""
    if "api_key" not in st.session_state: st.session_state.api_key = ""
    if "use_ai" not in st.session_state: st.session_state.use_ai = True

def main():
    init_session()

    st.title("🛢️ Drilling Workover Data Processor")
    st.markdown("Proses data laporan harian kerja bor (workover) menjadi tabel terstruktur")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        
        # Ambil API Key dari Secrets/Env jika ada
        default_key = st.secrets.get("llm_workover", os.getenv("llm_workover", ""))
        if not st.session_state.api_key and default_key:
            st.session_state.api_key = default_key

        api_key_input = st.text_input(
            "Kunci API Gemini (Opsional):", 
            type="password", 
            value=st.session_state.api_key,
            placeholder="AIzaSy..."
        )
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input

        st.session_state.use_ai = st.checkbox("Gunakan AI untuk parsing", value=st.session_state.use_ai)
        
        st.markdown("---")
        st.header("📋 Format Input")
        st.markdown("`WaktuMulai WaktuAkhir Durasi Deskripsi...`")
        st.code("06:00 09:00 3.0\nLanjutkan BAILING OF SAND (B.O.S.)\nL/D 3-3/4\" SAND PUMP.\nB.O.S F/ 611' TO 618'\nPekerjaan terhenti")

    # Tabs (Kembalikan 4 tab)
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Input Data", "📊 Tabel Hasil", "📈 Analisis", "💾 Ekspor"])

    with tab1:
        st.subheader("Masukkan Data Workover")
        raw_input = st.text_area(
            "Tempel data mentah:", height=400, 
            placeholder="06:00 09:00 3.0 ...", 
            value=st.session_state.raw_input
        )
        st.session_state.raw_input = raw_input
        
        if st.button("🔄 Proses Data", type="primary", use_container_width=True):
            if raw_input.strip():
                with st.spinner("Memproses data..."):
                    processor = DataProcessor(
                        use_ai=st.session_state.use_ai, 
                        api_key=st.session_state.api_key
                    )
                    processed = processor.process_raw_data(raw_input)
                    
                    # Bersihkan data akhir sebelum simpan
                    clean_data = []
                    for row in processed:
                        clean_row = {}
                        for k, v in row.items():
                            if isinstance(v, str):
                                v = v.replace(';', ' ').replace('|', ' ')
                            clean_row[k] = v
                        clean_data.append(clean_row)
                    
                    st.session_state.processed_data = clean_data
                    st.success(f"✅ {len(clean_data)} baris berhasil diproses!")
                    st.rerun()
            else:
                st.warning("Data masih kosong!")

    with tab2:
        st.subheader("Tabel Data Terstruktur")
        if st.session_state.processed_data:
            df = pd.DataFrame(st.session_state.processed_data).fillna('')
            df = df.rename(columns=Config.COLUMN_MAPPING)
            
            # Bersihkan karakter di DataFrame
            for col in df.columns:
                if col != "Durasi (Jam)":
                    df[col] = df[col].astype(str).str.replace(';', ' ').str.replace('|', ' ')
            
            st.dataframe(df, use_container_width=True, height=500, hide_index=True)
            
            # Statistik
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Total Baris", len(processed))
            with c2: st.metric("Total Durasi (Jam)", f"{df['Durasi (Jam)'].sum():.1f}")
            with c3: st.metric("AI Digunakan", "Ya" if st.session_state.use_ai and st.session_state.api_key else "Tidak")
        else:
            st.info("Belum ada data yang diproses.")

    with tab3:
        st.subheader("Analisis Operasi")
        if st.session_state.processed_data:
            st.info("📊 Modul analisis sedang dalam pengembangan lanjutan.")
        else:
            st.info("Belum ada data.")

    with tab4:
        st.subheader("Ekspor Data")
        if st.session_state.processed_data:
            csv = pd.DataFrame(st.session_state.processed_data).to_csv(index=False)
            st.download_button("📥 Download CSV", data=csv, file_name="workover_data.csv", mime="text/csv")
        else:
            st.info("Belum ada data.")

if __name__ == "__main__":
    main()
