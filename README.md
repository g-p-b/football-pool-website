# ⚽ Football Pool Website

A modern football pool (soccer prediction game) website where friends compete by predicting match scores.

## Features

- **User dashboard** — leaderboard, upcoming matches with bet inputs, past results with points earned
- **Scoring system** — 3 points for exact score, 1 point for correct result (win/draw/loss), 0 for wrong
- **Admin panel** — manage users, matches, seasons; set results; import matches via CSV
- **Secure** — password-protected accounts, betting locks when a match starts

---

## Quick Start

### 1. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Run the app

```bash
python3 app.py
```

Open your browser at: **http://localhost:3000**

### 3. First login

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | `admin`  | `admin123` |

> **Change the admin password** after first login via Admin → Users → Edit.

---

## How to use

### Admin workflow

1. **Create users** — Admin → Users → Add User (give each player a username and password)
2. **Create a season** — Admin → Seasons → New Season, then activate it
3. **Add matches** — Admin → Matches → Add Match (or Import CSV for bulk upload)
4. **Set results** — After a match is played, go to Matches → Set Result → enter the score

### CSV Import Format

```csv
Round,Home Team,Away Team,Date
Matchday 1,Manchester City,Arsenal,2024-08-17T15:00
Matchday 1,Chelsea,Liverpool,2024-08-17T17:30
Matchday 2,Manchester United,Tottenham,2024-08-24T15:00
```

### Player workflow

1. Players log in with their username and password
2. On the dashboard, they enter their predicted score for each upcoming match
3. Bets are locked once the match start time is reached
4. After the admin sets a result, points are automatically calculated

---

## Scoring

| Prediction | Points |
|-----------|--------|
| Exact score (e.g. bet 2-1, result 2-1) | **3 pts** |
| Correct result (win/draw/loss correct, wrong score) | **1 pt** |
| Wrong result | **0 pts** |

---

## Deployment

### Run on a server (Linux/VPS)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Set a strong secret key
export SECRET_KEY="your-random-secret-key-here"

# Run (optionally on a different port)
PORT=8080 python3 app.py
```

For production use, consider running behind **nginx** + **gunicorn**:

```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Deploy to Railway / Render / Fly.io

These platforms detect Python apps automatically. Just push the repo and set the start command to:
```
python3 app.py
```

---

## Tech Stack

- **Backend**: Python 3 + Flask
- **Database**: SQLite (file-based, zero configuration)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Auth**: Werkzeug password hashing + Flask sessions
