# visualizer.py

import plotly.graph_objects as go
import pandas as pd
import re
from typing import List, Dict

class WellVisualizer:
    """Generate visualizations from parsed well data"""

    def parse_depth_data(self, processed_data: List[Dict]) -> pd.DataFrame:
        """Parse depth interval strings into numeric Start and End"""
        depth_data = []
        for row in processed_data:
            interval = row.get('interval_kedalaman', 'N/A')
            if interval == 'N/A':
                continue
            
            # Coba ekstrak angka dari interval
            # Format: F/ 611' TO 618', @ 689', 486' - 610'
            numbers = re.findall(r'(\d+\.?\d*)', interval)
            if len(numbers) == 2:
                try:
                    depth_data.append({
                        'start_depth': float(numbers[0]),
                        'end_depth': float(numbers[1]),
                        'description': row.get('peralatan_deskripsi', '')[:50],
                        'duration': row.get('durasi_jam', 0)
                    })
                except ValueError:
                    continue
        return pd.DataFrame(depth_data)

    def create_well_schematic(self, processed_data: List[Dict]) -> go.Figure:
        """Create a vertical well schematic (Bar chart)"""
        df = self.parse_depth_data(processed_data)
        if df.empty:
            return go.Figure()

        fig = go.Figure()
        
        # Plot setiap interval sebagai batang vertikal
        for _, row in df.iterrows():
            start = row['start_depth']
            end = row['end_depth']
            
            fig.add_trace(go.Bar(
                x=[row['description']],
                y=[end - start],  # Tinggi batang = selisih kedalaman
                base=start,       # Posisi bawah batang
                name=f"{start} - {end}",
                text=[f"Durasi: {row['duration']} jam"],
                hovertemplate="<b>%{text}</b><br>Kedalaman: %{base:.1f} - %{y:.1f} FT<br>"
            ))

        # Layout styling agar terlihat seperti profil sumur
        fig.update_layout(
            title="Profil Pekerjaan Sumur (Kedalaman vs Interval)",
            yaxis_title="Kedalaman (FT)",
            xaxis_title="Operasi / Deskripsi",
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            yaxis=dict(autorange="reversed")  # Kedalaman dimulai dari atas turun ke bawah
        )
        return fig

    def create_metrics_dashboard(self, processed_data: List[Dict], historical_data: List[Dict] = None) -> Dict:
        """Generate key performance metrics and comparison"""
        if not processed_data:
            return {}
            
        total_duration = sum(r.get('durasi_jam', 0) for r in processed_data)
        
        # Hitung NPT (Non-Productive Time) - asumsi W/O, WAIT, STANDBY adalah NPT
        npt_duration = 0
        productive_duration = 0
        swab_runs = 0
        swab_duration = 0
        rig_up_count = 0
        rig_down_count = 0
        
        for row in processed_data:
            desc = row.get('peralatan_deskripsi', '').upper()
            dur = row.get('durasi_jam', 0)
            
            # Downtime (NPT)
            if any(k in desc for k in ['W/O', 'WAIT', 'STANDBY']):
                npt_duration += dur
            else:
                productive_duration += dur
                
            # Swabbing Speed
            if 'SWAB' in desc:
                swab_runs += 1
                swab_duration += dur
                
            # Rig Up vs Rig Down
            if 'RIG UP' in desc or 'N/U' in desc or 'M/U' in desc:
                rig_up_count += 1
            if 'RIG DOWN' in desc or 'N/D' in desc:
                rig_down_count += 1
                
        avg_swab_speed = swab_duration / swab_runs if swab_runs > 0 else 0
        
        # AI Prediction (Simulasi sederhana: rata-rata historis vs current)
        prediction = "N/A (Belum ada data historis)"
        if historical_data:
            avg_hist_dur = sum(r.get('durasi_jam', 0) for r in historical_data) / len(historical_data)
            if avg_hist_dur > 0:
                diff = total_duration - avg_hist_dur
                if diff > 0:
                    prediction = f"⚠️ Estimasi selesai {diff:.1f} jam lebih lambat dari rata-rata historis ({avg_hist_dur:.1f} jam)"
                else:
                    prediction = f"✅ Lebih cepat {abs(diff):.1f} jam dari rata-rata historis ({avg_hist_dur:.1f} jam)"
        
        return {
            "total_duration": total_duration,
            "productive_hours": productive_duration,
            "npt_hours": npt_duration,
            "npt_percentage": (npt_duration / total_duration * 100) if total_duration > 0 else 0,
            "avg_swab_speed": avg_swab_speed,
            "rig_up_down_ratio": (rig_up_count / rig_down_count) if rig_down_count > 0 else "N/A",
            "prediction": prediction
        }
