#!/bin/bash

# Start the Backend (FastAPI) in the background
# We bind to 0.0.0.0:8000 so the frontend can reach it via localhost:8000
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &

# Wait a few seconds for variable initialization
sleep 5

# Start the Frontend (Flask)
# HF Spaces expects the listener on port 7860
python -m app.web.app
