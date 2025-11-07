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
    main_profile: str
    all_postings: str

# --- 3. "Tool" Function (File Reader) ---
def get_files_for_profile_agent():
    """
    Reads the main candidate profile and ALL job postings.
    Returns them as two large strings.
    """
    try:
        # Load the single profile we are acting for
        with open("data/profiles/noah_laine.txt", "r") as f:
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
            return None, "Error: No .txt files found in data/postings/"

        return profile_text, all_postings_text

    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}")
        return None, f"Error: {e.filename} not found."

# --- 4. Graph Nodes ---

def scanner_node(state: State):
    """
    Reads all necessary files from disk and prepares the
    state for the analyzer.
    """
    print("Profile Agent: Reading my profile and all job postings...")
    profile, postings = get_files_for_profile_agent()
    
    if "Error:" in postings:
        # If there's an error, add it as a message to stop the graph
        return {"messages": [("system", postings)]}

# Create the prompt for the LLM
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
        candidate's primary job function and field of interest (e.g., 'Software Engineer',
        'Financial Analyst') based on their **education, skills, and projects**.
    2.  **Filter Postings:** Second, scan 'ALL POSTINGS' and create a filtered list
        of jobs that *strictly match* this primary job function.
    3.  **CRITICAL RULE:** **You MUST ignore** postings that do not align with the
        candidate's clear career path. For example, do NOT suggest a 'Customer Service'
        job to a 'Software Engineer' candidate.
    4.  **Rank Filtered List:** From the *filtered list only*, identify the top 3
        most suitable job postings.
    5.  **Format Output:** Respond with ONLY a Python-formatted list of the filenames
        for the most suitable postings. If no postings are suitable, return an empty list [].

    Example Output: ['job_posting.txt', 'job_posting_tech.txt']
    """ 
    
    return {"messages": [("human", prompt)]}


def analyzer_node(state:State):
    """
    This is the LLM agent. It takes the big prompt
    and returns the list of suitable jobs.
    """
    print("Profile Agent: Analyzing... Which jobs are best for me?")
    
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
print("--- RUNNING PROFILE AGENT ---")
state = graph.invoke({})

print("\n--- PROFILE AGENT'S SUITABLE POSTINGS ---")
# The final message content will be the list you can pass to the judge
print(state["messages"][-1].content)