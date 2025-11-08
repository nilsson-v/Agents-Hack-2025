# Matchmaking Agent API

This project uses a multi-agent system (built with LangGraph) to match job candidate profiles with job postings. It provides two separate APIs: one for running a full batch job on local files and one for on-demand matching from a frontend.

## 🚀 Setup & Installation

This project is managed with `uv`.

1.  **Create the virtual environment:**
    ```sh
    # This creates a .venv folder
    uv venv
    
    # Activate the environment (macOS/Linux)
    source .venv/bin/activate
    
    # (Windows)
    # .venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```sh
    uv pip install fastapi uvicorn langchain-google-genai langgraph python-dotenv
    ```

3.  **Set up your API Key:**
    Create a file named `.env` in the root of the project and add your Google API key:
    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

4.  **Populate Data:**
    Make sure your `data/postings` and `data/profiles` folders contain your `.txt` files.

---

## 🤖 How to Run the APIs

You have two servers that can be run independently. **All commands must be run from the project's root directory.**

### 1. The Batch API (Your Local Server)

This local runs the *entire* matchmaking process for **all** local `.txt` files in your `data/` folder. It's great for development and running the full system test.

**To run the locally:**
``sh
uv run agents/matcher_agent.py 

**To run the api:**
```sh
uvicorn main_api:app --host 0.0.0.0 --port 8000

