"""PDF report generation helpers for research datasets."""

import os
from fpdf import FPDF


class ResearchReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Research Data Processing Toolkit Report", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _add_section_title(pdf, title):
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, title, ln=True)
    pdf.ln(2)


def _add_text_block(pdf, text):
    pdf.set_font("Helvetica", size=10)
    for line in text.split("\n"):
        pdf.multi_cell(0, 6, line)
    pdf.ln(2)


def generate_pdf_report(dataset_name, cleaned_df, validation_report, analysis_report, plot_images, destination_path):
    pdf = ResearchReport()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    _add_section_title(pdf, "Dataset Summary")
    _add_text_block(pdf, f"Dataset: {dataset_name}\nRows: {len(cleaned_df)}\nColumns: {len(cleaned_df.columns)}")

    _add_section_title(pdf, "Validation Findings")
    if validation_report["invalid_cells"] or validation_report["anomalies"] or validation_report["range_warnings"]:
        for section, items in validation_report.items():
            if not items:
                continue
            _add_text_block(pdf, f"{section.replace('_', ' ').title()}")
            for item in items[:4]:
                _add_text_block(pdf, str(item))
    else:
        _add_text_block(pdf, "No validation issues detected.")

    _add_section_title(pdf, "Analysis Highlights")
    if analysis_report.get("trend_analysis"):
        for item in analysis_report["trend_analysis"][:4]:
            _add_text_block(pdf, f"{item['column']} trend is {item['direction']} (avg change {item['average_change']:.3f})")
    else:
        _add_text_block(pdf, "Trend analysis does not contain numeric feature changes.")

    if plot_images:
        for image in plot_images[:3]:
            if os.path.exists(image):
                pdf.add_page()
                pdf.image(image, x=15, y=35, w=180)

    pdf.output(destination_path)
