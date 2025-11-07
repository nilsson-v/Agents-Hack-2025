from dotenv import load_dotenv
from typing import Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash" # Using 1.5-flash as 2.5 is likely a typo
)

# --- 2. State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- 3. "Tool" Function (File Reader) ---
def get_analysis_prompt():
    """
    Reads the job posting and candidate profile from disk
    and formats them into a prompt for the judge.
    """
    try:
        with open("data/profiles/sofia_virtanen.txt", "r") as f:
            profile_text = f.read()
        with open("data/postings/software_engineer_intern.txt", "r") as f:
            job_text = f.read()
    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}")
        # Return a message to stop the graph
        return "Error: Could not read files. Make sure candidate_profile.txt and job_posting.txt are in the same directory."

    # This prompt guides the LLM judge
    return f"""
    You are an expert Senior Software Engineer acting as a hiring manager.
    Your task is to analyze a candidate's suitability for an internship.

    First, here is the job posting:
    ---JOB POSTING---
    {job_text}
    ---END JOB POSTING---

    Next, here is the candidate's profile:
    ---CANDIDATE PROFILE---
    {profile_text}
    ---END CANDIDATE PROFILE---

    Please provide a detailed analysis and a final judgment. Follow this structure:
    1.  **Direct Comparison:** List the main 'Qualifications' from the job and state 'MATCH', 'PARTIAL MATCH', or 'NO MATCH' based on the candidate's profile, with a brief reason.
    2.  **Project Analysis:** Briefly analyze if the candidate's GitHub projects are relevant to the role.
    3.  **Final Judgment:** Conclude with a final suitability rating (e.g., "Strong Fit", "Good Fit", "Partial Fit", "Not a Good Fit") and a 2-3 sentence justification.
    """

# --- 4. Graph Nodes ---

def analyzer_node(state: State):
    """
    This is the "task" node. It calls the "tool" (get_analysis_prompt)
    and adds the analysis prompt to the message list.
    """
    print("Analyzer Node: Reading files and preparing prompt...")
    analysis_prompt = get_analysis_prompt()
    
    return {"messages": [("human", analysis_prompt)]}


def judge_node(state:State):
    """
    This is the "LLM as a judge" node.
    It takes the prompt from the analyzer and invokes the LLM.
    """
    print("Judge Node: LLM is making a decision...")
    
    # Access the .content attribute, not the [1] index
    if state["messages"][-1].content.startswith("Error:"):
        print("Judge Node: Skipping, error detected in previous step.")
        return {} # Do nothing

    response = llm.invoke(state["messages"])
    
    return {"messages": [response]}

# --- 5. Graph Definition ---

graph_builder = StateGraph(State)

graph_builder.add_node("analyzer", analyzer_node)
graph_builder.add_node("judge", judge_node)

graph_builder.set_entry_point("analyzer")
graph_builder.add_edge("analyzer", "judge")
graph_builder.add_edge("judge", END)

graph = graph_builder.compile()

# --- 6. Run the Graph ---

print("Running candidate-job matching analysis...")
state = graph.invoke({})

print("\n--- JUDGE'S ANALYSIS ---")
print(state["messages"][-1].content)