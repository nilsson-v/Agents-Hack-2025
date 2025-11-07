import os
from dotenv import load_dotenv
from typing import Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Setup ---
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)

# --- 2. State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]
    main_posting: str
    all_profiles: str

# --- 3. "Tool" Function (File Reader) ---
def get_files_for_recruiter_agent():
    """
    Reads the main job posting and ALL candidate profiles.
    Returns them as two large strings.
    """
    try:
        # Load the single posting we are acting for
        with open("data/postings/financial_analyst_intern.txt", "r") as f:
            posting_text = f.read()

        # Scan and load ALL candidate profiles
        profile_files = os.listdir("data/profiles")
        all_profiles_text = ""
        for filename in profile_files:
            if filename.endswith(".txt"):
                with open(os.path.join("data/profiles", filename), "r") as f:
                    all_profiles_text += f"\n\n--- START OF PROFILE: {filename} ---\n"
                    all_profiles_text += f.read()
                    all_profiles_text += f"\n--- END OF PROFILE: {filename} ---"
        
        if not all_profiles_text:
            return None, "Error: No .txt files found in data/profiles/"

        return posting_text, all_profiles_text

    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}")
        return None, f"Error: {e.filename} not found."

# --- 4. Graph Nodes ---

def scanner_node(state: State):
    """
    Reads all necessary files from disk and prepares the
    state for the analyzer.
    """
    print("Recruiter Agent: Reading my job posting and all candidate profiles...")
    posting, profiles = get_files_for_recruiter_agent()
    
    if "Error:" in profiles:
        # If there's an error, add it as a message to stop the graph
        return {"messages": [("system", profiles)]}

    # Create the prompt for the LLM
    prompt = f"""
    You are a recruiter agent. Your goal is to find suitable candidates for a job.

    Here is your job posting:
    ---MY JOB POSTING---
    {posting}
    ---END MY JOB POSTING---

    Here are all the available candidate profiles:
    ---ALL PROFILES---
    {profiles}
    ---END ALL PROFILES---

    Analyze all profiles against the job posting.
    Identify the most suitable candidates.
    If no cndidate is suitable don't return anyone.

    Respond with ONLY a Python-formatted list of the filenames for the
    most suitable profiles.
    Example: ['candidate_profile_1.txt', 'candidate_profile_sofia.txt']
    """
    
    return {"messages": [("human", prompt)]}


def analyzer_node(state:State):
    """
    This is the LLM agent. It takes the big prompt
    and returns the list of suitable candidates.
    """
    print("Recruiter Agent: Analyzing... Which candidates are best for me?")
    
    # Check for error message from the scanner
    if state["messages"][-1].content.startswith("Error:"):
        print("Analyzer: Skipping, error detected in scanner.")
        return {}
    
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# --- 5. Graph Definition ---
graph_builder = StateGraph(State)

graph_builder.add_node("scanner", scanner_node)
graph_builder.add_node("analyzer", analyzer_node)

graph_builder.set_entry_point("scanner")
graph_builder.add_edge("scanner", "analyzer")
graph_builder.add_edge("analyzer", END)

graph = graph_builder.compile()

# --- 6. Run the Graph ---
print("--- RUNNING RECRUITER AGENT ---")
state = graph.invoke({})

print("\n--- RECRUITER AGENT'S SUITABLE PROFILES ---")
# The final message content will be the list you can pass to the judge
print(state["messages"][-1].content)