# app.py (Updated Level 2)

import streamlit as st
import os
import pandas as pd
import re
from typing import Dict
from datetime import datetime, timedelta
from config import Config
from data_processor import DataProcessor
from analytics import DataAnalyzer
from csv_export import CSVExporter
from visualizer import WellVisualizer  # <--- IMPOR MODUL BARU

st.set_page_config(page_title="Drilling Workover Data Processor", layout="wide")

def init_session():
    if "processed_data" not in st.session_state: st.session_state.processed_data = []
    if "historical_data" not in st.session_state: st.session_state.historical_data = [] # Database sederhana
    if "raw_input" not in st.session_state: st.session_state.raw_input = ""
    if "api_key" not in st.session_state: st.session_state.api_key = ""
    if "use_ai" not in st.session_state: st.session_state.use_ai = True
    if "use_metric" not in st.session_state: st.session_state.use_metric = False
    if "filter_phase" not in st.session_state: st.session_state.filter_phase = "Semua"

def classify_phase(desc: str) -> str:
    desc = desc.upper()
    if 'RIG UP' in desc or 'N/U' in desc or 'M/U' in desc: return 'Rig Up & Make Up'
    if 'RIH' in desc: return 'Running In Hole'
    if 'POH' in desc: return 'Pulling Out Hole'
    if 'SWAB' in desc: return 'Swabbing'
    if 'BAILING' in desc or 'B.O.S' in desc: return 'Bailing'
    if 'W/O' in desc or 'WAIT' in desc: return 'Waiting / Delay'
    return 'Lainnya'

def convert_depth_unit(val: str, to_metric: bool) -> str:
    if val == "N/A" or not val: return "N/A"
    match = re.search(r'(\d+\.?\d*)\s*[\'"]?\s*(?:FT)?', val, re.IGNORECASE)
    if match:
        num = float(match.group(1))
        if to_metric:
            return val.replace(match.group(1), f"{num * 0.3048:.1f}") + " (m)"
        return val
    return val

def detect_anomalies(row: Dict) -> Dict:
    anomalies = []
    durasi = row.get('durasi_jam', 0)
    kedalaman = row.get('interval_kedalaman', 'N/A')
    desc = row.get('peralatan_deskripsi', '').upper()
    
    if durasi > 12.0 and kedalaman != 'N/A' and not any(k in desc for k in ['W/O', 'WAIT']):
        anomalies.append("Durasi panjang tanpa perubahan kedalaman")
    
    if 'WATER' in desc or 'OIL' in desc:
        percents = re.findall(r'(\d+)%', desc)
        if percents:
            for p in percents:
                if int(p) > 100: anomalies.append("Persentase > 100%")
                if int(p) < 0: anomalies.append("Persentase negatif")
                    
    row['anomalies'] = "; ".join(anomalies) if anomalies else "Tidak Ada"
    return row

