import streamlit as st
import time

def render_agent_status_card(agent_name: str, status: str, details: str = ""):
    """Render a clean status card for an AIRO agent in the Streamlit UI."""
    status_colors = {
        "pending": "gray",
        "running": "blue",
        "success": "green",
        "failed": "red",
        "warning": "orange"
    }

    color = status_colors.get(status.lower(), "gray")
    icon = {
        "pending": "⏳",
        "running": "🔄",
        "success": "✅",
        "failed": "❌",
        "warning": "⚠️"
    }.get(status.lower(), "▪️")

    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {color};
            padding: 10px 15px;
            margin: 5px 0;
            background-color: #f8f9fa;
            border-radius: 4px;
        ">
            <h4 style="margin: 0; color: #333;">{icon} {agent_name.title()} Agent</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                <b>Status:</b> {status.title()}<br/>
                {details if details else ""}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
