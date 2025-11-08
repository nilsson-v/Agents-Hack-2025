import os
from dotenv import load_dotenv
from typing import Annotated, List, Tuple
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
    target_posting_filename: str 
    recruiter_picks_list: List[str]
    interested_profiles_list: List[str]
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
            if not filename.strip(): # Skip empty filenames
                continue
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
    recruiter_set = set(state["recruiter_picks_list"])
    interested_set = set(state["interested_profiles_list"])
    
    matches = list(recruiter_set.intersection(interested_set))
    print(f"  Judge: Found {len(matches)} mutual match(es): {matches}")
    
    return {"mutual_matches": matches}

def prepare_judge_prompt_node(state: State):
    """
    Reads the full text for the job and all matched profiles,
    then creates the final prompt for the LLM judge.
    """
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

    Please provide a final assessment.
    You should be very precise and see if the person actually matches with the posting. Analyze the responsibilites and qualifications very thouroghly 
    and if the person lacks more than one qualifications they are not deemed fit.
    """
    return {"messages": [("human", prompt)]}

def judge_node(state: State):
    """
    The LLM judge makes its final decision based on the prepared prompt.
    """
    if state["messages"][-1].content.startswith("Error:"):
        return {}
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def no_match_node(state: State):
    """
This node is a dead-end if no mutual matches were found.
    """
    return {"messages": [("system", "No mutual matches found.")]}

# --- 5. Graph Definition Function ---
def get_judge_agent_graph():
    """
    Creates and returns the compiled graph for the judge agent.
    """
    graph_builder = StateGraph(State)

    graph_builder.add_node("find_intersection", find_intersection_node)
    graph_builder.add_node("prepare_prompt", prepare_judge_prompt_node)
    graph_builder.add_node("judge", judge_node)
    graph_builder.add_node("no_match", no_match_node)

    graph_builder.set_entry_point("find_intersection")

    def should_judge(state: State):
        if state["mutual_matches"]:
            return "prepare_prompt"
        else:
            return "no_match"

    graph_builder.add_conditional_edges(
        "find_intersection",
        should_judge,
        {"prepare_prompt": "prepare_prompt", "no_match": "no_match"}
    )
    graph_builder.add_edge("prepare_prompt", "judge")
    graph_builder.add_edge("judge", END)
    graph_builder.add_edge("no_match", END)

    return graph_builder.compile()

# --- 6. (REMOVED) ---
# We no longer run the graph from this file.