import os
import json
import sqlite3
import secrets
from functools import wraps
from datetime import date, time, datetime, timedelta
from flask import Flask, request, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'timetrack-rail-finale-key')

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    return response

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return '', 204

DEFAULT_DB = '/tmp/timetrack_r3.db' if os.getenv('VERCEL') else 'timetrack_r3.db'
DB_PATH = os.getenv('DATABASE_PATH', DEFAULT_DB)

DAY_MAP = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

SEED_TRAINS = [
    # 1. Pune Jn (PUNE) -> Mumbai CSMT (CSMT)
    {
        "train_number": "11010", "train_name": "Sinhagad Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "06:05", "arr_time": "09:55", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "PUNE", "station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "06:05", "day": 1},
            {"code": "SVJR", "station": "Shivajinagar (SVJR)", "arr": "06:11", "dep": "06:13", "day": 1},
            {"code": "PMP", "station": "Pimpri (PMP)", "arr": "06:23", "dep": "06:25", "day": 1},
            {"code": "CCH", "station": "Chinchwad (CCH)", "arr": "06:29", "dep": "06:30", "day": 1},
            {"code": "LNL", "station": "Lonavala (LNL)", "arr": "07:08", "dep": "07:10", "day": 1},
            {"code": "KJT", "station": "Karjat (KJT)", "arr": "07:58", "dep": "08:00", "day": 1},
            {"code": "KYN", "station": "Kalyan Jn (KYN)", "arr": "08:42", "dep": "08:45", "day": 1},
            {"code": "DR", "station": "Dadar Central (DR)", "arr": "09:30", "dep": "09:33", "day": 1},
            {"code": "CSMT", "station": "Mumbai CSMT (CSMT)", "arr": "09:55", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12124", "train_name": "Deccan Queen SF Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "07:15", "arr_time": "10:25", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "PUNE", "station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "07:15", "day": 1},
            {"code": "SVJR", "station": "Shivajinagar (SVJR)", "arr": "07:20", "dep": "07:22", "day": 1},
            {"code": "LNL", "station": "Lonavala (LNL)", "arr": "08:13", "dep": "08:15", "day": 1},
            {"code": "KJT", "station": "Karjat (KJT)", "arr": "08:58", "dep": "09:00", "day": 1},
            {"code": "DR", "station": "Dadar Central (DR)", "arr": "10:02", "dep": "10:05", "day": 1},
            {"code": "CSMT", "station": "Mumbai CSMT (CSMT)", "arr": "10:25", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "11008", "train_name": "Deccan Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "15:15", "arr_time": "19:05", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "PUNE", "station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "15:15", "day": 1},
            {"code": "KK", "station": "Khadki (KK)", "arr": "15:23", "dep": "15:25", "day": 1},
            {"code": "TGN", "station": "Talegaon (TGN)", "arr": "15:48", "dep": "15:50", "day": 1},
            {"code": "LNL", "station": "Lonavala (LNL)", "arr": "16:18", "dep": "16:20", "day": 1},
            {"code": "KYN", "station": "Kalyan Jn (KYN)", "arr": "17:52", "dep": "17:55", "day": 1},
            {"code": "DR", "station": "Dadar Central (DR)", "arr": "18:40", "dep": "18:43", "day": 1},
            {"code": "CSMT", "station": "Mumbai CSMT (CSMT)", "arr": "19:05", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12128", "train_name": "Pune - Mumbai Intercity SF",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "17:55", "arr_time": "21:05", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "PUNE", "station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "17:55", "day": 1},
            {"code": "SVJR", "station": "Shivajinagar (SVJR)", "arr": "18:02", "dep": "18:04", "day": 1},
            {"code": "LNL", "station": "Lonavala (LNL)", "arr": "18:53", "dep": "18:55", "day": 1},
            {"code": "TNA", "station": "Thane (TNA)", "arr": "20:18", "dep": "20:20", "day": 1},
            {"code": "DR", "station": "Dadar Central (DR)", "arr": "20:42", "dep": "20:45", "day": 1},
            {"code": "CSMT", "station": "Mumbai CSMT (CSMT)", "arr": "21:05", "dep": "Ends", "day": 1}
        ]
    },
    # 2. Mumbai CSMT (CSMT) -> Pune Jn (PUNE)
    {
        "train_number": "12127", "train_name": "Mumbai - Pune Intercity SF",
        "source_code": "CSMT", "source_name": "Mumbai CSMT",
        "dest_code": "PUNE", "dest_name": "Pune Jn",
        "dep_time": "06:40", "arr_time": "09:57", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "CSMT", "station": "Mumbai CSMT (CSMT)", "arr": "Starts", "dep": "06:40", "day": 1},
            {"code": "DR", "station": "Dadar Central (DR)", "arr": "06:50", "dep": "06:52", "day": 1},
            {"code": "TNA", "station": "Thane (TNA)", "arr": "07:13", "dep": "07:15", "day": 1},
            {"code": "LNL", "station": "Lonavala (LNL)", "arr": "08:53", "dep": "08:55", "day": 1},
            {"code": "SVJR", "station": "Shivajinagar (SVJR)", "arr": "09:38", "dep": "09:40", "day": 1},
            {"code": "PUNE", "station": "Pune Jn (PUNE)", "arr": "09:57", "dep": "Ends", "day": 1}
        ]
    },
    # 3. New Delhi (NDLS) -> Kanpur Central (CNB)
    {
        "train_number": "22436", "train_name": "Varanasi Vande Bharat Exp",
        "source_code": "NDLS", "source_name": "New Delhi",
        "dest_code": "CNB", "dest_name": "Kanpur Central",
        "dep_time": "06:00", "arr_time": "10:08", "days": "Mon,Tue,Wed,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "Starts", "dep": "06:00", "day": 1},
            {"code": "CNB", "station": "Kanpur Central (CNB)", "arr": "10:08", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12004", "train_name": "Lucknow Swarna Shatabdi",
        "source_code": "NDLS", "source_name": "New Delhi",
        "dest_code": "CNB", "dest_name": "Kanpur Central",
        "dep_time": "06:10", "arr_time": "11:20", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "Starts", "dep": "06:10", "day": 1},
            {"code": "GZB", "station": "Ghaziabad (GZB)", "arr": "06:38", "dep": "06:40", "day": 1},
            {"code": "ALJN", "station": "Aligarh Jn (ALJN)", "arr": "07:50", "dep": "07:52", "day": 1},
            {"code": "TDL", "station": "Tundla Jn (TDL)", "arr": "08:50", "dep": "08:52", "day": 1},
            {"code": "ETW", "station": "Etawah Jn (ETW)", "arr": "09:48", "dep": "09:50", "day": 1},
            {"code": "CNB", "station": "Kanpur Central (CNB)", "arr": "11:20", "dep": "Ends", "day": 1}
        ]
    },
    # 4. KSR Bengaluru (SBC) -> MGR Chennai Central (MAS)
    {
        "train_number": "12008", "train_name": "MGR Chennai Central Shatabdi",
        "source_code": "SBC", "source_name": "KSR Bengaluru",
        "dest_code": "MAS", "dest_name": "MGR Chennai Central",
        "dep_time": "06:00", "arr_time": "11:00", "days": "Mon,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "SBC", "station": "KSR Bengaluru (SBC)", "arr": "Starts", "dep": "06:00", "day": 1},
            {"code": "KPD", "station": "Katpadi Jn (KPD)", "arr": "09:08", "dep": "09:10", "day": 1},
            {"code": "MAS", "station": "MGR Chennai Central (MAS)", "arr": "11:00", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12608", "train_name": "Lalbagh SF Express",
        "source_code": "SBC", "source_name": "KSR Bengaluru",
        "dest_code": "MAS", "dest_name": "MGR Chennai Central",
        "dep_time": "06:25", "arr_time": "12:15", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "SBC", "station": "KSR Bengaluru (SBC)", "arr": "Starts", "dep": "06:25", "day": 1},
            {"code": "BWT", "station": "Bangarapet (BWT)", "arr": "07:28", "dep": "07:30", "day": 1},
            {"code": "KPD", "station": "Katpadi Jn (KPD)", "arr": "09:48", "dep": "09:50", "day": 1},
            {"code": "AJJ", "station": "Arakkonam Jn (AJJ)", "arr": "10:48", "dep": "10:50", "day": 1},
            {"code": "MAS", "station": "MGR Chennai Central (MAS)", "arr": "12:15", "dep": "Ends", "day": 1}
        ]
    },
    # 5. Patna Jn (PNBE) -> New Delhi (NDLS)
    {
        "train_number": "12309", "train_name": "Rajendra Nagar Rajdhani Exp",
        "source_code": "PNBE", "source_name": "Patna Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "19:35", "arr_time": "07:40", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["1A", "2A", "3A"],
        "stops": [
            {"code": "PNBE", "station": "Patna Jn (PNBE)", "arr": "Starts", "dep": "19:35", "day": 1},
            {"code": "DDU", "station": "Pt DD Upadhyaya Jn (DDU)", "arr": "22:12", "dep": "22:22", "day": 1},
            {"code": "PRYJ", "station": "Prayagraj Jn (PRYJ)", "arr": "00:10", "dep": "00:12", "day": 2},
            {"code": "CNB", "station": "Kanpur Central (CNB)", "arr": "02:15", "dep": "02:20", "day": 2},
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "07:40", "dep": "Ends", "day": 2}
        ]
    },
    {
        "train_number": "12393", "train_name": "Sampoorna Kranti SF Exp",
        "source_code": "PNBE", "source_name": "Patna Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "19:25", "arr_time": "07:55", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["1A", "2A", "3A", "SL"],
        "stops": [
            {"code": "PNBE", "station": "Patna Jn (PNBE)", "arr": "Starts", "dep": "19:25", "day": 1},
            {"code": "ARA", "station": "Ara Jn (ARA)", "arr": "20:02", "dep": "20:04", "day": 1},
            {"code": "DDU", "station": "Pt DD Upadhyaya Jn (DDU)", "arr": "22:22", "dep": "22:32", "day": 1},
            {"code": "CNB", "station": "Kanpur Central (CNB)", "arr": "02:30", "dep": "02:35", "day": 2},
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "07:55", "dep": "Ends", "day": 2}
        ]
    },
    # 6. Howrah Jn (HWH) -> Bhubaneswar (BBS)
    {
        "train_number": "22895", "train_name": "Howrah - Puri Vande Bharat",
        "source_code": "HWH", "source_name": "Howrah Jn",
        "dest_code": "BBS", "dest_name": "Bhubaneswar",
        "dep_time": "06:10", "arr_time": "11:10", "days": "Mon,Tue,Wed,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "HWH", "station": "Howrah Jn (HWH)", "arr": "Starts", "dep": "06:10", "day": 1},
            {"code": "KGP", "station": "Kharagpur Jn (KGP)", "arr": "07:38", "dep": "07:40", "day": 1},
            {"code": "BLS", "station": "Balasore (BLS)", "arr": "08:50", "dep": "08:52", "day": 1},
            {"code": "CTC", "station": "Cuttack Jn (CTC)", "arr": "10:35", "dep": "10:37", "day": 1},
            {"code": "BBS", "station": "Bhubaneswar (BBS)", "arr": "11:10", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12073", "train_name": "Howrah - Bhubaneswar Jan Shatabdi",
        "source_code": "HWH", "source_name": "Howrah Jn",
        "dest_code": "BBS", "dest_name": "Bhubaneswar",
        "dep_time": "13:25", "arr_time": "20:05", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "HWH", "station": "Howrah Jn (HWH)", "arr": "Starts", "dep": "13:25", "day": 1},
            {"code": "KGP", "station": "Kharagpur Jn (KGP)", "arr": "15:05", "dep": "15:10", "day": 1},
            {"code": "CTC", "station": "Cuttack Jn (CTC)", "arr": "19:15", "dep": "19:20", "day": 1},
            {"code": "BBS", "station": "Bhubaneswar (BBS)", "arr": "20:05", "dep": "Ends", "day": 1}
        ]
    },
    # 7. Ahmedabad Jn (ADI) -> Mumbai Central (MMCT)
    {
        "train_number": "20902", "train_name": "Gandhinagar - Mumbai Vande Bharat",
        "source_code": "ADI", "source_name": "Ahmedabad Jn",
        "dest_code": "MMCT", "dest_name": "Mumbai Central",
        "dep_time": "14:40", "arr_time": "20:15", "days": "Mon,Tue,Thu,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "ADI", "station": "Ahmedabad Jn (ADI)", "arr": "Starts", "dep": "14:40", "day": 1},
            {"code": "BRC", "station": "Vadodara Jn (BRC)", "arr": "15:46", "dep": "15:51", "day": 1},
            {"code": "ST", "station": "Surat (ST)", "arr": "17:13", "dep": "17:18", "day": 1},
            {"code": "BVI", "station": "Borivali (BVI)", "arr": "19:33", "dep": "19:36", "day": 1},
            {"code": "MMCT", "station": "Mumbai Central (MMCT)", "arr": "20:15", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12010", "train_name": "Ahmedabad - Mumbai Shatabdi",
        "source_code": "ADI", "source_name": "Ahmedabad Jn",
        "dest_code": "MMCT", "dest_name": "Mumbai Central",
        "dep_time": "15:10", "arr_time": "21:35", "days": "Mon,Tue,Wed,Thu,Fri,Sat",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "ADI", "station": "Ahmedabad Jn (ADI)", "arr": "Starts", "dep": "15:10", "day": 1},
            {"code": "BRC", "station": "Vadodara Jn (BRC)", "arr": "16:28", "dep": "16:33", "day": 1},
            {"code": "ST", "station": "Surat (ST)", "arr": "18:05", "dep": "18:10", "day": 1},
            {"code": "MMCT", "station": "Mumbai Central (MMCT)", "arr": "21:35", "dep": "Ends", "day": 1}
        ]
    },
    # 8. Jaipur Jn (JP) -> New Delhi (NDLS)
    {
        "train_number": "12016", "train_name": "Ajmer - New Delhi Shatabdi",
        "source_code": "JP", "source_name": "Jaipur Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "17:50", "arr_time": "22:40", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "JP", "station": "Jaipur Jn (JP)", "arr": "Starts", "dep": "17:50", "day": 1},
            {"code": "AWR", "station": "Alwar Jn (AWR)", "arr": "19:42", "dep": "19:45", "day": 1},
            {"code": "GGN", "station": "Gurgaon (GGN)", "arr": "21:43", "dep": "21:45", "day": 1},
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "22:40", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12985", "train_name": "Jaipur - Delhi Double Decker",
        "source_code": "JP", "source_name": "Jaipur Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "06:00", "arr_time": "10:30", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "JP", "station": "Jaipur Jn (JP)", "arr": "Starts", "dep": "06:00", "day": 1},
            {"code": "AWR", "station": "Alwar Jn (AWR)", "arr": "07:53", "dep": "07:55", "day": 1},
            {"code": "GGN", "station": "Gurgaon (GGN)", "arr": "09:44", "dep": "09:46", "day": 1},
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "10:30", "dep": "Ends", "day": 1}
        ]
    },
    # 9. Secunderabad Jn (SC) -> Vijayawada Jn (BZA)
    {
        "train_number": "20707", "train_name": "Secunderabad - Visakhapatnam Vande Bharat",
        "source_code": "SC", "source_name": "Secunderabad Jn",
        "dest_code": "BZA", "dest_name": "Vijayawada Jn",
        "dep_time": "05:05", "arr_time": "08:50", "days": "Mon,Tue,Wed,Fri,Sat,Sun",
        "classes": ["CC", "EC"],
        "stops": [
            {"code": "SC", "station": "Secunderabad Jn (SC)", "arr": "Starts", "dep": "05:05", "day": 1},
            {"code": "WL", "station": "Warangal (WL)", "arr": "06:33", "dep": "06:35", "day": 1},
            {"code": "KMT", "station": "Khammam (KMT)", "arr": "07:38", "dep": "07:40", "day": 1},
            {"code": "BZA", "station": "Vijayawada Jn (BZA)", "arr": "08:50", "dep": "Ends", "day": 1}
        ]
    },
    # 10. Kota Jn (KOTA) -> New Delhi (NDLS) - JEE/NEET Aspirant Corridor
    {
        "train_number": "12059", "train_name": "Kota - Hazrat Nizamuddin Jan Shatabdi",
        "source_code": "KOTA", "source_name": "Kota Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "05:55", "arr_time": "12:30", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["CC", "2S"],
        "stops": [
            {"code": "KOTA", "station": "Kota Jn (KOTA)", "arr": "Starts", "dep": "05:55", "day": 1},
            {"code": "SWM", "station": "Sawai Madhopur (SWM)", "arr": "07:03", "dep": "07:05", "day": 1},
            {"code": "MTJ", "station": "Mathura Jn (MTJ)", "arr": "10:15", "dep": "10:17", "day": 1},
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "12:30", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12951", "train_name": "Mumbai - New Delhi Tejas Rajdhani",
        "source_code": "KOTA", "source_name": "Kota Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "03:20", "arr_time": "08:32", "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "classes": ["1A", "2A", "3A"],
        "stops": [
            {"code": "KOTA", "station": "Kota Jn (KOTA)", "arr": "03:15", "dep": "03:20", "day": 1},
            {"code": "NDLS", "station": "New Delhi (NDLS)", "arr": "08:32", "dep": "Ends", "day": 1}
        ]
    }
]

