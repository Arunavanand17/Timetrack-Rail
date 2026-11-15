# TimeTrack Rail — Round 2 Prototype (FirstCommit '26 Hackathon)

Team: **AvishkarX**  
Evaluation Target: **Deadline-First Train Search Engine**

## Overview
TimeTrack Rail is a deadline-first train discovery web app for Indian Railways. Instead of searching only by departure time, travellers entering their venue arrival deadline and station-to-venue transit time can find trains guaranteed to reach their destination on time, ranked by safe spare buffer minutes and verified by Google Gemini AI.

## Features
- **Deadline-First Search**: Automatically calculates station-to-venue buffer, spare minutes, and filters out late trains.
- **Risk Categorization**: Tags trains as **Safe** (>= 60m spare), **Tight** (30–59m spare), or **Risky** (0–29m spare).
- **Gemini AI Recommendation**: Generates intelligent plain-language advice with deterministic fallback.
- **Station-by-Station Timetables**: Expandable route tables with real IR schedules.
- **IRCTC Quick Redirect & Demo Booking**: Direct booking link to official IRCTC portal plus local demo booking simulation.

## Run Locally
1. Copy `.env.example` to `.env` (optional: add your `GEMINI_API_KEY`).
2. `pip install -r requirements.txt`
3. `python app.py`
4. Visit `http://127.0.0.1:5002` in your browser.
