# app.py

import streamlit as st
from datetime import datetime

from config import Config
from data_processor import DataProcessor
from analyzer import DataAnalyzer
from csv_exporter import CSVExporter
#from excel_exporter import ExcelExporter
#from json_exporter import JSONExporter

def configure_gemini(api_key):
    """Configure Gemini API"""
    try:
        import google.generativeai as genai
        api_key = st.secrets.get("llm_workover", os.getenv("llm_workover"))
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Error configuring Gemini: {str(e)}")
        return False

def main():
    # Initialize configuration
    Config.init_session_state()

    # Page setup
    st.set_page_config(**Config.PAGE_CONFIG)
    st.title("🛢️ Drilling Workover Data Processor")
    st.markdown("Proses data laporan harian kerja bor (workover) menjadi tabel terstruktur")

    # Sidebar
    render_sidebar()

    # Main content tabs
    render_main_content()

def render_sidebar():
    """Render sidebar configuration"""
    with st.sidebar:
        st.header("⚙️ Konfigurasi")

        api_key_input = st.text_input(
            "Kunci API Gemini (opsional):",
            type="password",
            placeholder="AIzaSy...",
            value=st.session_state.api_key
        )

        if api_key_input and api_key_input != st.session_state.api_key:
            if configure_gemini(api_key_input):
                st.session_state.api_key = api_key_input
                st.success("✅ API key dikonfigurasi!")

        st.markdown("---")
        st.header("📋 Format Input")
        st.markdown(Config.INPUT_FORMAT_GUIDE)

        st.session_state.use_ai = st.checkbox("Gunakan AI untuk parsing", value=True)

def render_main_content():
    """Render main content tabs"""
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
    """Render input data tab"""
    st.subheader("Masukkan Data Workover")

    col1, col2 = st.columns([2, 1])

    with col1:
        raw_input = st.text_area(
            "Tempel data workover mentah:",
            height=400,
            placeholder=Config.EXAMPLE_INPUT,
            value=st.session_state.raw_input
        )

        st.session_state.raw_input = raw_input

        if st.button("🔄 Proses Data", type="primary", use_container_width=True):
            process_data(raw_input)

    with col2:
        st.markdown("**Contoh Data Valid:**")
        st.code(Config.EXAMPLE_CODE)
        render_tips()

def process_data(raw_input):
    """Process the input data"""
    if raw_input.strip():
        with st.spinner("Memproses data..."):
            processor = DataProcessor(
                use_ai=st.session_state.use_ai,
                api_key=st.session_state.api_key
            )

            processed = processor.process_raw_data(raw_input)
            st.session_state.processed_data = processed

            st.success(f"✅ {len(processed)} baris berhasil diproses!")
            st.rerun()
    else:
        st.warning("Masukkan data terlebih dahulu!")

def render_table_tab():
    """Render table results tab"""
    st.subheader("Tabel Data Terstruktur")

    if st.session_state.processed_data:
        display_data_table()
        display_summary_stats()
    else:
        st.info("Belum ada data yang diproses.")

def display_data_table():
    """Display the processed data table"""
    exporter = CSVExporter()
    df = exporter._format_dataframe(st.session_state.processed_data)

    st.dataframe(
        df,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config=Config.TABLE_COLUMN_CONFIG
    )

def display_summary_stats():
    """Display summary statistics"""
    analyzer = DataAnalyzer()
    totals = analyzer.calculate_totals(st.session_state.processed_data)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Operasi", totals["total_operations"])
    with col2:
        st.metric("Total Durasi (Jam)", f"{totals['total_duration_hours']:.1f}")
    with col3:
        st.metric("Interval Kedalaman", len(totals["depth_intervals"]))

def render_analysis_tab():
    """Render analysis tab"""
    st.subheader("Analisis Operasi")

    if st.session_state.processed_data:
        analyzer = DataAnalyzer()

        # Get analysis results
        totals = analyzer.calculate_totals(st.session_state.processed_data)
        efficiency = analyzer.analyze_efficiency(st.session_state.processed_data)

        # Display analysis
        display_operation_distribution(totals)
        display_efficiency_analysis(efficiency)

    else:
        st.info("Belum ada data untuk dianalisis.")