PERSONA_BUFFERS = {
    "standard": {"label": "Standard Transfer", "extra_mins": 0},
    "exam": {"label": "Exam Centre (Gate Closure +30m)", "extra_mins": 30},
    "interview": {"label": "Job Interview (Security/Check-in +20m)", "extra_mins": 20},
    "hospital": {"label": "Hospital OPD (Registration +25m)", "extra_mins": 25},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            journey_date TEXT NOT NULL,
            deadline TEXT NOT NULL,
            buffer INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS demo_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            passenger_name TEXT NOT NULL,
            passenger_age INTEGER NOT NULL,
            passenger_gender TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            journey_date TEXT NOT NULL,
            train_number TEXT NOT NULL,
            travel_class TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DEMO CONFIRMED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS trains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_number TEXT UNIQUE NOT NULL,
            train_name TEXT NOT NULL,
            source_code TEXT NOT NULL,
            source_name TEXT NOT NULL,
            dest_code TEXT NOT NULL,
            dest_name TEXT NOT NULL,
            dep_time TEXT NOT NULL,
            arr_time TEXT NOT NULL,
            days TEXT NOT NULL,
            classes_json TEXT NOT NULL,
            stops_json TEXT NOT NULL
        )''')
        
        # Populate / refresh seed trains
        for t in SEED_TRAINS:
            db.execute('''INSERT OR REPLACE INTO trains 
                (train_number, train_name, source_code, source_name, dest_code, dest_name, dep_time, arr_time, days, classes_json, stops_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (t['train_number'], t['train_name'], t['source_code'], t['source_name'],
                 t['dest_code'], t['dest_name'], t['dep_time'], t['arr_time'],
                 t['days'], json.dumps(t['classes']), json.dumps(t['stops']))
            )

