# 🌿 SmartCampus AI

Real-Time Air Quality Monitoring and Anomaly Detection System

## What it does
- Fetches live PM2.5 air quality data from OpenAQ every 30 seconds
- Runs Isolation Forest ML model to detect dangerous pollution spikes
- Stores all readings in MySQL database
- Sends automatic email alerts when anomaly is detected
- Displays live dashboard with trends and anomaly summary

## Tech Stack
| Layer | Technology |
|---|---|
| ML Model | Scikit-learn — Isolation Forest |
| Backend | FastAPI + Python |
| Database | MySQL |
| Dashboard | Streamlit |
| Scheduler | APScheduler |
| Alerts | SMTP via Gmail |
| DevOps (Phase 3) | Docker + GitHub Actions |

## Project Structure
SmartCampusAI/
├── backend/          # FastAPI endpoints
├── ml_model/         # Isolation Forest training + prediction
├── data_collection/  # OpenAQ API integration
├── dashboard/        # Streamlit live dashboard
├── alerts/           # Email alert system
└── database/         # MySQL schema

## How to run
\```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload

# Terminal 2 — Dashboard
streamlit run dashboard/app.py
\```

## Author
Riya Sharma — B.Tech CSE, UIET Kurukshetra
