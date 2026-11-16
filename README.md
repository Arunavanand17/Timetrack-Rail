# TimeTrack Rail — Grand Finale Edition (FirstCommit '26 Hackathon)

🏆 **Grand Finale Submission (Round 3 Winner Edition)**  
Team: **AvishkarX**  
Evaluation Target: **Backward-Chained Deadline-First Indian Railways Train Discovery Engine**

---

## 🌟 Executive Summary & Problem Solved
Traditional rail portals (IRCTC, NTES) operate strictly **forward from departure time**. When 23 million daily Indian Railways passengers travel for high-stakes commitments (UPSC & JEE examinations, job interviews, hospital appointments, connecting flights), departure time is irrelevant — **arriving on time with a safe buffer is everything**.

**TimeTrack Rail** revolutionizes rail discovery by searching **backwards from the traveller's hard venue arrival deadline**:
1. User enters **Destination Venue Deadline** (e.g., 12:00 PM) + **Station-to-Venue Transit** (e.g., 45m cab) + **Commitment Persona Buffer**.
2. **Automated Elimination**: Any train arriving too late to meet the commitment is rejected immediately.
3. **Color-Coded Safety Margin**: Qualifying trains are classified as **Safe** (≥60m spare), **Tight** (30–59m), or **Risky** (0–29m).
4. **Live Delay Stress-Test Simulator**: Interactive slider (0m → +90m) recalculates arrival times, buffers, and resilience against real-world Indian Railways delays in real time.

---

## 🚀 Round 3 Grand Finale Feature Innovations

### 1. ⚡ Live Delay Stress-Test Simulator (0 min → +90 min)
* Answers the **#1 judge and commuter concern: "What if the train is delayed by Indian Railways?"**
* Moving the slider dynamically recomputes every train's destination arrival, venue arrival, remaining spare buffer minutes, and flips cards from **Safe** ➔ **Tight** ➔ **Risky** ➔ **MISSED DEADLINE** instantaneously on the frontend without server re-fetching.

### 2. 🎯 Smart Persona Presets with Mandatory Reporting Buffers
* **🚆 Standard Transfer (+0m)**: Everyday commuting & casual travel.
* **🎓 Exam Centre (+30m)**: Protects against mandatory biometric registration and strict gate closures (e.g., UPSC, JEE, NEET).
* **💼 Job Interview (+20m)**: Protects against corporate security screening, visitor badges, and tower elevator queues.
* **🏥 Hospital OPD (+25m)**: Protects against OPD counter registration, token queues, and triage.

### 3. 📊 Visual Buffer Timeline Bar on Every Card
* High-contrast segmented timeline depicting:
  * **[Train Ride Duration]** (Blue)
  * **[Last-Mile + Persona Buffer]** (Purple)
  * **[Spare Margin Buffer]** (Green / Amber / Orange / Red)
  relative to the **[Hard Venue Deadline]**.

### 4. 🚄 10+ Major Corridors, Intermediate Stop Matching & Day-of-Week Validation
* **Corridors Covered**:
  * Pune Jn ↔ Mumbai CSMT (Sinhagad, Deccan Queen, Deccan Exp, Intercity SF)
  * New Delhi ↔ Kanpur Central (Vande Bharat, Shatabdi)
  * Kota Jn ↔ New Delhi (**JEE/NEET Aspirant Corridor**: Tejas Rajdhani, Jan Shatabdi)
  * KSR Bengaluru ↔ MGR Chennai Central (Shatabdi, Lalbagh SF)
  * Patna Jn ↔ New Delhi (**Overnight Expresses**: Tejas Rajdhani, Sampoorna Kranti)
  * Ahmedabad Jn ↔ Mumbai Central (Gandhinagar Vande Bharat, Shatabdi)
  * Jaipur Jn ↔ New Delhi (Ajmer Shatabdi, Double Decker)
  * Howrah Jn ↔ Bhubaneswar (Puri Vande Bharat, Jan Shatabdi)
  * Secunderabad Jn ↔ Vijayawada Jn (Vande Bharat)
* **Intermediate Stop Routing**: Searches from intermediate stations (e.g., *Pune to Dadar*, *Vadodara to Mumbai Central*, *Kharagpur to Bhubaneswar*) match schedules accurately.
* **Day-of-Week Validation**: Automatically validates weekday running schedules and filters trains that don't operate on the passenger's travel date.

### 5. 📅 1-Click Google Calendar & WhatsApp / Family Share Plan
* **Add to Calendar**: Generates one-click Google Calendar events pre-populated with train numbers, station boarding/alighting times, hard venue deadline, and spare buffer minutes.
* **Share Buffer Plan**: Formats an easy-to-read WhatsApp/SMS journey summary with emojis and safety badges to share with family or colleagues.

### 6. ✨ Google Gemini AI Journey Intelligence
* Synthesizes personalized, plain-English travel recommendations using Google Gemini 2.5 Flash, backed by an offline heuristic fallback engine when API keys are absent.

---

## 🛠️ Tech Stack & Architecture
* **Frontend**: Pure HTML5, Modern CSS Variables (Light & Dark Theme), Vanilla ES6+ JavaScript (zero external bloated dependencies).
* **Backend**: Python 3 / Flask microframework with SQLite database and persistent session auth.
* **AI Engine**: Google GenAI SDK (`gemini-2.5-flash`) with structured prompts & deterministic domain fallback.

---

## 💻 Run Locally

1. Clone repository:
   ```bash
   git clone https://github.com/Arunavanand17/Timetrack-Rail.git
   cd Timetrack-Rail
   ```
2. (Optional) Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`:
   ```bash
   copy .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run server:
   ```bash
   python app.py
   # Or double-click run_app.bat on Windows
   ```
5. Open browser at `http://127.0.0.1:5002`.

---

## 👥 AvishkarX Team
Developed for **FirstCommit '26 Hackathon (Round 3 Grand Finale)**.
