# Array-Based Browser Navigation

> A browser-like application demonstrating how a **Python Array/List** can power browser **Back** and **Forward** navigation history.

---

## Architecture

```
User Interaction (Frontend)
        ↓
Navigation Controller (JS)
        ↓
FastAPI REST API
        ↓
Navigation Service
        ↓
Array Algorithm Engine  ←── The Brain
  history = []
  current_index = -1
        ↓
MySQL Persistence (via SQLAlchemy + PyMySQL)
```

---

## Project Structure

```
array_browser_navigation/
│
├── backend/
│   ├── main.py                          ← FastAPI app + static file server
│   ├── api/
│   │   └── navigation_routes.py         ← REST endpoints
│   ├── algorithms/
│   │   └── array_navigation.py          ← Array Algorithm Engine (the brain)
│   ├── services/
│   │   └── navigation_service.py        ← Business logic bridge
│   ├── database/
│   │   ├── connection.py                ← SQLAlchemy + PyMySQL connection
│   │   └── models.py                    ← ORM model (navigation_history table)
│   └── schemas/
│       └── navigation_schema.py         ← Pydantic v2 schemas
│
├── frontend/
│   ├── index.html                       ← Browser chrome UI
│   ├── style.css                        ← Dark glassmorphism design
│   └── app.js                           ← Navigation controller
│
├── tests/
│   └── test_array_navigation.py         ← 40+ Pytest tests
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
cd array_browser_navigation
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```bash
cp .env.example .env
```

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=array_navigation
```

### 3. Start the server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will automatically:
- Create the `array_navigation` MySQL database if it doesn't exist
- Create the `navigation_history` table

### 4. Open the browser

Navigate to: **http://localhost:8000**

---

## API Endpoints

| Method | Endpoint             | Description                              |
|--------|----------------------|------------------------------------------|
| GET    | `/`                  | Serves the browser frontend              |
| GET    | `/api/history`       | Full array state + MySQL records         |
| POST   | `/api/visit`         | Visit a new URL                          |
| POST   | `/api/back`          | Navigate backward                        |
| POST   | `/api/forward`       | Navigate forward                         |
| POST   | `/api/reload`        | Reload current page (no array change)    |
| POST   | `/api/reset`         | Clear all history                        |
| GET    | `/api/algorithm/rules` | Explain the array algorithm            |
| GET    | `/docs`              | Swagger UI (for testing)                 |

### Example: Visit a URL

```bash
curl -X POST http://localhost:8000/api/visit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'
```

Response:
```json
{
  "action": "visit",
  "success": true,
  "message": "Navigated to https://www.google.com",
  "state": {
    "history": ["https://www.google.com"],
    "current_index": 0,
    "current_page": "https://www.google.com",
    "can_go_back": false,
    "can_go_forward": false
  }
}
```

---

## Array Navigation Algorithm

### Data Structure

```python
history       = []   # Python List — stores visited URLs in order
current_index = -1   # Integer pointer into the array
```

### Rules

**Visit:**
```python
history = history[:current_index + 1]  # erase forward history
history.append(new_url)                # add new page
current_index = len(history) - 1      # advance pointer
```

**Back:**
```python
if current_index > 0:
    current_index -= 1
return history[current_index]
```

**Forward:**
```python
if current_index < len(history) - 1:
    current_index += 1
return history[current_index]
```

**Reload:**
```python
return history[current_index]  # array unchanged ✓
```

**Reset:**
```python
history = []
current_index = -1
```

---

## Example Flow

```
Start                   history=[]             index=-1
Visit Google            history=[G]            index=0
Visit YouTube           history=[G,Y]          index=1
Visit ChatGPT           history=[G,Y,C]        index=2
Back                    history=[G,Y,C]        index=1  → YouTube
Back                    history=[G,Y,C]        index=0  → Google
Forward                 history=[G,Y,C]        index=1  → YouTube
Visit GitHub            history=[G,Y,GH]       index=2  (ChatGPT erased!)
```

---

## Running Tests

```bash
cd array_browser_navigation
pytest tests/ -v
```

Expected: **all tests pass** ✓

---

## Database

- **Database:** `array_navigation`
- **Table:** `navigation_history`
- **Driver:** PyMySQL
- **ORM:** SQLAlchemy 2.0

> MySQL is used only for persistence. All navigation decisions are made by the Python Array Algorithm Engine.

---

## Keyboard Shortcuts

| Shortcut          | Action        |
|-------------------|---------------|
| `Alt + ←`         | Back          |
| `Alt + →`         | Forward       |
| `F5`              | Reload        |
| `Ctrl + L`        | Focus address bar |
| `Enter` (in bar)  | Navigate      |
