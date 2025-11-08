import os
from dotenv import load_dotenv
from typing import Annotated, List, Tuple
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
    
    # --- INPUTS ---
    # The job posting we are judging
    target_posting_filename: str 
    # List A: Profiles the recruiter liked for this job
    recruiter_picks_list: List[str]
    # List B: Profiles who liked this job
    interested_profiles_list: List[str]
    
    # --- INTERNAL ---
    # The final list of mutual matches
    mutual_matches: List[str]

# --- 3. "Tool" Function (File Reader) ---
def get_file_texts(posting_filename: str, profile_filenames: List[str]) -> tuple[str, str, str]:
    """
    Reads the job posting and all matched profile texts from disk.
    Returns (posting_text, all_profiles_text, error_message)
    """
    try:
        with open(os.path.join("data/postings", posting_filename), "r") as f:
            posting_text = f.read()

        all_profiles_text = ""
        for filename in profile_filenames:
            with open(os.path.join("data/profiles", filename), "r") as f:
                all_profiles_text += f"\n\n--- START OF PROFILE: {filename} ---\n"
                all_profiles_text += f.read()
                all_profiles_text += f"\n--- END OF PROFILE: {filename} ---"
        
        return posting_text, all_profiles_text, None

    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}")
        return None, None, f"Error: {e.filename} not found."

# --- 4. Graph Nodes ---

def find_intersection_node(state: State):
    """
    Finds the candidates who appear on both the recruiter's
    list and the interested profiles list.
    """
    print("Judge: Finding mutual matches...")
    # Use set intersection to find common filenames
    recruiter_set = set(state["recruiter_picks_list"])
    interested_set = set(state["interested_profiles_list"])
    
    matches = list(recruiter_set.intersection(interested_set))
    print(f"Judge: Found {len(matches)} mutual match(es): {matches}")
    
    return {"mutual_matches": matches}

def prepare_judge_prompt_node(state: State):
    """
    Reads the full text for the job and all matched profiles,
    then creates the final prompt for the LLM judge.
    """
    print("Judge: Reading files for final analysis...")
    matches = state["mutual_matches"]
    posting_file = state["target_posting_filename"]
    
    posting_text, profiles_text, error = get_file_texts(posting_file, matches)
    
    if error:
        return {"messages": [("system", error)]}

    prompt = f"""
    You are the final Judge. You have received a list of mutual matches for a
    job posting. Your task is to perform a final, detailed analysis for *each*
    matched candidate and decide who is the best fit.

    --- JOB POSTING ---
    {posting_text}
    --- END JOB POSTING ---

    --- MUTUALLY MATCHED CANDIDATES ---
    {profiles_text}
    --- END CANDIDATES ---

    Please provide a detailed final assessment. Follow this structure:
    1.  **Overall Summary:** Briefly state how many candidates were analyzed.
    2.  **Candidate Rankings:**
        * **Rank 1 (Best Fit):** [filename of candidate]
        * **Rank 2 (Second Best):** [filename of candidate]
        * ...
    3.  **Detailed Justification:** For *each* candidate, provide a 2-3 sentence
        justification for their ranking, comparing their strengths and weaknesses
        directly against the job requirements.
    """
    
    return {"messages": [("human", prompt)]}

def judge_node(state: State):
    """
    The LLM judge makes its final decision based on the prepared prompt.
    """
    print("Judge: LLM is making the final decision...")
    
    # Check for error message
    if state["messages"][-1].content.startswith("Error:"):
        print("Judge: Skipping, error detected.")
        return {}
        
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def no_match_node(state: State):
    """
    This node is a dead-end if no mutual matches were found.
    """
    print("Judge: Process complete. No mutual matches found.")
    return {"messages": [("system", "No mutual matches found.")]}

# --- 5. Graph Definition (with Conditional Routing) ---

graph_builder = StateGraph(State)

# Add all the nodes
graph_builder.add_node("find_intersection", find_intersection_node)
graph_builder.add_node("prepare_prompt", prepare_judge_prompt_node)
graph_builder.add_node("judge", judge_node)
graph_builder.add_node("no_match", no_match_node)

# The graph starts by finding the intersection
graph_builder.set_entry_point("find_intersection")

def should_judge(state: State):
    """
    This function decides which node to go to next.
    If there are matches, go to 'prepare_prompt'.
    If not, go to 'no_match'.
    """
    if state["mutual_matches"]:
        return "prepare_prompt"
    else:
        return "no_match"

# Add the conditional edge
graph_builder.add_conditional_edges(
    "find_intersection",
    should_judge,
    {
        "prepare_prompt": "prepare_prompt",
        "no_match": "no_match"
    }
)

# Add the final edges
graph_builder.add_edge("prepare_prompt", "judge")
graph_builder.add_edge("judge", END)
graph_builder.add_edge("no_match", END)

# Compile the graph
graph = graph_builder.compile()

# --- 6. Run the Graph ---

# --- SIMULATE THE INPUTS FROM THE OTHER AGENTS ---
# In a real app, you would get these lists by running the other agents first.

# The job we are hiring for:
TARGET_JOB = "software_engineer_intern.txt" # The Software Engineer Intern job

# List A: From recruiter_agent.py (for job_posting.txt)
# The recruiter liked Sofia (candidate_profile.txt) but not Noah.
recruiter_picks = [
    'sofia_virtanen.txt' 
]

# List B: From running profile_agent.py for *all* profiles.
# Sofia (candidate_profile.txt) liked this job.
# Noah (candidate_profile_noah.txt) did *not* (he wants Customer Service).
interested_candidates = [
    'sofia_virtanen.txt',
    'noah_laine.txt'
]

# This input should find ONE match: candidate_profile.txt
input_data = {
    "target_posting_filename": TARGET_JOB,
    "recruiter_picks_list": recruiter_picks,
    "interested_profiles_list": interested_candidates
}

print("--- RUNNING JUDGE AGENT (Test 1: One Match) ---")
state = graph.invoke(input_data)

print("\n--- JUDGE'S FINAL VERDICT ---")
print(state["messages"][-1].content)