init_db()

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify(error='Please login first'), 401
        return func(*args, **kwargs)
    return wrapper

def extract_query_token(raw: str):
    text = raw.strip()
    if '(' in text and ')' in text:
        code = text.split('(')[-1].split(')')[0].strip().upper()
        clean_name = text.split('(')[0].strip().upper()
        return code, clean_name
    return text.upper(), text.upper()

def match_segment_stops(stops, src_code, src_upper, dst_code, dst_upper):
    """Matches either primary endpoints or any ordered pair of intermediate stops."""
    src_idx = None
    dst_idx = None
    for idx, stop in enumerate(stops):
        s_code = stop.get('code', '').upper()
        s_name = stop.get('station', '').upper()
        if src_idx is None:
            if (src_code and (s_code == src_code or src_code in s_name)) or (src_upper and src_upper in s_name):
                src_idx = idx
        elif src_idx is not None:
            if (dst_code and (s_code == dst_code or dst_code in s_name)) or (dst_upper and dst_upper in s_name):
                dst_idx = idx
                break
    if src_idx is not None and dst_idx is not None and dst_idx > src_idx:
        return stops[src_idx], stops[dst_idx]
    return None, None

def generate_ai_recommendation(source, destination, deadline, total_transit_mins, persona_label, matching_trains, rejected_count, skipped_day_count):
    if not matching_trains:
        extra_note = f" ({skipped_day_count} train(s) do not run on the selected day of week.)" if skipped_day_count else ""
        fallback = (
            f"No trains from {source} to {destination} reach in time for your {deadline} deadline "
            f"after accounting for {total_transit_mins} mins ({persona_label}).{extra_note} "
            f"Consider travelling the evening prior or choosing an earlier departure corridor."
        )
    else:
        top = matching_trains[0]
        fallback = (
            f"Best Option: {top['train_number']} {top['train_name']} (Departs {top['dep_time']}, Arrives {top['arr_time']}). "
            f"Including {total_transit_mins} mins for {persona_label}, you reach your venue at {top['venue_arrival_time']} — "
            f"leaving {top['spare_minutes']} minutes of {top['risk_tag']} buffer before {deadline}."
        )
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        return fallback
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=12000))
        prompt = (
            f"Passenger route: {source} to {destination}. Hard deadline: {deadline}. "
            f"Total last-mile + reporting buffer: {total_transit_mins} mins ({persona_label}). "
            f"Qualifying trains ranked by spare buffer: {json.dumps(matching_trains[:3])}. "
            f"Late trains filtered out: {rejected_count}. Non-operating day trains skipped: {skipped_day_count}. "
            f"Write a crisp 2-3 sentence recommendation explaining the best train, exact spare buffer at the venue, "
            f"and resilience against minor railway delays."
        )
        response = client.models.generate_content(
            model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=220)
        )
        return (response.text or '').strip() or fallback
    except Exception:
        return fallback