def render_export_tab():
    """Render export tab"""
    st.subheader("Ekspor Data")

    if st.session_state.processed_data:
        display_export_options()
    else:
        st.info("Belum ada data untuk diekspor.")

def display_export_options():
    """Display export options"""
    col1, col2, col3 = st.columns(3)

    with col1:
        csv_exporter = CSVExporter()
        csv_data, filename = csv_exporter.export(st.session_state.processed_data)

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        excel_exporter = ExcelExporter()
        excel_data, filename = excel_exporter.export(st.session_state.processed_data)

        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col3:
        json_exporter = JSONExporter()
        json_data, filename = json_exporter.export(st.session_state.processed_data)

        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )

# Add missing functions
def render_tips():
    """Render tips section"""
    st.markdown("---")
    st.markdown("**Tips:**")
    st.markdown(Config.TIPS)

def display_operation_distribution(totals):
    """Display operation distribution"""
    st.markdown("### 📊 Distribusi Jenis Operasi")
    op_counts = totals["operation_counts"]

    cols = st.columns(min(4, len(op_counts)))
    for idx, (op_type, count) in enumerate(op_counts.items()):
        if idx < 4:
            with cols[idx]:
                st.metric(op_type, count)

def display_efficiency_analysis(efficiency):
    """Display efficiency analysis"""
    st.markdown("### ⚠️ Analisis Efisiensi")

    if efficiency["long_operations"]:
        st.warning(f"**Operasi Panjang**: {len(efficiency['long_operations'])} operasi > 4 jam")
        for op in efficiency["long_operations"][:3]:
            st.write(f"- Baris {op['row']}: {op['operation']} ({op['duration']} jam)")
    else:
        st.success("Tidak ada operasi yang terlalu panjang (>4 jam)")

    total_time = efficiency["productive_time"] + efficiency["waiting_time"]
    if total_time > 0:
        efficiency_pct = (efficiency["productive_time"] / total_time) * 100
        st.metric("Efisiensi Produktif", f"{efficiency_pct:.1f}%")

# Update Config class with additional constants
Config.INPUT_FORMAT_GUIDE = """**Format yang didukung:**
WaktuMulai WaktuAkhir Durasi Peralatan&Deskripsi Interval/Kedalaman Kondisi/Hasil
06:00 09:00 3.0 Lanjutkan BAILING... B.O.S F/ 611'... Pekerjaan terhenti..."""

Config.EXAMPLE_INPUT = """Contoh:
06:0009:003.0Lanjutkan BAILING OF SAND (B.O.S.). L/D 3-3/4" SAND PUMP.B.O.S F/ 611' TO 618'Pekerjaan terhenti (sand pump not go down).
09:0010:001.0M/U & RIH W/ 3-1/2" M.SHOE ON 23 JTS 3.5" TBG.Tagged @ 618' (TOS)Kedalaman awal Top of Sand (TOS).
"""

Config.EXAMPLE_CODE = """06:00 09:00 3.0
Lanjutkan BAILING OF SAND (B.O.S.)
L/D 3-3/4" SAND PUMP.
B.O.S F/ 611' TO 618'
Pekerjaan terhenti"""

Config.TIPS = """1. Tempel data langsung dari laporan
2. Pastikan format waktu konsisten
3. Gunakan AI untuk parsing kompleks
4. Periksa hasil parsing di tab berikutnya"""

Config.TABLE_COLUMN_CONFIG = {
    "Waktu Mulai": st.column_config.TextColumn(width="small"),
    "Waktu Akhir": st.column_config.TextColumn(width="small"),
    "Durasi (Jam)": st.column_config.NumberColumn(width="small", format="%.1f"),
    "Peralatan Utama & Deskripsi Operasi": st.column_config.TextColumn(width="large"),
    "Interval/Kedalaman Operasi": st.column_config.TextColumn(width="medium"),
    "Kondisi Awal/Hasil Utama": st.column_config.TextColumn(width="large")
}

if __name__ == "__main__":
    main()
