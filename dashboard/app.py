import os
import time

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

API_URL = os.getenv(
    "FASTAPI_URL",
    "http://127.0.0.1:8000",
)

REFRESH_INTERVAL = 35

# ─── Page config ─────────────────────────────────────────────

st.set_page_config(
    page_title="SmartCampus AI",
    page_icon="🌿",
    layout="wide",
)

# ─── Header ──────────────────────────────────────────────────

st.title("🌿 SmartCampus AI")
st.subheader(
    "Real-Time Air Quality Monitoring and Anomaly Detection"
)
st.caption(
    "Data source: OpenAQ — PM2.5 readings processed "
    "by Isolation Forest ML model"
)

# ─── Helper ──────────────────────────────────────────────────

def get_api_data(endpoint: str):
    response = requests.get(
        f"{API_URL}{endpoint}",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

# ─── Manual fetch button ─────────────────────────────────────

st.markdown("### Fetch New Reading")

if st.button("🔄 Fetch New AQI Data", type="primary"):
    with st.spinner("Fetching from OpenAQ and running ML..."):
        try:
            fetch_response = requests.post(
                f"{API_URL}/fetch",
                timeout=20,
            )

            if fetch_response.status_code == 200:
                result = fetch_response.json()
                ml = result.get("ml_result", {})

                st.success(
                    "New reading fetched, analysed and stored!"
                )

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "PM2.5",
                        f"{result.get('pm25', '—')} µg/m³",
                    )
                with c2:
                    st.metric(
                        "ML Status",
                        ml.get("status", "—"),
                    )
                with c3:
                    score = ml.get("anomaly_score")
                    st.metric(
                        "Anomaly Score",
                        f"{float(score):.4f}"
                        if score is not None else "—",
                    )

                if ml.get("is_anomaly"):
                    st.error(
                        "⚠️ ANOMALY DETECTED — "
                        "Dangerous PM2.5 spike!"
                    )
                else:
                    st.success("✅ Reading is Normal")

            else:
                st.error(
                    f"Fetch failed: {fetch_response.text}"
                )

        except requests.RequestException as error:
            st.error("FastAPI could not be reached.")
            st.exception(error)

st.divider()

# ─── Latest reading ──────────────────────────────────────────

st.markdown("### Latest Reading")

try:
    latest = get_api_data("/latest")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "PM2.5",
            f"{latest.get('pm25', '—')} µg/m³",
        )
    with col2:
        st.metric(
            "ML Status",
            latest.get("status") or "Not analysed",
        )
    with col3:
        score = latest.get("anomaly_score")
        st.metric(
            "Anomaly Score",
            f"{float(score):.4f}"
            if score is not None else "—",
        )

    if latest.get("is_anomaly"):
        st.error(
            "⚠️ Latest reading is an ANOMALY — "
            "air quality is dangerous!"
        )
    else:
        st.success("✅ Latest reading is Normal")

    st.write(
        "**City:**",
        latest.get("city") or "Unknown",
    )
    st.write(
        "**Recorded at:**",
        latest.get("recorded_at") or "Unknown",
    )

except requests.HTTPError as error:
    if error.response.status_code == 404:
        st.warning("No AQI data yet.")
    else:
        st.error("FastAPI returned an error.")
        st.exception(error)

except requests.RequestException as error:
    st.error("FastAPI is not running.")
    st.exception(error)

st.divider()

# ─── Recent readings table ────────────────────────────────────

st.markdown("### Recent Readings")

try:
    recent_data = get_api_data("/recent?limit=10")

    if recent_data:
        df = pd.DataFrame(recent_data)

        preferred_columns = [
            "id", "city", "pm25", "status",
            "is_anomaly", "anomaly_score", "recorded_at",
        ]

        visible_columns = [
            col for col in preferred_columns
            if col in df.columns
        ]

        st.dataframe(
            df[visible_columns],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### PM2.5 Trend")

        chart_df = df.copy()

        if "recorded_at" in chart_df.columns:
            chart_df["recorded_at"] = pd.to_datetime(
                chart_df["recorded_at"],
                errors="coerce",
            )
            chart_df = chart_df.sort_values("recorded_at")
            st.line_chart(
                chart_df,
                x="recorded_at",
                y="pm25",
                color="#00c853",
            )
        else:
            st.line_chart(
                chart_df.sort_values("id"),
                x="id",
                y="pm25",
            )

        st.markdown("### Anomaly Summary")

        total = len(df)
        anomalies = int(df["is_anomaly"].sum()) \
            if "is_anomaly" in df.columns else 0
        normal = total - anomalies

        a1, a2, a3 = st.columns(3)

        with a1:
            st.metric("Total Readings", total)
        with a2:
            st.metric("Normal", normal)
        with a3:
            st.metric("Anomalies", anomalies)

    else:
        st.info("No recent readings yet.")

except requests.RequestException as error:
    st.error("Could not load recent readings.")
    st.exception(error)

st.divider()

# ─── Footer + auto-refresh ───────────────────────────────────
# This is at the BOTTOM so everything above renders first

st.caption(
    "SmartCampus AI — B.Tech CSE Pre-Final Year Project | "
    "Built with FastAPI · Streamlit · MySQL · Scikit-learn"
)

# Countdown timer at the very bottom
refresh_placeholder = st.empty()

for seconds_left in range(REFRESH_INTERVAL, 0, -1):
    refresh_placeholder.caption(
        f"⏱️ Auto-refreshing in {seconds_left} seconds..."
    )
    time.sleep(1)

st.rerun()