@app.get('/')
def home():
    return send_file('index.html')

@app.get('/api/health')
def health():
    return jsonify(
        status='running',
        project='TimeTrack Rail Finale Edition',
        railway_mode='timetable-seeded-20-trains',
        ai_mode='gemini' if os.getenv('GEMINI_API_KEY') else 'rule-based-fallback'
    )

@app.post('/api/auth/register')
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get('name', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    if not name or '@' not in email or len(password) < 8:
        return jsonify(error='Enter name, email and password of 8+ characters'), 400
    try:
        with get_db() as db:
            cursor = db.execute('INSERT INTO users (name,email,password_hash) VALUES (?,?,?)',
                                (name, email, generate_password_hash(password)))
            user_id = cursor.lastrowid
        session['user_id'] = user_id
        return jsonify(user={'id': user_id, 'name': name, 'email': email}), 201
    except sqlite3.IntegrityError:
        return jsonify(error='Email already registered'), 409

@app.post('/api/auth/login')
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify(error='Invalid email or password'), 401
    session['user_id'] = user['id']
    return jsonify(user={'id': user['id'], 'name': user['name'], 'email': user['email']})

@app.post('/api/auth/logout')
def logout():
    session.clear()
    return jsonify(message='Logged out successfully')

@app.get('/api/auth/me')
def profile():
    if 'user_id' not in session:
        return jsonify(user=None)
    with get_db() as db:
        user = db.execute('SELECT id,name,email FROM users WHERE id=?', (session['user_id'],)).fetchone()
    return jsonify(user=dict(user) if user else None)

@app.patch('/api/auth/profile')
@login_required
def edit_profile():
    data = request.get_json(silent=True) or {}
    name = str(data.get('name', '')).strip()
    if not 2 <= len(name) <= 80:
        return jsonify(error='Name must be 2 to 80 characters'), 400
    with get_db() as db:
        db.execute('UPDATE users SET name=? WHERE id=?', (name, session['user_id']))
        row = db.execute('SELECT id,name,email FROM users WHERE id=?', (session['user_id'],)).fetchone()
    return jsonify(user=dict(row), message='Profile updated')

@app.get('/api/searches')
@login_required
def saved_searches():
    with get_db() as db:
        rows = db.execute('SELECT * FROM searches WHERE user_id=? ORDER BY id DESC LIMIT 30', (session['user_id'],)).fetchall()
    return jsonify(searches=[dict(row) for row in rows])

@app.delete('/api/searches/<int:search_id>')
@login_required
def delete_search(search_id):
    with get_db() as db:
        db.execute('DELETE FROM searches WHERE id=? AND user_id=?', (search_id, session['user_id']))
    return jsonify(message='Search deleted')

@app.post('/api/trains/search')
def search_trains():
    data = request.get_json(silent=True) or {}
    source_raw = str(data.get('source', '')).strip()
    dest_raw = str(data.get('destination', '')).strip()
    journey_date_str = str(data.get('journey_date', '')).strip()
    deadline_str = str(data.get('deadline', '')).strip()
    persona_key = str(data.get('persona', 'standard')).strip().lower()
    persona = PERSONA_BUFFERS.get(persona_key, PERSONA_BUFFERS['standard'])

    try:
        j_date = date.fromisoformat(journey_date_str)
        d_time = time.fromisoformat(deadline_str)
        venue_mins = int(data.get('venue_travel_minutes', data.get('buffer', 30)))
        if not 0 <= venue_mins <= 360:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify(error='Invalid date, deadline, or venue travel time'), 400

    if not source_raw or not dest_raw:
        return jsonify(error='Enter both origin and destination stations'), 400

    total_transit_mins = venue_mins + persona['extra_mins']
    weekday_short = DAY_MAP[j_date.weekday()]
    src_code, src_upper = extract_query_token(source_raw)
    dst_code, dst_upper = extract_query_token(dest_raw)

    if 'user_id' in session:
        with get_db() as db:
            db.execute(
                'INSERT INTO searches (user_id,source,destination,journey_date,deadline,buffer) VALUES (?,?,?,?,?,?)',
                (session['user_id'], source_raw, dest_raw, journey_date_str, deadline_str, total_transit_mins)
            )

    with get_db() as db:
        all_rows = db.execute('SELECT * FROM trains').fetchall()

    deadline_dt = datetime.combine(j_date, d_time)
    qualifying = []
    rejected = []
    skipped_day = []

    for r in all_rows:
        stops = json.loads(r['stops_json'])
        board_stop, alight_stop = match_segment_stops(stops, src_code, src_upper, dst_code, dst_upper)
        if not board_stop or not alight_stop:
            continue

        operating_days = [d.strip() for d in r['days'].split(',')]
        if weekday_short not in operating_days:
            skipped_day.append(r['train_number'])
            continue

        dep_str = board_stop['dep'] if board_stop['dep'] != 'Starts' else r['dep_time']
        arr_str = alight_stop['arr'] if alight_stop['arr'] != 'Ends' else r['arr_time']
        dep_h, dep_m = map(int, dep_str.split(':'))
        arr_h, arr_m = map(int, arr_str.split(':'))

        # In a deadline-first search, target arrival is on the deadline date (j_date).
        # For overnight journeys (where arrival time < departure time), the train departs
        # the evening prior and reaches on j_date morning.
        if (arr_h, arr_m) < (dep_h, dep_m):
            arr_dt = datetime.combine(j_date, time(arr_h, arr_m))
            dep_dt = datetime.combine(j_date - timedelta(days=1), time(dep_h, dep_m))
        else:
            dep_dt = datetime.combine(j_date, time(dep_h, dep_m))
            arr_dt = datetime.combine(j_date, time(arr_h, arr_m))

        ride_minutes = int((arr_dt - dep_dt).total_seconds() // 60)
        venue_arr_dt = arr_dt + timedelta(minutes=total_transit_mins)
        spare_minutes = int((deadline_dt - venue_arr_dt).total_seconds() // 60)

        if spare_minutes >= 60:
            risk_tag = 'Safe'
        elif spare_minutes >= 30:
            risk_tag = 'Tight'
        elif spare_minutes >= 0:
            risk_tag = 'Risky'
        else:
            risk_tag = 'Late'

        item = {
            'train_number': r['train_number'],
            'train_name': r['train_name'],
            'source': board_stop['station'],
            'destination': alight_stop['station'],
            'dep_time': dep_str,
            'arr_time': arr_str,
            'ride_minutes': ride_minutes,
            'venue_arrival_time': venue_arr_dt.strftime('%H:%M'),
            'venue_travel_minutes': venue_mins,
            'persona_extra_minutes': persona['extra_mins'],
            'total_transit_minutes': total_transit_mins,
            'spare_minutes': spare_minutes,
            'risk_tag': risk_tag,
            'days': r['days'],
            'classes': json.loads(r['classes_json']),
            'stops': stops,
            'irctc_url': 'https://www.irctc.co.in/nget/train-search'
        }

        if spare_minutes >= 0:
            qualifying.append(item)
        else:
            rejected.append(item)

    qualifying.sort(key=lambda x: x['spare_minutes'], reverse=True)
    ai_summary = generate_ai_recommendation(
        source_raw, dest_raw, deadline_str, total_transit_mins,
        persona['label'], qualifying, len(rejected), len(skipped_day)
    )

    return jsonify(
        mode='timetable',
        source=source_raw,
        destination=dest_raw,
        journey_date=journey_date_str,
        weekday=weekday_short,
        deadline=deadline_str,
        persona=persona,
        venue_travel_minutes=venue_mins,
        total_transit_minutes=total_transit_mins,
        trains=qualifying,
        rejected_count=len(rejected),
        skipped_day_count=len(skipped_day),
        ai_recommendation=ai_summary,
        message=f"Found {len(qualifying)} train(s) on {weekday_short} reaching before {deadline_str}."
    )

@app.get('/api/trains/live')
def live_train():
    number = request.args.get('train_number', '').strip()
    if not number:
        return jsonify(error='Enter train number'), 400
    with get_db() as db:
        row = db.execute('SELECT * FROM trains WHERE train_number=?', (number,)).fetchone()
    if row:
        return jsonify(
            mode='timetable',
            train_number=row['train_number'],
            train_name=row['train_name'],
            route=f"{row['source_name']} ({row['source_code']}) → {row['dest_name']} ({row['dest_code']})",
            dep_time=row['dep_time'],
            arr_time=row['arr_time'],
            days=row['days'],
            stops=json.loads(row['stops_json']),
            message='Scheduled timetable loaded. Use the Delay Stress-Test Slider in Deadline Planner to simulate live NTES delays.'
        )
    return jsonify(mode='demo', train_number=number, message='Train not in sample timetable. Live GPS running status requires NTES partner credentials.')

@app.get('/api/pnr/<pnr_number>')
def check_pnr(pnr_number):
    if not pnr_number.isdigit() or len(pnr_number) != 10:
        return jsonify(error='PNR must contain 10 digits'), 400
    return jsonify(mode='demo', message='PNR enquiry requires an authorized railway API.')

def generate_assistant_fallback(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ['pune', 'csmt', 'mumbai', 'sinhagad', 'deccan queen']):
        return (
            "🚄 Pune Jn to Mumbai CSMT Corridor Analysis:\n\n"
            "For a 12:00 PM venue deadline with 45-minute transit:\n"
            "• 11010 Sinhagad Express: Departs 06:05 → Arrives 09:55 → Reaches Venue 10:40 → 80 mins spare (Safe Buffer). Top recommendation!\n"
            "• 12124 Deccan Queen SF: Departs 07:15 → Arrives 10:25 → Reaches Venue 11:10 → 50 mins spare (Tight Buffer).\n"
            "• Evening Trains (11008, 12128): Arrive between 19:05 and 21:05 and are automatically rejected by our deadline filter."
        )
    elif any(k in q for k in ['kota', 'jee', 'neet', 'delhi', 'aspirant']):
        return (
            "🎓 Kota Jn to New Delhi (JEE/NEET Aspirant Corridor):\n\n"
            "• 12951 Tejas Rajdhani: Departs 03:20 → Arrives 08:32. Ideal for morning exam reporting!\n"
            "• 12059 Jan Shatabdi: Departs 05:55 → Arrives 12:30. Best suited for afternoon exam slots (2:00 PM onwards).\n"
            "• Tip: Select the 'Exam Centre (+30m gate buffer)' persona preset to protect against biometric gate closures!"
        )
    elif any(k in q for k in ['delhi', 'kanpur', 'patna', 'bhubaneswar', 'howrah', 'chennai', 'bengaluru', 'ahmedabad', 'jaipur', 'secunderabad', 'vijayawada']):
        return (
            "📍 Supported Fast Corridors with Full Route Timetables:\n\n"
            "• New Delhi ↔ Kanpur: 22436 Vande Bharat (arr 10:08) & 12004 Shatabdi (arr 11:20)\n"
            "• Kota ↔ New Delhi: 12951 Tejas Rajdhani (arr 08:32) & 12059 Jan Shatabdi (arr 12:30)\n"
            "• KSR Bengaluru ↔ Chennai: 12008 Shatabdi (arr 11:00) & 12608 Lalbagh SF (arr 12:15)\n"
            "• Patna ↔ New Delhi: 12309 Tejas Rajdhani (arr 07:40) & 12393 Sampoorna Kranti (arr 07:55)\n"
            "• Ahmedabad ↔ Mumbai: 20902 Vande Bharat (arr 20:15) & 12010 Shatabdi (arr 21:35)\n"
            "• Jaipur ↔ New Delhi: 12985 Double Decker (arr 10:30) & 12016 Shatabdi (arr 22:40)\n"
            "• Secunderabad ↔ Vijayawada: 20707 Vande Bharat (arr 08:50)\n"
            "• Howrah ↔ Bhubaneswar: 22895 Vande Bharat (arr 11:10) & 12073 Jan Shatabdi (arr 20:05)"
        )
    elif any(k in q for k in ['buffer', 'safety', 'how much time', 'margin', 'delay', 'slider', 'stress']):
        return (
            "⏱️ Recommended Safety Buffers & Stress-Testing on Indian Railways:\n\n"
            "• Exams & Gate Closures: Minimum 60+ minutes ('Safe' badge) + 30m gate buffer. Most exam centres shut gates 30 minutes before exam time!\n"
            "• Job Interviews: 30–59 minutes ('Tight' badge) + 20m security check-in buffer.\n"
            "• Live Stress-Test Slider: In our search results, drag the Delay Slider (0 to +90m) to see if your chosen train still reaches on time if delayed!"
        )
    elif any(k in q for k in ['usp', 'unique', 'different', 'why timetrack', 'feature', 'platform', 'what is this', 'explain', 'about', 'round 3', 'finale']):
        return (
            "✨ TimeTrack Rail's Core Innovation: Backward-Chained Deadline-First Train Discovery\n\n"
            "Traditional portals (IRCTC/NTES) search forward from departure time, forcing travellers to open multiple train schedules and manually guess whether they will reach in time.\n\n"
            "TimeTrack Rail Round 3 Grand Finale Features:\n"
            "1. Backward-Chained Search: Eliminates arrival anxiety by starting from venue deadline.\n"
            "2. Smart Persona Presets: One-click adds real-world reporting buffer (+30m exam, +20m interview, +25m hospital).\n"
            "3. Live Delay Stress-Test Simulator: Test 0 to +90 min delays with instant re-ranking.\n"
            "4. Visual Buffer Timeline: Color-coded breakdown of Ride, Last-Mile, and Spare Buffer.\n"
            "5. 1-Click Google Calendar & WhatsApp Plan Export for passengers and families."
        )
    else:
        return (
            "✨ TimeTrack Rail Journey Intelligence:\n\n"
            f"You asked: \"{question}\"\n\n"
            "TimeTrack Rail solves arrival uncertainty on Indian Railways by computing station-to-venue transit backwards from your deadline, "
            "filtering out late trains, and stress-testing delay margins.\n\n"
            "💡 Tip: Try our 1-click pitch demo above to see the deadline-first discovery algorithm live in action!"
        )

@app.post('/api/assistant')
def assistant():
    data = request.get_json(silent=True) or {}
    question = str(data.get('message') or data.get('question') or '').strip()
    if not question:
        return jsonify(error='Please enter a question.'), 400
    if len(question) > 1500:
        return jsonify(error='Question is too long (maximum 1500 characters).'), 400

    fallback_reply = generate_assistant_fallback(question)
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        return jsonify(mode='rule-based-fallback', reply=fallback_reply)
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20000))
        response = client.models.generate_content(
            model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=(
                    'You are TimeTrack Rail AI, an Indian railway deadline-first journey planner. '
                    'Reply in clear, concise English. Help passengers plan safe arrival buffers for exams, '
                    'interviews, and hospital appointments. Recommend specific trains and buffers when relevant.'
                ),
                temperature=0.4,
                max_output_tokens=500
            )
        )
        answer = (response.text or '').strip()
        if not answer:
            return jsonify(mode='rule-based-fallback', reply=fallback_reply)
        return jsonify(mode='gemini', reply=answer)
    except Exception:
        app.logger.exception('Gemini request failed')
        return jsonify(mode='rule-based-fallback', reply=fallback_reply)

