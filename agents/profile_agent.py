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
    
    # --- Option 1: For batch job ---
    target_profile_filename: str | None = None
    
    # --- Option 2: For on-demand API ---
    profile_text: str | None = None


# --- 3. Graph Nodes ---
def scanner_node(state: State):
    """
    Reads all necessary files from disk OR uses profile_text from state.
    """
    print("Profile Agent: Reading profile and all job postings...")
    
    # This is the new flexible logic
    profile_text = ""
    if state.get("target_profile_filename"):
        # Logic for batch job (your original method)
        print(f"  Mode: File ({state['target_profile_filename']})")
        profile_file = state["target_profile_filename"]
        try:
            with open(os.path.join("data/profiles", profile_file), "r") as f:
                profile_text = f.read()
        except FileNotFoundError as e:
            return {"messages": [("system", f"Error: {e.filename} not found.")]}
            
    elif state.get("profile_text"):
        # Logic for on-demand API
        print("  Mode: Raw text input")
        profile_text = state["profile_text"]
    else:
        return {"messages": [("system", "Error: No profile_text or target_profile_filename provided.")]}

    # --- This part is the same as before ---
    
    # Scan and load ALL job postings
    try:
        posting_files = os.listdir("data/postings")
        all_postings_text = ""
        for filename in posting_files:
            if filename.endswith(".txt"):
                with open(os.path.join("data/postings", filename), "r") as f:
                    all_postings_text += f"\n\n--- START OF POSTING: {filename} ---\n"
                    all_postings_text += f.read()
                    all_postings_text += f"\n--- END OF POSTING: {filename} ---"
        if not all_postings_text:
            return {"messages": [("system", "Error: No .txt files found in data/postings/")]}
    except FileNotFoundError as e:
        return {"messages": [("system", f"Error: Could not read postings directory. {e}")]}
    prompt = f"""
    You are a meticulous job-seeking agent. Your task is to find the *most relevant*
    jobs for your candidate and filter out all irrelevant ones.

    Here is your candidate's profile:
    ---MY PROFILE---
    {profile_text}
    ---END MY PROFILE---

    Here are all the available job postings:
    ---ALL POSTINGS---
    {all_postings_text}
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

    print(f"Suitable postings: {response.content}")

    return {"messages": [response]}

# --- 4. Graph Definition Function ---
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
