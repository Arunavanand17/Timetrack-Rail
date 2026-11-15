@echo off
title TimeTrack Rail - Local Server
echo ========================================================
echo   TimeTrack Rail - Deadline-First Train Search Engine
echo   Team AvishkarX (FirstCommit '26 Round 2)
echo ========================================================
echo.
echo Starting Flask backend on http://127.0.0.1:5002 ...
start "" "http://127.0.0.1:5002"
"C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe" app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server stopped with an error. Trying python from PATH...
    python app.py
    pause
)
