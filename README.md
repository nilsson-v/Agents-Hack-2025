Matchmaking Agent API

This project is a multi-agent system (built with LangGraph and FastAPI) that provides an API endpoint for matchmaking. It receives lists of candidate profiles and job postings from a frontend, runs a full matchmaking process using AI agents, and returns a final verdict.

1. Prerequisites

Before you begin, you must have the following installed on your system:

Python (version 3.10 or newer)

uv (a fast Python package installer and virtual environment manager)

How to Install uv

On macOS / Linux:

curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh


On Windows (in PowerShell):

powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"


2. Setup Instructions

Follow these steps exactly to set up your project environment.

Step 1: Clone the Repository

Clone this project to your local machine.

git clone <your-repository-url>
cd <your-project-folder>


Step 2: Create and Activate Virtual Environment

Use uv to create and activate a new virtual environment.

# This creates a folder named .venv
uv venv

# Activate the environment (macOS/Linux)
source .venv/bin/activate

# (Windows - Command Prompt)
# .venv\Scripts\activate


Your terminal prompt should change to show (.venv) at the beginning.

Step 3: Sync Dependencies (Install Packages)

Use uv to read the requirements.txt file and install all the necessary packages. This is the "sync" step.

uv pip sync requirements.txt


Step 4: Add Your API Key (Crucial)

Your agents need a Google API key to function.

Create a new file in the root of the project named .env

Open the file and add your key in the following format:

GOOGLE_API_KEY="YOUR_API_KEY_HERE"


Step 5: Create Data Directories (Necessity)

The agents work by writing and reading temporary files. You must create the data folders for this to work.

# On macOS/Linux
mkdir -p data/postings data/profiles

# On Windows
mkdir data
mkdir data\postings
mkdir data\profiles


3. Running the API Server

Once you have completed all the setup steps, you can turn on your API server.

Make sure your virtual environment is still active.

Run the main_api.py file using uvicorn:

uvicorn main_api:app --host 0.0.0.0 --port 8000


--host 0.0.0.0 makes the API "callable" from other devices on your network (like your frontend).

For development, you can use uvicorn main_api:app --reload to auto-restart the server when you make code changes.

Your server is now running at http://127.0.0.1:8000.

4. How to Use the API

Your frontend can now call this API. The main_api.py file is already configured with CORS (Cross-Origin Resource Sharing) to allow requests from any domain ("*") for development.

Endpoint: POST /run-live-matchmaking

URL (from frontend): http://<your_server_ip>:8000/run-live-matchmaking
(If your frontend is on the same machine, you can use http://127.0.0.1:8000)

Required JSON Body:
Your frontend must send a JSON object with two keys: "postings" and "profiles".

{
  "postings": [
    {
      "ID": 1,
      "title": "Software Engineer Intern",
      "company": "Innovatech",
      "location": "Helsinki, Finland",
      "about": "We are a fast-growing B2B SaaS company...",
      "job_description": "We are seeking an experienced...",
      "responsibilities": "* Write, test, and debug code...",
      "qualifications": "* Currently pursuing a Bachelor's..."
    }
  ],
  "profiles": [
    {
      "ID": 101,
      "Name": "Sofia Virtanen",
      "Profile": "A second-year Computer Science student...",
      "experience": "* AI Analytics Dashboard (Python, Flask, React)...",
      "education": "Aalto University | Espoo, Finland",
      "skills": "Python, Java, JavaScript, SQL, C++",
      "extracurricular": "Active member of the Aalto Coding Club.",
      "preferences": "Looking for challenging software engineering roles."
    }
  ]
}
