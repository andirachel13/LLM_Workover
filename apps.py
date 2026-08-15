# app.py

import streamlit as st
import os
import pandas as pd
from datetime import datetime
from config import Config
from data_processor import DataProcessor

def main():
    Config.init_session_state()
    st.set_page_config(**Config.PAGE_CONFIG)
    st.title("🛢️ Drilling Workover Data Processor")
    st.markdown("Proses data laporan harian kerja bor (workover) menjadi tabel terstruktur")
    render_sidebar()
    render_main_content()

def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        api_key_input = st.text_input("Kunci API Gemini (opsional):", type="password", placeholder="AIzaSy...", value=st.session_state.get("api_key", ""))
        
        if api_key_input and api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input
            st.success("✅ API key dikonfigurasi!")

        st.markdown("---")
        st.header("📋 Format Input")
        st.markdown(Config.INPUT_FORMAT_GUIDE)
        
        # Reset checkbox AI
        st.session_state.use_ai = st.checkbox("Gunakan AI untuk parsing", value=True)

def render_main_content():
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Input Data", "📊 Tabel Hasil", "📈 Analisis", "💾 Ekspor"])

    with tab1:
        render_input_tab()
    with tab2:
        render_table_tab()
    with tab3:
        render_analysis_tab()
    with tab4:
        render_export_tab()

def render_input_tab():
    st.subheader("Masukkan Data Workover")
    col1, col2 = st.columns([2, 1])

    with col1:
        raw_input = st.text_area("Tempel data workover mentah:", height=400, placeholder=Config.EXAMPLE_INPUT, value=st.session_state.get("raw_input", ""))
        st.session_state.raw_input = raw_input

        if st.button("🔄 Proses Data", type="primary", use_container_width=True):
            if raw_input.strip():
                with st.spinner("Memproses data..."):
                    # PAKSA RESET DATA LAMA
                    st.session_state.processed_data = []
                    
                    processor = DataProcessor(use_ai=st.session_state.use_ai, api_key=st.session_state.api_key)
                    processed = processor.process_raw_data(raw_input)
                    
                    # PAKSA BERSIHKAN DATA BARU SEBELUM SIMPAN
                    clean_data = []
                    for row in processed:
                        clean_row = {}
                        for k, v in row.items():
                            if isinstance(v, str):
                                v = v.replace(';', ' ').replace('|', ' ')
                                v = ' '.join(v.split()) # Hapus spasi ganda
                            clean_row[k] = v
                        clean_data.append(clean_row)

                    st.session_state.processed_data = clean_data
                    st.success(f"✅ {len(clean_data)} baris berhasil diproses!")
                    st.rerun()
            else:
                st.warning("Masukkan data terlebih dahulu!")

    with col2:
        st.markdown("**Contoh Data Valid:**")
        st.code(Config.EXAMPLE_CODE)

def render_table_tab():
    st.subheader("Tabel Data Terstruktur")
    if st.session_state.get("processed_data"):
        display_data_table()
        display_summary_stats()
    else:
        st.info("Belum ada data yang diproses.")

def display_data_table():
    data = st.session_state.processed_data
    if not data: return

    df = pd.DataFrame(data).fillna('')
    
    # Mapping kolom
    column_map = Config.COLUMN_MAPPING
    df = df.rename(columns=column_map)
    
    # Pastikan urutan kolom sesuai
    cols = ["Waktu Mulai", "Waktu Akhir", "Durasi (Jam)", "Peralatan Utama & Deskripsi Operasi", "Interval/Kedalaman Operasi", "Kondisi Awal/Hasil Utama"]
    df = df[[c for c in cols if c in df.columns]]

    # BERSIHKAN KARAKTER KOTOR LANGSUNG DI DATAFRAME
    for col in df.columns:
        if col != "Durasi (Jam)":
            df[col] = df[col].astype(str).str.replace(';', ' ').str.replace('|', ' ').str.replace('  ', ' ').str.strip()

    st.dataframe(df, use_container_width=True, height=600, hide_index=True)

def display_summary_stats():
    data = st.session_state.processed_data
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Operasi", len(data))
    with col2: st.metric("Total Durasi (Jam)", f"{sum(row.get('durasi_jam', 0) for row in data):.1f}")
    with col3: st.metric("Interval Kedalaman", len([r for r in data if r.get('interval_kedalaman') != 'N/A']))

def render_analysis_tab():
    st.subheader("Analisis Operasi")
    if st.session_state.get("processed_data"):
        st.info("Analisis sedang dalam pengembangan.")
    else:
        st.info("Belum ada data untuk dianalisis.")

def render_export_tab():
    st.subheader("Ekspor Data")
    if st.session_state.get("processed_data"):
        st.download_button("📥 Download CSV", data="", file_name="empty.csv", disabled=True)
        st.info("Fitur ekspor akan ditambahkan setelah data bersih.")
    else:
        st.info("Belum ada data untuk diekspor.")

if __name__ == "__main__":
    main()
