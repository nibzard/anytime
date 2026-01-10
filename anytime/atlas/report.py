"""Report generation for atlas benchmarks."""

from typing import Any
from pathlib import Path

from anytime.atlas.runner import Metrics


def _spec_kind(spec: object) -> str:
    if isinstance(spec, dict):
        return spec.get("kind", "bounded")
    return getattr(spec, "kind", "bounded")


def _spec_alpha(spec: object) -> float | None:
    if isinstance(spec, dict):
        return spec.get("alpha")
    return getattr(spec, "alpha", None)


def _report_alpha(specs: dict[str, Any] | None) -> float | None:
    if not specs:
        return None
    for spec in specs.values():
        if spec is None:
            continue
        alpha = _spec_alpha(spec)
        if alpha is not None:
            return alpha
    return None


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
        if d.get('evalue_decision_rate', 0) > 0:
            self.sections.append(f"- **E-value Decision Rate**: {d['evalue_decision_rate']:.3f}\n")
        if d.get('naive_peeking_error', 0) > 0:
            self.sections.append(f"- **Naive Peeking Error**: {d['naive_peeking_error']:.3f} *(inflated!)*\n")

    def add_plot(self, image_path: str, caption: str = "") -> None:
        """Add an embedded plot with optional caption.

        Args:
            image_path: Relative or absolute path to the image file
            caption: Optional caption text to display below the image
        """
        # For markdown, use relative path if possible
        path = Path(image_path)
        if path.exists():
            # Use just the filename if it's in the same directory
            display_path = path.name
        else:
            display_path = str(path)

        self.sections.append(f"![{caption or 'plot'}]({display_path})\n")
        if caption:
            self.sections.append(f"*{caption}*\n")

    def add_code_block(self, code: str, language: str = "") -> None:
        """Add a code block."""
        self.sections.append(f"```{language}\n{code}\n```\n")

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
    specs: dict[str, Any] | None = None,
) -> None:
    """Generate a method comparison report.

    Args:
        results: Nested dict {method_name: {scenario_name: Metrics}}
        output_path: Where to save the report
        specs: Optional dict with 'one_sample' and/or 'two_sample' StreamSpecs
               for recommender audit
    """
    builder = ReportBuilder("Atlas Method Comparison")

    builder.add_header(2, "Summary")
    builder.add_text("This report compares confidence sequence methods across scenarios.")

    # Build comparison table
    methods = list(results.keys())
    scenarios = list(next(iter(results.values())).keys())
    alpha = _report_alpha(specs)
    coverage_target = 1.0 - alpha if alpha is not None else 0.95
    type_i_target = alpha if alpha is not None else 0.05

    builder.add_header(2, "Coverage Comparison (Anytime)")
    headers = ["Scenario"] + methods
    rows = []
    for scenario in scenarios:
        row = [scenario]
        for method in methods:
            m = results[method].get(scenario)
            if m:
                cov = f"{m.coverage:.3f}"
                # Bold coverage at or above nominal level
                formatted = f"**{cov}**" if float(cov) >= coverage_target else cov
                row.append(formatted)
            else:
                row.append("N/A")
        rows.append(row)
    builder.add_table(headers, rows)

    builder.add_header(2, "Type I Error (should be ≤ α for null scenarios)")
    rows = []
    for scenario in scenarios:
        row = [scenario]
        for method in methods:
            m = results[method].get(scenario)
            if m:
                t1e = f"{m.type_i_error:.3f}"
                # Bold Type I error at or below nominal alpha
                formatted = f"**{t1e}**" if float(t1e) <= type_i_target else t1e
                row.append(formatted)
            else:
                row.append("N/A")
        rows.append(row)
    builder.add_table(headers, rows)

    builder.add_header(2, "Power (higher is better, for alt scenarios)")
    rows = []
    for scenario in scenarios:
        row = [scenario]
        for method in methods:
            m = results[method].get(scenario)
            if m:
                pow_val = f"{m.power:.3f}"
                row.append(pow_val)
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
            if m:
                width = f"{m.avg_width:.4f}"
                row.append(width)
            else:
                row.append("N/A")
        rows.append(row)
    builder.add_table(headers, rows)

    # Add recommender audit table if specs provided
    if specs:
        builder.add_header(2, "Recommender Audit")
        builder.add_text("Default method choices for each spec type:")

        from anytime.recommend import recommend_cs, recommend_ab

        recomm_results = []
        for spec_type, spec in specs.items():
            if spec_type == "one_sample" and spec:
                try:
                    rec = recommend_cs(spec)
                    method_name = rec.method.__name__
                    recomm_results.append([spec_type, _spec_kind(spec), method_name, rec.reason])
                except Exception:
                    recomm_results.append([spec_type, _spec_kind(spec), "ERROR", "Failed to recommend"])
            elif spec_type == "two_sample" and spec:
                try:
                    rec = recommend_ab(spec)
                    method_name = rec.method.__name__
                    recomm_results.append([spec_type, _spec_kind(spec), method_name, rec.reason])
                except Exception:
                    recomm_results.append([spec_type, _spec_kind(spec), "ERROR", "Failed to recommend"])

        builder.add_table(["Spec Type", "Data Kind", "Recommended Method", "Reason"], recomm_results)

    builder.add_header(2, "Detailed Metrics")
    for method in methods:
        builder.add_header(3, method)
        for scenario in scenarios:
            m = results[method].get(scenario)
            if m:
                builder.add_metrics(f"{scenario}", m)

    builder.save(output_path)
