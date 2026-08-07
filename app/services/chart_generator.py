"""
Automated Chart Generator Service.
Generates both Matplotlib PNG chart images AND Plotly interactive JSON figure specifications
(data & layout) with dropdown selectors, rich hover templates, zoom/pan controls, and export tools.
"""

import os
import uuid
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.config import Config


def generate_charts(df: pd.DataFrame, correlation_info: dict = None, datetime_info: dict = None, file_id: str = None) -> tuple:
    if not file_id:
        file_id = uuid.uuid4().hex[:10]

    charts_dir = os.path.join(Config.CHARTS_FOLDER, file_id)
    os.makedirs(charts_dir, exist_ok=True)

    charts_meta = {}
    plotly_specs = {}

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # 1. Histograms (Plotly & Matplotlib)
    if numeric_cols:
        try:
            # Matplotlib PNG
            fig_cols = min(3, len(numeric_cols))
            fig_rows = (len(numeric_cols) + fig_cols - 1) // fig_cols
            fig, axes = plt.subplots(fig_rows, fig_cols, figsize=(5 * fig_cols, 4 * fig_rows))
            axes = axes.flatten() if len(numeric_cols) > 1 else [axes]

            for idx, col in enumerate(numeric_cols):
                sns.histplot(df[col].dropna(), kde=True, ax=axes[idx], color="#4f46e5")
                axes[idx].set_title(f"Distribution of {col}", fontsize=11, fontweight="bold")
                axes[idx].set_xlabel(col)

            for idx in range(len(numeric_cols), len(axes)):
                axes[idx].set_visible(False)

            plt.tight_layout()
            hist_path = os.path.join(charts_dir, "histograms.png")
            plt.savefig(hist_path, dpi=120)
            plt.close()

            charts_meta["histograms"] = {
                "url": f"/static/charts/{file_id}/histograms.png",
                "title": "Numerical Feature Distributions",
            }

            # Interactive Plotly Histogram with Column Selector Dropdown
            first_num = numeric_cols[0]
            fig_hist = px.histogram(df, x=first_num, marginal="rug")
            fig_hist.update_traces(marker_color="#4f46e5", opacity=0.85)

            dropdown_buttons = [
                dict(
                    method="update",
                    label=str(col),
                    args=[{"x": [df[col].dropna()]}, {"title": {"text": f"Distribution Analysis ({col})", "x": 0.0, "xanchor": "left"}, "xaxis": {"title": col}}],
                )
                for col in numeric_cols
            ]

            fig_hist.update_layout(
                title=dict(text=f"Distribution Analysis ({first_num})", x=0.0, xanchor="left"),
                updatemenus=[
                    dict(
                        buttons=dropdown_buttons,
                        direction="down",
                        showactive=True,
                        x=1.0, xanchor="right",
                        y=1.22, yanchor="top"
                    )
                ],
                margin=dict(l=40, r=40, t=75, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["histogram"] = json.loads(fig_hist.to_json())

        except Exception:
            plt.close()

    # 2. Boxplots & Violin Plots (Plotly & Matplotlib)
    if numeric_cols:
        try:
            plt.figure(figsize=(10, 5))
            sns.boxplot(data=df[numeric_cols], palette="Set2")
            plt.title("Numerical Features Boxplot (Outlier Overview)", fontsize=12, fontweight="bold")
            plt.xticks(rotation=45)
            plt.tight_layout()
            box_path = os.path.join(charts_dir, "boxplots.png")
            plt.savefig(box_path, dpi=120)
            plt.close()

            charts_meta["boxplots"] = {
                "url": f"/static/charts/{file_id}/boxplots.png",
                "title": "Numerical Outlier Boxplots",
            }

            # Interactive Plotly Boxplot
            first_num = numeric_cols[0]
            fig_box = px.box(df, y=first_num, points="outliers")
            fig_box.update_traces(marker_color="#ef4444", boxmean=True)

            box_dropdowns = [
                dict(
                    method="update",
                    label=str(col),
                    args=[{"y": [df[col].dropna()]}, {"title": {"text": f"Outlier & Boxplot Analysis ({col})", "x": 0.0, "xanchor": "left"}, "yaxis": {"title": col}}],
                )
                for col in numeric_cols
            ]

            fig_box.update_layout(
                title=dict(text=f"Outlier & Boxplot Analysis ({first_num})", x=0.0, xanchor="left"),
                updatemenus=[
                    dict(
                        buttons=box_dropdowns,
                        direction="down",
                        showactive=True,
                        x=1.0, xanchor="right",
                        y=1.22, yanchor="top"
                    )
                ],
                margin=dict(l=40, r=40, t=75, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["boxplot"] = json.loads(fig_box.to_json())

            # Interactive Plotly Violin Plot
            fig_v = px.violin(df, y=first_num, box=True, points="all")
            fig_v.update_traces(marker_color="#10b981", fillColor="#10b981", opacity=0.8)

            violin_dropdowns = [
                dict(
                    method="update",
                    label=str(col),
                    args=[{"y": [df[col].dropna()]}, {"title": {"text": f"Density & Violin Kernel Shape ({col})", "x": 0.0, "xanchor": "left"}, "yaxis": {"title": col}}],
                )
                for col in numeric_cols
            ]

            fig_v.update_layout(
                title=dict(text=f"Density & Violin Kernel Shape ({first_num})", x=0.0, xanchor="left"),
                updatemenus=[
                    dict(
                        buttons=violin_dropdowns,
                        direction="down",
                        showactive=True,
                        x=1.0, xanchor="right",
                        y=1.22, yanchor="top"
                    )
                ],
                margin=dict(l=40, r=40, t=75, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["violin_plot"] = json.loads(fig_v.to_json())

        except Exception:
            plt.close()

    # 3. Correlation Heatmap (Plotly & Matplotlib)
    if len(numeric_cols) >= 2:
        try:
            corr_matrix = df[numeric_cols].corr(method="pearson")

            plt.figure(figsize=(8, 6))
            sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
            plt.title("Pearson Correlation Heatmap", fontsize=12, fontweight="bold")
            plt.tight_layout()
            heatmap_path = os.path.join(charts_dir, "correlation_heatmap.png")
            plt.savefig(heatmap_path, dpi=120)
            plt.close()

            charts_meta["correlation_heatmap"] = {
                "url": f"/static/charts/{file_id}/correlation_heatmap.png",
                "title": "Pearson Correlation Heatmap",
            }

            # Interactive Plotly Heatmap with Hover Text
            hover_text = [
                [f"{row} vs {col}: r = {corr_matrix.loc[row, col]:.3f}" for col in corr_matrix.columns]
                for row in corr_matrix.index
            ]

            fig_corr = go.Figure(
                data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale="Viridis",
                    zmin=-1, zmax=1,
                    text=corr_matrix.values.round(2),
                    texttemplate="%{text}",
                    textfont={"size": 11},
                    hoverinfo="text",
                    hovertext=hover_text
                )
            )

            fig_corr.update_layout(
                title="Interactive Correlation Matrix (Hover for Exact Pearson r)",
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["correlation_heatmap"] = json.loads(fig_corr.to_json())

        except Exception:
            plt.close()

    # 4. Missing Value Plot (Plotly & Matplotlib)
    missing_series = df.isna().sum()
    if missing_series.sum() > 0:
        try:
            plt.figure(figsize=(8, 4))
            missing_pct = (missing_series[missing_series > 0] / len(df)) * 100
            missing_pct.sort_values(ascending=False).plot(kind="bar", color="#ef4444")
            plt.title("Missing Values Percentage per Column", fontsize=12, fontweight="bold")
            plt.ylabel("Missing %")
            plt.tight_layout()
            missing_path = os.path.join(charts_dir, "missing_values.png")
            plt.savefig(missing_path, dpi=120)
            plt.close()

            charts_meta["missing_values"] = {
                "url": f"/static/charts/{file_id}/missing_values.png",
                "title": "Missing Values per Column",
            }

            # Interactive Plotly Missing Plot
            missing_df = pd.DataFrame({
                "Column": missing_pct.index,
                "Missing_Count": [missing_series[c] for c in missing_pct.index],
                "Missing_Percentage": missing_pct.values.round(2)
            })

            fig_m = px.bar(
                missing_df,
                x="Column", y="Missing_Percentage",
                text="Missing_Percentage",
                title="Interactive Missing Values Percentage per Column",
                color="Missing_Percentage",
                color_continuous_scale="Reds"
            )
            fig_m.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_m.update_layout(
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["missing_values"] = json.loads(fig_m.to_json())

        except Exception:
            plt.close()

    # 5. Count Plot & Pie Chart & Pareto Chart for Categorical Features
    if cat_cols:
        try:
            top_cat_col = cat_cols[0]
            cat_counts = df[top_cat_col].value_counts().head(10).reset_index()
            cat_counts.columns = [top_cat_col, "Count"]

            plt.figure(figsize=(8, 4))
            sns.barplot(data=cat_counts, x=top_cat_col, y="Count", palette="viridis")
            plt.title(f"Top Categories for {top_cat_col}", fontsize=12, fontweight="bold")
            plt.xticks(rotation=45)
            plt.tight_layout()
            count_path = os.path.join(charts_dir, "categorical_countplot.png")
            plt.savefig(count_path, dpi=120)
            plt.close()

            charts_meta["categorical_countplot"] = {
                "url": f"/static/charts/{file_id}/categorical_countplot.png",
                "title": f"Top Categories for {top_cat_col}",
            }

            # Interactive Plotly Count Plot
            fig_c = px.bar(cat_counts, x=top_cat_col, y="Count", title=f"Interactive Category Counts ({top_cat_col})", color="Count", color_continuous_scale="Viridis")
            fig_c.update_layout(
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["countplot"] = json.loads(fig_c.to_json())

            # Interactive Plotly Pie Chart
            fig_p = px.pie(cat_counts.head(8), names=top_cat_col, values="Count", title=f"Interactive Pie Chart ({top_cat_col})", hole=0.3)
            fig_p.update_traces(textinfo="percent+label", hovertemplate=f"Category: %{{label}}<br>Count: %{{value}}<br>Share: %{{percent}}<extra></extra>")
            fig_p.update_layout(
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["pie_chart"] = json.loads(fig_p.to_json())

            # Interactive Plotly Pareto Chart (Bar + Cumulative Line)
            cat_sorted = df[top_cat_col].value_counts().reset_index()
            cat_sorted.columns = ["Category", "Frequency"]
            cat_sorted["Cumulative_Pct"] = (cat_sorted["Frequency"].cumsum() / cat_sorted["Frequency"].sum()) * 100

            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=cat_sorted["Category"], y=cat_sorted["Frequency"], name="Frequency", marker_color="#3b82f6"))
            fig_pareto.add_trace(go.Scatter(x=cat_sorted["Category"], y=cat_sorted["Cumulative_Pct"], name="Cumulative %", yaxis="y2", mode="lines+markers", line=dict(color="#f59e0b", width=2.5)))
            fig_pareto.update_layout(
                title=f"Pareto 80/20 Category Distribution ({top_cat_col})",
                yaxis=dict(title="Frequency"),
                yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["pareto_chart"] = json.loads(fig_pareto.to_json())

        except Exception:
            plt.close()

    # 6. Scatter Plot for Strongest Correlation Pair
    if correlation_info and correlation_info.get("strong_pairs"):
        try:
            top_pair = correlation_info["strong_pairs"][0]
            col_a, col_b = top_pair["column_a"], top_pair["column_b"]
            plt.figure(figsize=(7, 5))
            sns.regplot(data=df, x=col_a, y=col_b, color="#8b5cf6", scatter_kws={"alpha": 0.6})
            plt.title(f"Scatter Plot: {col_a} vs {col_b} (r={top_pair['correlation']:.2f})", fontsize=12, fontweight="bold")
            plt.tight_layout()
            scatter_path = os.path.join(charts_dir, "scatter_plot.png")
            plt.savefig(scatter_path, dpi=120)
            plt.close()

            charts_meta["scatter_plot"] = {
                "url": f"/static/charts/{file_id}/scatter_plot.png",
                "title": f"Top Correlation Scatter Plot ({col_a} vs {col_b})",
            }

            # Interactive Plotly Scatter
            fig_s = px.scatter(df, x=col_a, y=col_b, trendline="ols", title=f"Interactive Scatter Plot: {col_a} vs {col_b} (r={top_pair['correlation']:.2f})")
            fig_s.update_traces(marker=dict(size=8, opacity=0.7, color="#6366f1"))
            fig_s.update_layout(
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["scatter_plot"] = json.loads(fig_s.to_json())

        except Exception:
            plt.close()

    # 7. Datetime Analysis Visual Charts (Plotly)
    if datetime_info and datetime_info.get("datetime_detected") and datetime_info.get("per_column"):
        try:
            first_dt_col = datetime_info["columns"][0]
            dt_data = datetime_info["per_column"][first_dt_col]

            # Year Bar Chart
            if dt_data.get("records_per_year"):
                yr_df = pd.DataFrame([{"Year": str(k), "Records": v} for k, v in dt_data["records_per_year"].items()])
                fig_yr = px.bar(yr_df, x="Year", y="Records", title=f"Records per Year ({first_dt_col})", color="Records", color_continuous_scale="Blues")
                fig_yr.update_layout(margin=dict(l=40, r=40, t=50, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color="#0f172a"))
                plotly_specs["datetime_year"] = json.loads(fig_yr.to_json())

            # Month Bar Chart
            if dt_data.get("records_per_month"):
                mo_df = pd.DataFrame([{"Month": str(k), "Records": v} for k, v in dt_data["records_per_month"].items()])
                fig_mo = px.bar(mo_df, x="Month", y="Records", title=f"Records per Month ({first_dt_col})", color="Records", color_continuous_scale="Teal")
                fig_mo.update_layout(margin=dict(l=40, r=40, t=50, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color="#0f172a"))
                plotly_specs["datetime_month"] = json.loads(fig_mo.to_json())

            # Weekday Bar Chart
            if dt_data.get("records_per_weekday"):
                wk_df = pd.DataFrame([{"Weekday": str(k), "Records": v} for k, v in dt_data["records_per_weekday"].items()])
                fig_wk = px.bar(wk_df, x="Weekday", y="Records", title=f"Records per Weekday ({first_dt_col})", color="Records", color_continuous_scale="Purples")
                fig_wk.update_layout(margin=dict(l=40, r=40, t=50, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color="#0f172a"))
                plotly_specs["datetime_weekday"] = json.loads(fig_wk.to_json())

        except Exception:
            pass

    # 8. Data Quality Radar / Spider Benchmark Chart
    try:
        total_cells = df.shape[0] * df.shape[1]
        missing_count = int(df.isna().sum().sum())
        completeness = max(0, min(100, round((1 - missing_count / max(1, total_cells)) * 100, 1)))

        dup_rows = int(df.duplicated().sum())
        uniqueness = max(0, min(100, round((1 - dup_rows / max(1, len(df))) * 100, 1)))

        outlier_count = 0
        if numeric_cols:
            for col in numeric_cols:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    outlier_count += int(((df[col] < (q1 - 1.5 * iqr)) | (df[col] > (q3 + 1.5 * iqr))).sum())
        outlier_health = max(0, min(100, round((1 - outlier_count / max(1, total_cells)) * 100, 1)))
        overall_score = round((completeness * 0.4 + uniqueness * 0.3 + outlier_health * 0.3), 1)

        radar_df = pd.DataFrame(dict(
            r=[completeness, uniqueness, outlier_health, 100, overall_score],
            theta=['Completeness', 'Uniqueness', 'Outlier Health', 'Validity', 'Overall Score']
        ))
        fig_radar = px.line_polar(radar_df, r='r', theta='theta', line_close=True, title="Data Quality Benchmark Dimensions (100 = Perfect)")
        fig_radar.update_traces(fill='toself', fillcolor='rgba(16, 185, 129, 0.25)', line_color='#10b981')
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
                bgcolor="rgba(0,0,0,0)"
            ),
            margin=dict(l=40, r=40, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#0f172a")
        )
        plotly_specs["quality_radar"] = json.loads(fig_radar.to_json())
    except Exception:
        pass

    # 9. 3D Feature Explorer Scatter Plot
    if len(numeric_cols) >= 3:
        try:
            c1, c2, c3 = numeric_cols[0], numeric_cols[1], numeric_cols[2]
            fig_3d = px.scatter_3d(df.dropna(subset=[c1, c2, c3]), x=c1, y=c2, z=c3, color=c3, color_continuous_scale="Viridis", title=f"3D Interactive Scatter Feature Explorer ({c1} vs {c2} vs {c3})")
            fig_3d.update_traces(marker=dict(size=4, opacity=0.85))
            fig_3d.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["scatter_3d"] = json.loads(fig_3d.to_json())
        except Exception:
            pass

    # 10. Skewness Feature Comparison Bar Chart
    if numeric_cols:
        try:
            skews = df[numeric_cols].skew().dropna().round(3)
            skew_df = pd.DataFrame({"Column": skews.index, "Skewness": skews.values})
            fig_skew = px.bar(skew_df, x="Column", y="Skewness", color="Skewness", color_continuous_scale="PuOr", title="Numerical Feature Skewness Comparison")
            fig_skew.update_layout(
                margin=dict(l=40, r=40, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0f172a")
            )
            plotly_specs["skewness_bar"] = json.loads(fig_skew.to_json())
        except Exception:
            pass

    return charts_meta, plotly_specs