def calculate_end_time(start_time_str: str, duration_hours: float) -> str:
    try:
        start_parts = start_time_str.split(':')
        start_hour = int(start_parts[0])
        start_minute = int(start_parts[1]) if len(start_parts) > 1 else 0
        
        total_minutes = duration_hours * 60
        add_hours = int(total_minutes // 60)
        add_minutes = int(total_minutes % 60)
        
        total_start_minutes = (start_hour * 60) + start_minute
        total_end_minutes = total_start_minutes + (add_hours * 60) + add_minutes
        
        end_hour = (total_end_minutes // 60) % 24
        end_minute = total_end_minutes % 60
        
        return f"{end_hour:02d}:{end_minute:02d}"
    except Exception:
        return "N/A"

def main():
    init_session()
    st.title("🛢️ DrillStruct AI")
    st.markdown("Pengolahan data workover berbasis AI & NLP dengan Analitik Lanjutan")

    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        default_key = st.secrets.get("llm_workover", os.getenv("llm_workover", ""))
        if not st.session_state.api_key and default_key:
            st.session_state.api_key = default_key

        api_key_input = st.text_input("Kunci API Gemini:", type="password", value=st.session_state.api_key, placeholder="AIzaSy...", key="api_key_input")
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input

        st.session_state.use_ai = st.checkbox("Gunakan AI untuk parsing", key="use_ai_checkbox", value=st.session_state.use_ai)
        st.session_state.use_metric = st.checkbox("Konversi ke Satuan Metrik (Meter)", key="use_metric_checkbox", value=st.session_state.use_metric)
        
        st.markdown("---")
        st.header("📋 Format Input")
        st.code("06:00 10:00 4.0 TGSM TOPIC... F/ 611' TO 618' (SAND PUMP NOT GO DOWN)")

    tab1, tab2, tab3, tab4 = st.tabs(["📥 Input Data", "📊 Tabel Hasil", "📈 Dashboard Performa", "💾 Ekspor"])

    with tab1:
        st.subheader("Masukkan Data Workover")
        raw_input = st.text_area("Tempel data mentah:", height=400, placeholder="06:00 10:00 4.0 ...", value=st.session_state.raw_input)
        st.session_state.raw_input = raw_input
        
        if st.button("🔄 Proses Data", type="primary", use_container_width=True):
            if raw_input.strip():
                with st.spinner("Memproses data..."):
                    processor = DataProcessor(use_ai=st.session_state.use_ai, api_key=st.session_state.api_key)
                    processed = processor.process_raw_data(raw_input)
                    
                    for row in processed:
                        if row.get('waktu_mulai') != 'N/A' and row.get('durasi_jam', 0) > 0:
                            row['waktu_akhir'] = calculate_end_time(row['waktu_mulai'], row['durasi_jam'])
                        else:
                            row['waktu_akhir'] = 'N/A'
                        
                        row['fase_pekerjaan'] = classify_phase(row.get('peralatan_deskripsi', ''))
                        row = detect_anomalies(row)
                        
                    st.session_state.processed_data = processed
                    st.success(f"✅ {len(processed)} baris berhasil diproses!")
                    st.rerun()
            else:
                st.warning("Data masih kosong!")

    with tab2:
        st.subheader("Tabel Data Terstruktur")
        if st.session_state.processed_data:
            df = pd.DataFrame(st.session_state.processed_data).fillna('')
            
            phases = ["Semua"] + sorted(df['fase_pekerjaan'].unique().tolist())
            st.session_state.filter_phase = st.selectbox("Filter berdasarkan Fase Pekerjaan:", phases)
            
            if st.session_state.filter_phase != "Semua":
                df = df[df['fase_pekerjaan'] == st.session_state.filter_phase]
            
            if st.session_state.use_metric:
                df['interval_kedalaman'] = df['interval_kedalaman'].apply(lambda x: convert_depth_unit(x, True))
            
            df = df.rename(columns=Config.COLUMN_MAPPING)
            
            for col in df.columns:
                if col not in ["Durasi (Jam)", "Total Baris"]:
                    df[col] = df[col].astype(str).str.replace(';', ' ').str.replace('|', ' ').str.strip()

            if 'anomalies' in df.columns:
                df_display = df.drop(columns=['anomalies'])
            else:
                df_display = df

            st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Baris", len(df))
            with c2: st.metric("Total Durasi (Jam)", f"{df['Durasi (Jam)'].sum():.1f}")
            with c3: st.metric("AI Digunakan", "Ya" if st.session_state.use_ai and st.session_state.api_key else "Tidak")
            
            anomalies_count = len(df[df['anomalies'].astype(str) != "Tidak Ada"])
            with c4: st.metric("⚠️ Data Anomali", anomalies_count)
            
            if anomalies_count > 0:
                st.warning(f"Terdeteksi {anomalies_count} data dengan anomali.")
        else:
            st.info("Belum ada data yang diproses.")

    with tab3:
        st.subheader("📈 Dashboard Performa & Analitik Lanjutan")
        if st.session_state.processed_data:
            visualizer = WellVisualizer()
            
            # 1. Metrik Kunci (Metrics Dashboard)
            metrics = visualizer.create_metrics_dashboard(
                st.session_state.processed_data, 
                st.session_state.historical_data  # Bandingkan dengan data historis
            )
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Jam Operasi", f"{metrics['total_duration']:.1f} jam")
            with col2:
                st.metric("🟢 Jam Produktif", f"{metrics['productive_hours']:.1f} jam")
            with col3:
                st.metric("🔴 NPT (Downtime)", f"{metrics['npt_hours']:.1f} jam ({metrics['npt_percentage']:.1f}%)")
            with col4:
                st.metric("Rig Up/Down Ratio", metrics['rig_up_down_ratio'])
                
            st.markdown("---")
            
            # 2. Prediksi Durasi (AI Forecasting)
            st.subheader("🤖 Analisis Prediktif")
            st.info(metrics['prediction'])
            
            # Simpan data saat ini ke historis untuk prediksi selanjutnya
            if st.button("Simpan ke Database Historis"):
                st.session_state.historical_data.extend(st.session_state.processed_data)
                st.success("Data berhasil disimpan ke database historis!")
                st.rerun()
            
            # 3. Visualisasi Peta Sumur (Well Schematic)
            st.markdown("---")
            st.subheader("🛢️ Peta Profil Sumur (Schematic)")
            fig = visualizer.create_well_schematic(st.session_state.processed_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # 4. Analisis Downtime (NPT Analysis)
            st.markdown("---")
            st.subheader("⏳ Analisis Downtime")
            
            if metrics['npt_hours'] > 0:
                st.warning(f"⚠️ **Total Downtime (NPT):** {metrics['npt_hours']:.1f} jam ({metrics['npt_percentage']:.1f}% dari total operasi).")
                st.markdown("**Rekomendasi:**")
                if metrics['npt_percentage'] > 20:
                    st.error("🚨 NPT > 20%. Segera evaluasi penyebab (cari pola W/O / Stuck Pipe).")
                elif metrics['npt_percentage'] > 10:
                    st.warning("⚠️ NPT 10-20%. Optimalkan jadwal operasi untuk mengurangi waktu tunggu.")
                else:
                    st.success("✅ NPT < 10%. Efisiensi operasi sudah baik.")
            else:
                st.success("Tidak ada Downtime (NPT) yang terdeteksi pada data ini.")
                
        else:
            st.info("Belum ada data untuk dianalisis. Silakan proses data di tab Input Data.")

    with tab4:
        st.subheader("Ekspor Data")
        if st.session_state.processed_data:
            exporter = CSVExporter()
            csv_data, filename = exporter.export(st.session_state.processed_data)
            st.download_button(label="📥 Download CSV", data=csv_data, file_name=filename, mime="text/csv")
            
            # Ekspor ke Historis
            st.markdown("---")
            if st.session_state.historical_data:
                hist_csv = pd.DataFrame(st.session_state.historical_data).to_csv(index=False)
                st.download_button(label="📥 Download Database Historis", data=hist_csv, file_name="historical_database.csv", mime="text/csv")
        else:
            st.info("Belum ada data.")

if __name__ == "__main__":
    main()
