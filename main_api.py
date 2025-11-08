import uvicorn
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# Import your matchmaking engine
from agents.matcher_agent import run_full_matchmaking

app = FastAPI(
    title="Full Matchmaking API",
    description="Receives live data from the frontend, runs matchmaking, and returns verdicts."
)

# --- Allow frontend origins (adjust if deployed) ---
origins = ["*"]  # You can later replace this with ["https://your-frontend-url.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
#  Pydantic Models (Match the Frontend)
# =========================

class Posting(BaseModel):
    ID: int
    title: str
    company: str
    location: Optional[str] = None
    about: Optional[str] = None
    job_description: Optional[str] = None
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None

class Profile(BaseModel):
    ID: int
    Name: str
    Profile: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None
    extracurricular: Optional[str] = None
    preferences: Optional[str] = None

class LiveMatchRequest(BaseModel):
    postings: List[Posting]
    profiles: List[Profile]

# =========================
#  Data File Handling
# =========================

POSTINGS_DIR = "data/postings"
PROFILES_DIR = "data/profiles"

def clear_data_folders():
    """Remove all .txt files from the data directories."""
    print("Clearing old .txt files...")
    for directory in [POSTINGS_DIR, PROFILES_DIR]:
        os.makedirs(directory, exist_ok=True)
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                os.remove(os.path.join(directory, filename))

def sync_live_data_to_files(postings: List[Posting], profiles: List[Profile]):
    """Write live data into local .txt files for the agent system."""
    clear_data_folders()

    # --- Write postings ---
    for p in postings:
        filepath = os.path.join(POSTINGS_DIR, f"{p.title}.txt")
        content = f"""
JOB TITLE: {p.title}
COMPANY: {p.company}
LOCATION: {p.location or ''}
ABOUT US:
{p.about or ''}
JOB DESCRIPTION:
{p.job_description or ''}
RESPONSIBILITIES:
{p.responsibilities or ''}
QUALIFICATIONS:
{p.qualifications or ''}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    # --- Write profiles ---
    for p in profiles:
        filepath = os.path.join(PROFILES_DIR, f"{p.Name}.txt")
        content = f"""
NAME: {p.Name}
PROFILE:
{p.Profile or ''}
EXPERIENCE:
{p.experience or ''}
EDUCATION:
{p.education or ''}
SKILLS:
{p.skills or ''}
EXTRACURRICULARS:
{p.extracurricular or ''}
PREFERENCES:
{p.preferences or ''}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Synced {len(postings)} postings and {len(profiles)} profiles.")

# =========================
#  API Endpoint
# =========================

@app.post("/run-live-matchmaking")
async def run_matchmaking_from_live_data(request: LiveMatchRequest):
    """
    Endpoint called by the React frontend.
    It receives Supabase data, saves it into text files, runs the matcher, and returns results.
    """
    print("Received matchmaking request...")
    sync_live_data_to_files(request.postings, request.profiles)

    # Run the multi-agent matchmaking engine
    verdicts = run_full_matchmaking()

    print("Matchmaking complete. Returning results.")
    return verdicts

@app.get("/")
async def root():
    return {"message": "Matchmaking API is running. POST to /run-live-matchmaking."}

# =========================
#  Run the Server
# =========================
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
