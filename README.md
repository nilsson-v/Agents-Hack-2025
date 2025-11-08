
````markdown
# Matchmaking Agent API

This project is a multi-agent system built with **LangGraph** and **FastAPI** that provides an API endpoint for matchmaking.  
It receives lists of candidate profiles and job postings from a frontend, runs a full matchmaking process using AI agents, and returns a final verdict.

---

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

- Python (version 3.10 or newer)
- uv (a fast Python package installer and virtual environment manager)

### How to Install uv

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
````

**Windows (PowerShell)**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 2. Setup Instructions

Follow these steps to set up your project environment.

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd <your-project-folder>
```

---

## 3. Sync UV

```bash
# This syncs uv
sync uv
```

---

## 4. Create and Activate Virtual Environment

Use `uv` to create and activate a new virtual environment.

```bash
# Create a folder named .venv
uv venv
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows (Command Prompt)**

```bash
.venv\Scripts\activate
```

When active, your terminal prompt should show `(.venv)` at the beginning.

---

## 5. Add Your API Key

Your agents require a Google API key to function.

1. Create a new file in the project root named `.env`
2. Add your key in the following format:

```bash
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

---

## 6. Running the API Server

Once setup is complete and your virtual environment is active, start the API server with Uvicorn:

```bash
uvicorn main_api:app --host 127.0.0.1 --port 8000
```

Your server will be running at:

```
http://127.0.0.1:8000
```

---

## 7. How to Use the API

Your frontend can now communicate with this API.
The `main_api.py` file includes CORS configuration to allow requests from any domain (`"*"`), which is convenient for development.

**Endpoint**

```
POST /run-live-matchmaking
```

**Example URL (Frontend)**

```
http://<your_server_ip>:8000/run-live-matchmaking
```

If your frontend runs on the same machine, use:

```
http://127.0.0.1:8000
```

---

**Matchmaking Agent API** is now ready to run and handle live AI-powered candidate-job matching.

```

---

Would you like me to format it for GitHub with a generated table of contents and consistent heading links (e.g., `[Setup Instructions](#2-setup-instructions)`)?
```
