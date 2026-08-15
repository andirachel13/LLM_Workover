# apps.py

import streamlit as st
import os
import pandas as pd
from config import Config
from data_processor import DataProcessor
from analytics import DataAnalyzer
from csv_export import CSVExporter

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

    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        default_key = st.secrets.get("llm_workover", os.getenv("llm_workover", ""))
        if not st.session_state.api_key and default_key:
            st.session_state.api_key = default_key

        api_key_input = st.text_input("Kunci API Gemini (Opsional):", type="password", value=st.session_state.api_key, placeholder="AIzaSy...")
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input

        st.session_state.use_ai = st.checkbox("Gunakan AI untuk parsing", value=st.session_state.use_ai)
        
        st.markdown("---")
        st.header("📋 Format Input")
        st.markdown("Contoh format:")
        st.code("06:00 09:00 3.0\nLanjutkan BAILING OF SAND (B.O.S.)\nL/D 3-3/4\" SAND PUMP.\nB.O.S F/ 611' TO 618'\nPekerjaan terhenti")

    tab1, tab2, tab3, tab4 = st.tabs(["📥 Input Data", "📊 Tabel Hasil", "📈 Analisis", "💾 Ekspor"])

    with tab1:
        st.subheader("Masukkan Data Workover")
        raw_input = st.text_area("Tempel data mentah:", height=400, placeholder="06:00 09:00 3.0 ...", value=st.session_state.raw_input)
        st.session_state.raw_input = raw_input
        
        if st.button("🔄 Proses Data", type="primary", use_container_width=True):
            if raw_input.strip():
                with st.spinner("Memproses data..."):
                    processor = DataProcessor(use_ai=st.session_state.use_ai, api_key=st.session_state.api_key)
                    processed = processor.process_raw_data(raw_input)
                    
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
            for col in df.columns:
                if col != "Durasi (Jam)":
                    df[col] = df[col].astype(str).str.replace(';', ' ').str.replace('|', ' ')
            st.dataframe(df, use_container_width=True, height=500, hide_index=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Total Baris", len(st.session_state.processed_data))
            with c2: st.metric("Total Durasi (Jam)", f"{df['Durasi (Jam)'].sum():.1f}")
            with c3: st.metric("AI Digunakan", "Ya" if st.session_state.use_ai and st.session_state.api_key else "Tidak")
        else:
            st.info("Belum ada data yang diproses.")

    with tab3:
        st.subheader("Analisis Operasi")
        if st.session_state.processed_data:
            analyzer = DataAnalyzer()
            totals = analyzer.calculate_totals(st.session_state.processed_data)
            efficiency = analyzer.analyze_efficiency(st.session_state.processed_data)

            # --- LAYOUT SESUAI GAMBAR ANDA ---
            # 1. Distribusi Operasi (Angka besar)
            st.markdown("### 📊 Distribusi Jenis Operasi")
            op_counts = totals.get("operation_counts", {})
            cols = st.columns(len(op_counts) if len(op_counts) > 0 else 1)
            for i, (op, count) in enumerate(op_counts.items()):
                with cols[i]:
                    st.metric(label=op, value=count)

            # 2. Analisis Efisiensi
            st.markdown("### ⚠️ Analisis Efisiensi")
            if efficiency["long_operations"]:
                st.warning(f"**Operasi Panjang**: {len(efficiency['long_operations'])} operasi > 4 jam")
                for op in efficiency["long_operations"]:
                    st.write(f"- Baris {op['row']}: {op['operation']} ({op['duration']} jam)")
            else:
                st.success("Tidak ada operasi yang terlalu panjang (>4 jam)")

            # 3. Efisiensi Produktif
            total_time = efficiency["productive_time"] + efficiency["waiting_time"]
            if total_time > 0:
                efficiency_pct = (efficiency["productive_time"] / total_time) * 100
                st.metric(label="Efisiensi Produktif", value=f"{efficiency_pct:.1f}%")
            # -----------------------------------
        else:
            st.info("Belum ada data untuk dianalisis.")

    with tab4:
        st.subheader("Ekspor Data")
        if st.session_state.processed_data:
            exporter = CSVExporter()
            csv_data, filename = exporter.export(st.session_state.processed_data)
            st.download_button(label="📥 Download CSV", data=csv_data, file_name=filename, mime="text/csv")
        else:
            st.info("Belum ada data untuk diekspor.")

if __name__ == "__main__":
    main()
