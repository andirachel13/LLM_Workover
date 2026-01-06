# analytics/analyzer.py

from typing import Dict, List
from ..config import Config

class DataAnalyzer:
    """Analyze drilling workover data"""

    def __init__(self):
        self.config = Config

    def calculate_totals(self, processed_data: List[Dict]) -> Dict:
        """Calculate summary statistics"""
        total_duration = sum(row.get('durasi_jam', 0) for row in processed_data)
        operation_counts = self._count_operations(processed_data)
        depth_intervals = self._extract_depth_intervals(processed_data)

        return {
            "total_duration_hours": total_duration,
            "operation_counts": operation_counts,
            "depth_intervals": depth_intervals,
            "total_operations": len(processed_data)
        }

    def _count_operations(self, data: List[Dict]) -> Dict:
        """Count operations by type"""
        operation_counts = {}

        for row in data:
            desc = row.get('peralatan_deskripsi', '').upper()
            op_type = self._classify_operation(desc)

            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1

        return operation_counts

    def _classify_operation(self, description: str) -> str:
        """Classify operation based on keywords"""
        for op_type, keywords in self.config.OPERATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description:
                    return op_type.title()

        return "Other"

    def _extract_depth_intervals(self, data: List[Dict]) -> List[str]:
        """Extract all depth intervals"""
        depth_ranges = []
        for row in data:
            depth_str = row.get('interval_kedalaman', '')
            if depth_str and depth_str != 'N/A':
                depth_ranges.append(depth_str)

        return depth_ranges

    def analyze_efficiency(self, data: List[Dict]) -> Dict:
        """Analyze operational efficiency"""
        insights = {
            "long_operations": [],
            "waiting_time": 0,
            "productive_time": 0
        }

        for i, row in enumerate(data):
            duration = row.get('durasi_jam', 0)
            desc = row.get('peralatan_deskripsi', '').upper()

            # Check for long operations
            if duration > 4.0:
                insights["long_operations"].append({
                    "row": i + 1,
                    "duration": duration,
                    "operation": desc[:50]
                })

            # Track waiting vs productive time
            if any(kw in desc for kw in ['W/O', 'WAIT', 'STANDBY']):
                insights["waiting_time"] += duration
            else:
                insights["productive_time"] += duration

        return insights