@app.post('/api/bookings/demo')
@login_required
def create_demo_booking():
    data = request.get_json(silent=True) or {}
    passenger = str(data.get('passenger_name', '')).strip()
    gender = str(data.get('passenger_gender', '')).strip()
    source = str(data.get('source', '')).strip()
    destination = str(data.get('destination', '')).strip()
    journey_date = str(data.get('journey_date', '')).strip()
    train_number = str(data.get('train_number', '')).strip()
    travel_class = str(data.get('travel_class', '')).strip()
    try:
        age = int(data.get('passenger_age'))
        date.fromisoformat(journey_date)
        if not 1 <= age <= 120:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify(error='Enter a valid age and journey date'), 400
    if not 2 <= len(passenger) <= 100 or not source or not destination or source.casefold() == destination.casefold() or not train_number or gender not in ('Male', 'Female', 'Other', 'Prefer not to say') or travel_class not in ('SL', '3A', '2A', '1A', 'CC', '2S', 'EC'):
        return jsonify(error='Complete all passenger and journey fields correctly'), 400
    reference = 'TTRDEMO-' + secrets.token_hex(5).upper()
    with get_db() as db:
        db.execute(
            'INSERT INTO demo_bookings (reference,user_id,passenger_name,passenger_age,passenger_gender,source,destination,journey_date,train_number,travel_class) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (reference, session['user_id'], passenger, age, gender, source, destination, journey_date, train_number, travel_class)
        )
    return jsonify(
        mode='demo',
        reference=reference,
        status='DEMO CONFIRMED',
        irctc_url='https://www.irctc.co.in/nget/train-search',
        message='Demo booking saved. Click "Book on IRCTC" for official reservation.'
    ), 201

@app.get('/api/bookings')
@login_required
def list_demo_bookings():
    with get_db() as db:
        rows = db.execute(
            'SELECT id,reference,passenger_name,passenger_age,passenger_gender,source,destination,journey_date,train_number,travel_class,status,created_at FROM demo_bookings WHERE user_id=? ORDER BY id DESC LIMIT 50',
            (session['user_id'],)
        ).fetchall()
    return jsonify(mode='demo', bookings=[dict(row) for row in rows])

@app.delete('/api/bookings/<int:booking_id>')
@login_required
def cancel_demo_booking(booking_id):
    with get_db() as db:
        result = db.execute(
            "UPDATE demo_bookings SET status='DEMO CANCELLED' WHERE id=? AND user_id=? AND status='DEMO CONFIRMED'",
            (booking_id, session['user_id'])
        )
    if not result.rowcount:
        return jsonify(error='Active demo booking not found'), 404
    return jsonify(mode='demo', message='Demo booking cancelled')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    print(f"Starting TimeTrack Rail Grand Finale server on http://127.0.0.1:{port} ...")
    app.run(host='0.0.0.0', port=port, debug=False)
