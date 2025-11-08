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
    target_profile_filename: str

# --- 3. "Tool" Function (File Reader) ---
def get_files_for_profile_agent(target_profile_file: str) -> tuple[str, str, str]:
    """
    Reads the main candidate profile and ALL job postings.
    Returns (profile_text, all_postings_text, error_message)
    """
    try:
        # Load the single profile we are acting for
        with open(os.path.join("data/profiles", target_profile_file), "r") as f:
            profile_text = f.read()

        # Scan and load ALL job postings
        posting_files = os.listdir("data/postings")
        all_postings_text = ""
        for filename in posting_files:
            if filename.endswith(".txt"):
                with open(os.path.join("data/postings", filename), "r") as f:
                    all_postings_text += f"\n\n--- START OF POSTING: {filename} ---\n"
                    all_postings_text += f.read()
                    all_postings_text += f"\n--- END OF POSTING: {filename} ---"
        
        if not all_postings_text:
            return None, None, "Error: No .txt files found in data/postings/"

        return profile_text, all_postings_text, None

    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}")
        return None, None, f"Error: {e.filename} not found."

# --- 4. Graph Nodes ---
def scanner_node(state: State):
    """
    Reads all necessary files from disk and prepares the
    state for the analyzer.
    """
    profile_file = state["target_profile_filename"]
    profile, postings, error = get_files_for_profile_agent(profile_file)
    
    if error:
        return {"messages": [("system", error)]}

    prompt = f"""
    You are a meticulous job-seeking agent. Your task is to find the *most relevant*
    jobs for your candidate and filter out all irrelevant ones.

    Here is your candidate's profile:
    ---MY PROFILE---
    {profile}
    ---END MY PROFILE---

    Here are all the available job postings:
    ---ALL POSTINGS---
    {postings}
    ---END ALL POSTINGS---

    Follow these steps precisely:
    1.  **Analyze Profile:** First, analyze the 'MY PROFILE' section to determine the
        candidate's primary job function (e.g., 'Software Engineer').
    2.  **Filter Postings:** Second, scan 'ALL POSTINGS' and create a filtered list
        of jobs that *strictly match* this primary job function.
    3.  **CRITICAL RULE:** **You MUST ignore** postings that do not align with the
        candidate's clear career path.
    4.  **Format Output:** Respond with ONLY a Python-formatted list of the filenames
        for the most suitable postings. If no postings are suitable, return an empty list [].

    Example Output: ['job_posting.txt', 'job_posting_tech.txt']
    """
    return {"messages": [("human", prompt)]}

def analyzer_node(state:State):
    """
    This is the LLM agent. It takes the big prompt
    and returns the list of suitable jobs.
    """
    if state["messages"][-1].content.startswith("Error:"):
        return {}
    
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# --- 5. Graph Definition Function ---
def get_profile_agent_graph():
    """
    Creates and returns the compiled graph for the profile agent.
    """
    graph_builder = StateGraph(State)
    graph_builder.add_node("scanner", scanner_node)
    graph_builder.add_node("analyzer", analyzer_node)
    graph_builder.set_entry_point("scanner")
    graph_builder.add_edge("scanner", "analyzer")
    graph_builder.add_edge("analyzer", END)
    return graph_builder.compile()
