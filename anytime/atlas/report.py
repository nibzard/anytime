"""Report generation for atlas benchmarks."""

from typing import Any
from pathlib import Path

from anytime.atlas.runner import Metrics


class ReportBuilder:
    """Build markdown reports from atlas results."""

    def __init__(self, title: str = "Atlas Benchmark Report"):
        self.title = title
        self.sections: list[str] = []

    def add_header(self, level: int, text: str) -> None:
        """Add a markdown header."""
        prefix = "#" * level
        self.sections.append(f"{prefix} {text}\n")

    def add_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Add a markdown table."""
        # Header
        self.sections.append("| " + " | ".join(headers) + " |")
        # Separator
        self.sections.append("|" + "|".join(["---" for _ in headers]) + "|")
        # Rows
        for row in rows:
            self.sections.append("| " + " | ".join(row) + " |")
        self.sections.append("")

    def add_text(self, text: str) -> None:
        """Add a paragraph of text."""
        self.sections.append(text + "\n")

    def add_metrics(self, label: str, metrics: Metrics) -> None:
        """Add metrics as a formatted section."""
        self.add_header(3, label)
        d = metrics.to_dict()
        self.sections.append(f"- **Coverage**: {d['coverage']:.3f}\n")
        self.sections.append(f"- **Final Coverage**: {d['final_coverage']:.3f}\n")
        self.sections.append(f"- **Type I Error**: {d['type_i_error']:.3f}\n")
        self.sections.append(f"- **Power**: {d['power']:.3f}\n")
        self.sections.append(f"- **Avg Width**: {d['avg_width']:.4f}\n")
        self.sections.append(f"- **Median Stop Time**: {d['median_stop_time']:.1f}\n")
        self.sections.append(f"- **Avg Runtime**: {d['avg_runtime']:.4f}s\n")

    def build(self) -> str:
        """Build the complete markdown report."""
        report = f"# {self.title}\n\n"
        report += "\n".join(self.sections)
        return report

    def save(self, path: str) -> None:
        """Save report to file."""
        Path(path).write_text(self.build())


def generate_comparison_report(
    results: dict[str, dict[str, Metrics]],
    output_path: str,
) -> None:
    """Generate a method comparison report.

    Args:
        results: Nested dict {method_name: {scenario_name: Metrics}}
        output_path: Where to save the report
    """
    builder = ReportBuilder("Atlas Method Comparison")

    builder.add_header(2, "Summary")
    builder.add_text("This report compares confidence sequence methods across scenarios.")

    # Build comparison table
    methods = list(results.keys())
    scenarios = list(next(iter(results.values())).keys())

    builder.add_header(2, "Coverage Comparison")
    headers = ["Scenario"] + methods
    rows = []
    for scenario in scenarios:
        row = [scenario]
        for method in methods:
            m = results[method].get(scenario)
            if m:
                cov = f"{m.coverage:.3f}"
                row.append(cov if cov != "1.000" else "**1.000**" if float(cov) >= 0.95 else cov)
            else:
                row.append("N/A")
        rows.append(row)
    builder.add_table(headers, rows)

    builder.add_header(2, "Final Coverage Comparison")
    rows = []
    for scenario in scenarios:
        row = [scenario]
        for method in methods:
            m = results[method].get(scenario)
            row.append(f"{m.final_coverage:.3f}" if m else "N/A")
        rows.append(row)
    builder.add_table(headers, rows)

    builder.add_header(2, "Width Comparison (smaller is better)")
    rows = []
    for scenario in scenarios:
        row = [scenario]
        for method in methods:
            m = results[method].get(scenario)
            row.append(f"{m.avg_width:.4f}" if m else "N/A")
        rows.append(row)
    builder.add_table(headers, rows)

    builder.add_header(2, "Detailed Metrics")
    for method in methods:
        builder.add_header(3, method)
        for scenario in scenarios:
            m = results[method].get(scenario)
            if m:
                builder.add_metrics(f"{scenario}", m)

    builder.save(output_path)
