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
app.secret_key = os.getenv('SECRET_KEY', 'timetrack-rail-dev-key')

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

DEFAULT_DB = '/tmp/timetrack.db' if os.getenv('VERCEL') else 'timetrack.db'
DB_PATH = os.getenv('DATABASE_PATH', DEFAULT_DB)

SEED_TRAINS = [
    {
        "train_number": "11010", "train_name": "Sinhagad Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "06:05", "arr_time": "09:55", "days": "Daily",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "06:05", "day": 1},
            {"station": "Shivajinagar (SVJR)", "arr": "06:11", "dep": "06:13", "day": 1},
            {"station": "Pimpri (PMP)", "arr": "06:23", "dep": "06:25", "day": 1},
            {"station": "Chinchwad (CCH)", "arr": "06:29", "dep": "06:30", "day": 1},
            {"station": "Lonavala (LNL)", "arr": "07:08", "dep": "07:10", "day": 1},
            {"station": "Karjat (KJT)", "arr": "07:58", "dep": "08:00", "day": 1},
            {"station": "Kalyan Jn (KYN)", "arr": "08:42", "dep": "08:45", "day": 1},
            {"station": "Dadar Central (DR)", "arr": "09:30", "dep": "09:33", "day": 1},
            {"station": "Mumbai CSMT (CSMT)", "arr": "09:55", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12124", "train_name": "Deccan Queen SF Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "07:15", "arr_time": "10:25", "days": "Daily",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "07:15", "day": 1},
            {"station": "Shivajinagar (SVJR)", "arr": "07:20", "dep": "07:22", "day": 1},
            {"station": "Lonavala (LNL)", "arr": "08:13", "dep": "08:15", "day": 1},
            {"station": "Karjat (KJT)", "arr": "08:58", "dep": "09:00", "day": 1},
            {"station": "Dadar Central (DR)", "arr": "10:02", "dep": "10:05", "day": 1},
            {"station": "Mumbai CSMT (CSMT)", "arr": "10:25", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "11008", "train_name": "Deccan Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "15:15", "arr_time": "19:05", "days": "Daily",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "15:15", "day": 1},
            {"station": "Khadki (KK)", "arr": "15:23", "dep": "15:25", "day": 1},
            {"station": "Talegaon (TGN)", "arr": "15:48", "dep": "15:50", "day": 1},
            {"station": "Lonavala (LNL)", "arr": "16:18", "dep": "16:20", "day": 1},
            {"station": "Kalyan Jn (KYN)", "arr": "17:52", "dep": "17:55", "day": 1},
            {"station": "Dadar Central (DR)", "arr": "18:40", "dep": "18:43", "day": 1},
            {"station": "Mumbai CSMT (CSMT)", "arr": "19:05", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12128", "train_name": "Pune - Mumbai Intercity SF",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "17:55", "arr_time": "21:05", "days": "Daily",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "17:55", "day": 1},
            {"station": "Shivajinagar (SVJR)", "arr": "18:02", "dep": "18:04", "day": 1},
            {"station": "Lonavala (LNL)", "arr": "18:53", "dep": "18:55", "day": 1},
            {"station": "Thane (TNA)", "arr": "20:18", "dep": "20:20", "day": 1},
            {"station": "Dadar Central (DR)", "arr": "20:42", "dep": "20:45", "day": 1},
            {"station": "Mumbai CSMT (CSMT)", "arr": "21:05", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "22106", "train_name": "Indrayani SF Express",
        "source_code": "PUNE", "source_name": "Pune Jn",
        "dest_code": "CSMT", "dest_name": "Mumbai CSMT",
        "dep_time": "18:35", "arr_time": "21:55", "days": "Daily",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "Pune Jn (PUNE)", "arr": "Starts", "dep": "18:35", "day": 1},
            {"station": "Shivajinagar (SVJR)", "arr": "18:42", "dep": "18:44", "day": 1},
            {"station": "Lonavala (LNL)", "arr": "19:33", "dep": "19:35", "day": 1},
            {"station": "Karjat (KJT)", "arr": "20:18", "dep": "20:20", "day": 1},
            {"station": "Kalyan Jn (KYN)", "arr": "20:57", "dep": "21:00", "day": 1},
            {"station": "Dadar Central (DR)", "arr": "21:34", "dep": "21:37", "day": 1},
            {"station": "Mumbai CSMT (CSMT)", "arr": "21:55", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "22436", "train_name": "Varanasi Vande Bharat Exp",
        "source_code": "NDLS", "source_name": "New Delhi",
        "dest_code": "CNB", "dest_name": "Kanpur Central",
        "dep_time": "06:00", "arr_time": "10:08", "days": "Daily (Ex Thu)",
        "classes": ["CC", "EC"],
        "stops": [
            {"station": "New Delhi (NDLS)", "arr": "Starts", "dep": "06:00", "day": 1},
            {"station": "Kanpur Central (CNB)", "arr": "10:08", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12004", "train_name": "Lucknow Swarna Shatabdi",
        "source_code": "NDLS", "source_name": "New Delhi",
        "dest_code": "CNB", "dest_name": "Kanpur Central",
        "dep_time": "06:10", "arr_time": "11:20", "days": "Daily",
        "classes": ["CC", "EC"],
        "stops": [
            {"station": "New Delhi (NDLS)", "arr": "Starts", "dep": "06:10", "day": 1},
            {"station": "Ghaziabad (GZB)", "arr": "06:38", "dep": "06:40", "day": 1},
            {"station": "Aligarh Jn (ALJN)", "arr": "07:50", "dep": "07:52", "day": 1},
            {"station": "Tundla Jn (TDL)", "arr": "08:50", "dep": "08:52", "day": 1},
            {"station": "Etawah Jn (ETW)", "arr": "09:48", "dep": "09:50", "day": 1},
            {"station": "Kanpur Central (CNB)", "arr": "11:20", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12008", "train_name": "MGR Chennai Central Shatabdi",
        "source_code": "SBC", "source_name": "KSR Bengaluru",
        "dest_code": "MAS", "dest_name": "MGR Chennai Central",
        "dep_time": "06:00", "arr_time": "11:00", "days": "Daily (Ex Tue)",
        "classes": ["CC", "EC"],
        "stops": [
            {"station": "KSR Bengaluru (SBC)", "arr": "Starts", "dep": "06:00", "day": 1},
            {"station": "Katpadi Jn (KPD)", "arr": "09:08", "dep": "09:10", "day": 1},
            {"station": "MGR Chennai Central (MAS)", "arr": "11:00", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12608", "train_name": "Lalbagh SF Express",
        "source_code": "SBC", "source_name": "KSR Bengaluru",
        "dest_code": "MAS", "dest_name": "MGR Chennai Central",
        "dep_time": "06:25", "arr_time": "12:15", "days": "Daily",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "KSR Bengaluru (SBC)", "arr": "Starts", "dep": "06:25", "day": 1},
            {"station": "Bangarapet (BWT)", "arr": "07:28", "dep": "07:30", "day": 1},
            {"station": "Katpadi Jn (KPD)", "arr": "09:48", "dep": "09:50", "day": 1},
            {"station": "Arakkonam Jn (AJJ)", "arr": "10:48", "dep": "10:50", "day": 1},
            {"station": "MGR Chennai Central (MAS)", "arr": "12:15", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12393", "train_name": "Sampoorna Kranti Express",
        "source_code": "PNBE", "source_name": "Patna Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "19:25", "arr_time": "07:55", "days": "Daily",
        "classes": ["1A", "2A", "3A", "SL"],
        "stops": [
            {"station": "Patna Jn (PNBE)", "arr": "Starts", "dep": "19:25", "day": 1},
            {"station": "Ara Jn (ARA)", "arr": "20:03", "dep": "20:05", "day": 1},
            {"station": "Buxar (BXR)", "arr": "20:53", "dep": "20:55", "day": 1},
            {"station": "Pt DD Upadhyaya Jn (DDU)", "arr": "22:22", "dep": "22:32", "day": 1},
            {"station": "Kanpur Central (CNB)", "arr": "02:25", "dep": "02:30", "day": 2},
            {"station": "New Delhi (NDLS)", "arr": "07:55", "dep": "Ends", "day": 2}
        ]
    },
    {
        "train_number": "12309", "train_name": "Rajendra Nagar - New Delhi Tejas Rajdhani",
        "source_code": "PNBE", "source_name": "Patna Jn",
        "dest_code": "NDLS", "dest_name": "New Delhi",
        "dep_time": "19:35", "arr_time": "07:40", "days": "Daily",
        "classes": ["1A", "2A", "3A"],
        "stops": [
            {"station": "Patna Jn (PNBE)", "arr": "Starts", "dep": "19:35", "day": 1},
            {"station": "Pt DD Upadhyaya Jn (DDU)", "arr": "22:10", "dep": "22:20", "day": 1},
            {"station": "Prayagraj Jn (PRYJ)", "arr": "00:10", "dep": "00:12", "day": 2},
            {"station": "Kanpur Central (CNB)", "arr": "02:15", "dep": "02:20", "day": 2},
            {"station": "New Delhi (NDLS)", "arr": "07:40", "dep": "Ends", "day": 2}
        ]
    },
    {
        "train_number": "22895", "train_name": "Howrah - Puri Vande Bharat Express",
        "source_code": "HWH", "source_name": "Howrah Jn",
        "dest_code": "BBS", "dest_name": "Bhubaneswar",
        "dep_time": "06:10", "arr_time": "12:20", "days": "Daily (Ex Thu)",
        "classes": ["CC", "EC"],
        "stops": [
            {"station": "Howrah Jn (HWH)", "arr": "Starts", "dep": "06:10", "day": 1},
            {"station": "Kharagpur Jn (KGP)", "arr": "07:38", "dep": "07:40", "day": 1},
            {"station": "Balasore (BLS)", "arr": "09:01", "dep": "09:03", "day": 1},
            {"station": "Bhadrak (BHC)", "arr": "09:53", "dep": "09:55", "day": 1},
            {"station": "Jajpur Keonjhar Road (JJKR)", "arr": "10:23", "dep": "10:25", "day": 1},
            {"station": "Cuttack Jn (CTC)", "arr": "11:22", "dep": "11:24", "day": 1},
            {"station": "Bhubaneswar (BBS)", "arr": "12:20", "dep": "Ends", "day": 1}
        ]
    },
    {
        "train_number": "12073", "train_name": "Howrah - Bhubaneswar Jan Shatabdi Express",
        "source_code": "HWH", "source_name": "Howrah Jn",
        "dest_code": "BBS", "dest_name": "Bhubaneswar",
        "dep_time": "13:25", "arr_time": "20:00", "days": "Daily (Ex Sun)",
        "classes": ["CC", "2S"],
        "stops": [
            {"station": "Howrah Jn (HWH)", "arr": "Starts", "dep": "13:25", "day": 1},
            {"station": "Kharagpur Jn (KGP)", "arr": "15:00", "dep": "15:05", "day": 1},
            {"station": "Belda (BLDA)", "arr": "15:35", "dep": "15:36", "day": 1},
            {"station": "Jaleswar (JER)", "arr": "16:00", "dep": "16:02", "day": 1},
            {"station": "Balasore (BLS)", "arr": "16:38", "dep": "16:40", "day": 1},
            {"station": "Soro (SORO)", "arr": "17:08", "dep": "17:10", "day": 1},
            {"station": "Bhadrak (BHC)", "arr": "17:58", "dep": "18:00", "day": 1},
            {"station": "Jajpur K Road (JJKR)", "arr": "18:31", "dep": "18:33", "day": 1},
            {"station": "Cuttack Jn (CTC)", "arr": "19:26", "dep": "19:28", "day": 1},
            {"station": "Bhubaneswar (BBS)", "arr": "20:00", "dep": "Ends", "day": 1}
        ]
    }
]

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
        
        # Ensure all seed trains are present
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

def parse_station_query(raw: str):
    text = raw.strip()
    if '(' in text and ')' in text:
        code = text.split('(')[-1].split(')')[0].strip().upper()
        clean_name = text.split('(')[0].strip()
        return code, clean_name
    return text.upper(), text

def generate_ai_recommendation(source, destination, deadline, venue_mins, matching_trains, rejected_count):
    if not matching_trains:
        fallback = (
            f"No trains from {source} to {destination} reach in time for your {deadline} deadline "
            f"(accounting for {venue_mins} mins travel from the station to your venue). "
            f"Consider travelling the evening before or choosing an earlier departure."
        )
    else:
        top = matching_trains[0]
        fallback = (
            f"Take {top['train_number']} {top['train_name']} departing at {top['dep_time']} "
            f"and arriving at {top['arr_time']}. After {venue_mins} mins to reach your venue, "
            f"you will arrive at {top['venue_arrival_time']} — giving you {top['spare_minutes']} minutes "
            f"to spare ({top['risk_tag']} buffer)."
        )
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        return fallback
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=12000))
        prompt = (
            f"User is travelling from {source} to {destination}. "
            f"Hard venue deadline: {deadline}. Station-to-venue travel time: {venue_mins} minutes. "
            f"Qualifying trains (ranked by spare buffer): {json.dumps(matching_trains[:3])}. "
            f"Trains rejected for arriving too late: {rejected_count}. "
            f"Write a crisp 2-3 sentence plain-language recommendation explaining the best option, "
            f"exact spare minutes at the venue, and why it's safe or tight. If no train fits, warn clearly."
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
        project='TimeTrack Rail',
        railway_mode='timetable-seeded',
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
    
    venue_val = data.get('venue_travel_minutes')
    if venue_val is None or venue_val == '':
        venue_val = data.get('buffer', 30)

    try:
        j_date = date.fromisoformat(journey_date_str)
        d_time = time.fromisoformat(deadline_str)
        venue_mins = int(venue_val)
        if not 0 <= venue_mins <= 360:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify(error='Invalid date, deadline, or venue travel time'), 400

    if not source_raw or not dest_raw:
        return jsonify(error='Enter both origin and destination stations'), 400

    src_code, src_name = parse_station_query(source_raw)
    dst_code, dst_name = parse_station_query(dest_raw)

    if 'user_id' in session:
        with get_db() as db:
            db.execute(
                'INSERT INTO searches (user_id,source,destination,journey_date,deadline,buffer) VALUES (?,?,?,?,?,?)',
                (session['user_id'], source_raw, dest_raw, journey_date_str, deadline_str, venue_mins)
            )

    src_clean_query = f"%{src_name.upper().replace('JUNCTION', 'JN').strip()}%"
    dst_clean_query = f"%{dst_name.upper().replace('JUNCTION', 'JN').strip()}%"

    with get_db() as db:
        rows = db.execute(
            '''SELECT * FROM trains 
            WHERE (UPPER(source_code) = ? OR UPPER(source_name) LIKE ? OR UPPER(source_name) LIKE ? OR ? LIKE '%' || UPPER(source_code) || '%')
            AND (UPPER(dest_code) = ? OR UPPER(dest_name) LIKE ? OR UPPER(dest_name) LIKE ? OR ? LIKE '%' || UPPER(dest_code) || '%')''',
            (src_code, f'%{source_raw.upper()}%', src_clean_query, source_raw.upper(),
             dst_code, f'%{dest_raw.upper()}%', dst_clean_query, dest_raw.upper())
        ).fetchall()

    deadline_dt = datetime.combine(j_date, d_time)
    qualifying = []
    rejected = []

    for r in rows:
        arr_h, arr_m = map(int, r['arr_time'].split(':'))
        dep_h, dep_m = map(int, r['dep_time'].split(':'))
        
        # In a deadline-first search, the target arrival is on the deadline date (j_date).
        # For overnight journeys (where arr_time < dep_time), the train arrives on j_date
        # having departed the previous evening.
        if (arr_h, arr_m) < (dep_h, dep_m):
            arr_dt = datetime.combine(j_date, time(arr_h, arr_m))
            dep_dt = datetime.combine(j_date - timedelta(days=1), time(dep_h, dep_m))
        else:
            dep_dt = datetime.combine(j_date, time(dep_h, dep_m))
            arr_dt = datetime.combine(j_date, time(arr_h, arr_m))

        venue_arr_dt = arr_dt + timedelta(minutes=venue_mins)
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
            'source': f"{r['source_name']} ({r['source_code']})",
            'destination': f"{r['dest_name']} ({r['dest_code']})",
            'dep_time': r['dep_time'],
            'arr_time': r['arr_time'],
            'venue_arrival_time': venue_arr_dt.strftime('%H:%M'),
            'venue_travel_minutes': venue_mins,
            'spare_minutes': spare_minutes,
            'risk_tag': risk_tag,
            'days': r['days'],
            'classes': json.loads(r['classes_json']),
            'stops': json.loads(r['stops_json']),
            'irctc_url': 'https://www.irctc.co.in/nget/train-search'
        }

        if spare_minutes >= 0:
            qualifying.append(item)
        else:
            rejected.append(item)

    qualifying.sort(key=lambda x: x['spare_minutes'], reverse=True)
    ai_summary = generate_ai_recommendation(
        source_raw, dest_raw, deadline_str, venue_mins, qualifying, len(rejected)
    )

    return jsonify(
        mode='timetable',
        source=source_raw,
        destination=dest_raw,
        journey_date=journey_date_str,
        deadline=deadline_str,
        venue_travel_minutes=venue_mins,
        trains=qualifying,
        rejected_count=len(rejected),
        ai_recommendation=ai_summary,
        message=f"Found {len(qualifying)} train(s) arriving before your {deadline_str} deadline."
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
            route=f"{row['source_name']} ({row['source_code']}) -> {row['dest_name']} ({row['dest_code']})",
            dep_time=row['dep_time'],
            arr_time=row['arr_time'],
            stops=json.loads(row['stops_json']),
            message='Scheduled timetable loaded. Live GPS running status requires NTES partner credentials.'
        )
    return jsonify(mode='demo', train_number=number, message='Train not in sample timetable. Live tracking requires an authorized railway API.')

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
            "For a 12:00 PM venue deadline with 45-minute cab transit:\n"
            "• 11010 Sinhagad Express: Departs 06:05 → Arrives 09:55 → Reaches Venue 10:40 → 80 mins spare (Safe Buffer). Top pick!\n"
            "• 12124 Deccan Queen SF: Departs 07:15 → Arrives 10:25 → Reaches Venue 11:10 → 50 mins spare (Tight Buffer).\n"
            "• Evening Trains (11008, 12128, 22106): Arrive between 19:05 and 21:55 and are automatically rejected by our deadline filter."
        )
    elif any(k in q for k in ['delhi', 'kanpur', 'patna', 'bhubaneswar', 'howrah', 'chennai', 'bengaluru']):
        return (
            "📍 Supported Fast Corridors with Full Route Timetables:\n\n"
            "• New Delhi → Kanpur Central: 22436 Vande Bharat (arr 10:08) & 12004 Shatabdi (arr 11:20)\n"
            "• KSR Bengaluru → Chennai Central: 12008 Shatabdi (arr 11:00) & 12608 Lalbagh SF (arr 12:15)\n"
            "• Patna → New Delhi: 12309 Tejas Rajdhani (arr 07:40) & 12393 Sampoorna Kranti (arr 07:55)\n"
            "• Howrah → Bhubaneswar: 22895 Vande Bharat (arr 12:20) & 12073 Jan Shatabdi (arr 20:00)"
        )
    elif any(k in q for k in ['buffer', 'safety', 'how much time', 'margin', 'delay']):
        return (
            "⏱️ Recommended Safety Buffers for Indian Railways:\n\n"
            "• Exams & Job Interviews (Critical): Minimum 60+ minutes ('Safe' badge) after reaching the venue to account for registration, biometric checks, and city traffic.\n"
            "• Standard Business Meetings: 30–59 minutes ('Tight' badge).\n"
            "• Under 30 minutes ('Risky'): High risk for time-sensitive commitments due to possible signal halts or cab delays."
        )
    elif any(k in q for k in ['usp', 'unique', 'different', 'why timetrack', 'feature', 'platform', 'what is this', 'explain', 'about']):
        return (
            "✨ TimeTrack Rail's Core USP: Backward-Chained Deadline-First Discovery\n\n"
            "Traditional portals (IRCTC/NTES) search forward from departure time, forcing travellers "
            "to manually open each schedule and calculate whether they will reach in time. For critical commitments "
            "(UPSC exams, job interviews, doctor appointments), one calculation error leads to missed opportunities.\n\n"
            "TimeTrack Rail solves this by:\n"
            "1. User enters venue arrival deadline (e.g., 12:00 PM) and station-to-venue transit time (e.g., 45m).\n"
            "2. Automated Elimination: Any train arriving too late is automatically filtered out.\n"
            "3. Color-Coded Buffer: Qualifying trains are tagged Safe (≥60m spare), Tight (30–59m), or Risky (0–29m).\n"
            "4. Plain-English AI Guidance: Explains the safest option with direct IRCTC booking links."
        )
    else:
        return (
            "✨ TimeTrack Rail Journey Intelligence:\n\n"
            f"You asked: \"{question}\"\n\n"
            "TimeTrack Rail solves arrival uncertainty by computing your station-to-venue transit backwards from your deadline, "
            "filtering out late trains, and ranking valid options by guaranteed spare minutes.\n\n"
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
                    'interviews, and hospital appointments.'
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
    print(f"Starting TimeTrack Rail server on http://127.0.0.1:{port} ...")
    app.run(host='0.0.0.0', port=port, debug=False)
