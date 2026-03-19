import streamlit as st
import plotly.express as px
import pandas as pd

def render_metric_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, 
                       color_col: str = None, chart_type: str = "bar"):
    """Render a reusable Plotly chart for metrics in the Streamlit UI."""
    if df.empty:
        st.info("No data available for this chart.")
        return

    try:
        if chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, title=title, 
                        color=color_col, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(xaxis_title=x_col.replace('_', ' ').title(), 
                            yaxis_title=y_col.replace('_', ' ').title())
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, title=title, 
                         color=color_col, markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=title, 
                           color=color_col, size_max=15)
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error rendering chart: {str(e)}")
