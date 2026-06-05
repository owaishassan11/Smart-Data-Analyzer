"""Visualization helpers using Plotly and Matplotlib."""

import pandas as pd
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import tempfile


def _save_figure_as_png(fig):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(temp_file.name, bbox_inches="tight")
    plt.close(fig)
    return temp_file.name


def build_visualization_html(df, return_images=False):
    html_fragments = []
    image_paths = []
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if numeric_cols:
        fig_line = px.line(df[numeric_cols].reset_index(), title="Trend overview for numeric columns")
        html_fragments.append(pio.to_html(fig_line, include_plotlyjs=False, full_html=False))

        fig_hist = px.histogram(df, x=numeric_cols[0], title=f"Distribution of {numeric_cols[0]}")
        html_fragments.append(pio.to_html(fig_hist, include_plotlyjs=False, full_html=False))

        fig_heat = px.imshow(df[numeric_cols].corr(), text_auto=True, title="Correlation heatmap")
        html_fragments.append(pio.to_html(fig_heat, include_plotlyjs=False, full_html=False))

        if return_images:
            fig1, ax1 = plt.subplots(figsize=(8, 4))
            df[numeric_cols].plot(ax=ax1)
            ax1.set_title("Trend overview for numeric columns")
            ax1.set_xlabel("Index")
            ax1.set_ylabel("Value")
            image_paths.append(_save_figure_as_png(fig1))

            fig2, ax2 = plt.subplots(figsize=(8, 4))
            ax2.hist(df[numeric_cols[0]].dropna(), bins=12, color="#5b9bd5", edgecolor="#2f4f4f")
            ax2.set_title(f"Distribution of {numeric_cols[0]}")
            ax2.set_xlabel(numeric_cols[0])
            ax2.set_ylabel("Count")
            image_paths.append(_save_figure_as_png(fig2))

            fig3, ax3 = plt.subplots(figsize=(8, 4))
            heat_data = df[numeric_cols].corr()
            im = ax3.imshow(heat_data, cmap="coolwarm", aspect="auto")
            ax3.set_xticks(range(len(numeric_cols)))
            ax3.set_yticks(range(len(numeric_cols)))
            ax3.set_xticklabels(numeric_cols, rotation=45, ha="right")
            ax3.set_yticklabels(numeric_cols)
            ax3.set_title("Correlation heatmap")
            plt.colorbar(im, ax=ax3)
            image_paths.append(_save_figure_as_png(fig3))
    else:
        fig = px.bar(x=df.columns, y=df.iloc[0].fillna(0), title="Dataset snapshot")
        html_fragments.append(pio.to_html(fig, include_plotlyjs=False, full_html=False))
        if return_images:
            fig4, ax4 = plt.subplots(figsize=(8, 4))
            ax4.bar(df.columns, df.iloc[0].fillna(0), color="#4a90e2")
            ax4.set_title("Dataset snapshot")
            ax4.set_xticklabels(df.columns, rotation=45, ha="right")
            image_paths.append(_save_figure_as_png(fig4))

    if return_images:
        return image_paths
    return "\n".join(html_fragments)
