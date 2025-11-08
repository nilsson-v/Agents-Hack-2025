import os
from dotenv import load_dotenv
from typing import Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Setup ---
load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# --- 2. State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]
    # This will be provided as input
    target_posting_filename: str

# --- 3. "Tool" Function (File Reader) ---
def get_files_for_recruiter_agent(target_posting_file: str) -> tuple[str, str, str]:
    """
    Reads the main job posting and ALL candidate profiles.
    Returns (posting_text, all_profiles_text, error_message)
    """
    try:
        with open(os.path.join("data/postings", target_posting_file), "r") as f:
            posting_text = f.read()

        profile_files = os.listdir("data/profiles")
        all_profiles_text = ""
        for filename in profile_files:
            if filename.endswith(".txt"):
                with open(os.path.join("data/profiles", filename), "r") as f:
                    all_profiles_text += f"\n\n--- START OF PROFILE: {filename} ---\n"
                    all_profiles_text += f.read()
                    all_profiles_text += f"\n--- END OF PROFILE: {filename} ---"
        
        if not all_profiles_text:
            return None, None, "Error: No .txt files found in data/profiles/"

        return posting_text, all_profiles_text, None

    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}")
        return None, None, f"Error: {e.filename} not found."

# --- 4. Graph Nodes ---
def scanner_node(state: State):
    """
    Reads all necessary files from disk and prepares the
    state for the analyzer.
    """
    posting_file = state["target_posting_filename"]
    posting, profiles, error = get_files_for_recruiter_agent(posting_file)
    
    if error:
        return {"messages": [("system", error)]}

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
    Identify the 3 *most suitable* candidates.

    Respond with ONLY a Python-formatted list of the filenames for the
    most suitable profiles. If no profiles are suitable, return an empty list [].
    Example: ['candidate_profile_1.txt', 'candidate_profile_sofia.txt']
    """
    return {"messages": [("human", prompt)]}


def analyzer_node(state:State):
    """
    This is the LLM agent. It takes the big prompt
    and returns the list of suitable candidates.
    """
    if state["messages"][-1].content.startswith("Error:"):
        return {}
    
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# --- 5. Graph Definition Function ---
def get_recruiter_agent_graph():
    """
    Creates and returns the compiled graph for the recruiter agent.
    """
    graph_builder = StateGraph(State)
    graph_builder.add_node("scanner", scanner_node)
    graph_builder.add_node("analyzer", analyzer_node)
    graph_builder.set_entry_point("scanner")
    graph_builder.add_edge("scanner", "analyzer")
    graph_builder.add_edge("analyzer", END)
    return graph_builder.compile()
