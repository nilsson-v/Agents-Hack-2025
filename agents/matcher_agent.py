import os
import ast  # For safely evaluating the LLM's list-as-a-string output
from profile_agent import get_profile_agent_graph
from recruiter_agent import get_recruiter_agent_graph
from judge_agent import get_judge_agent_graph

# --- 1. Get all files ---
try:
    all_posting_files = [f for f in os.listdir("data/postings") if f.endswith('.txt')]
    all_profile_files = [f for f in os.listdir("data/profiles") if f.endswith('.txt')]
except FileNotFoundError as e:
    print(f"Error: Directory not found. Make sure 'data/postings' and 'data/profiles' exist.")
    exit()

print(f"Found {len(all_posting_files)} postings and {len(all_profile_files)} profiles.")

# --- 2. Compile all agent graphs ---
profile_agent = get_profile_agent_graph()
recruiter_agent = get_recruiter_agent_graph()
judge_agent = get_judge_agent_graph()

# This dictionary will hold all the "session lists"
match_database = {}

# --- 3. Run Recruiter Agent for EACH posting ---
print("\n--- Running Recruiter Agents ---")
for posting_file in all_posting_files:
    print(f"Recruiter is analyzing: {posting_file}")
    
    # The input state for the recruiter
    recruiter_input = {"target_posting_filename": posting_file}
    
    # Run the recruiter graph
    recruiter_state = recruiter_agent.invoke(recruiter_input)
    recruiter_picks_str = recruiter_state["messages"][-1].content
    
    try:
        # The LLM gives us a string "['file1.txt']", ast.literal_eval turns it into a real list
        recruiter_picks_list = ast.literal_eval(recruiter_picks_str)
    except Exception:
        print(f"  Warning: Recruiter LLM returned bad format for {posting_file}. Skipping.")
        recruiter_picks_list = []

    # Store the recruiter's picks in our database
    match_database[posting_file] = {
        "recruiter_picks": recruiter_picks_list,
        "interested_profiles": []  # Initialize empty list for profiles
    }

# --- 4. Run Profile Agent for EACH profile ---
print("\n--- Running Profile Agents ---")
for profile_file in all_profile_files:
    print(f"Profile agent is analyzing: {profile_file}")
    
    # The input state for the profile agent
    profile_input = {"target_profile_filename": profile_file}
    
    # Run the profile graph
    profile_state = profile_agent.invoke(profile_input)
    profile_picks_str = profile_state["messages"][-1].content

    try:
        profile_picks_list = ast.literal_eval(profile_picks_str)
    except Exception:
        print(f"  Warning: Profile LLM returned bad format for {profile_file}. Skipping.")
        profile_picks_list = []

    # Add this profile to the "interested_profiles" list for each job it liked
    for posting_file in profile_picks_list:
        if posting_file in match_database:
            match_database[posting_file]["interested_profiles"].append(profile_file)
        else:
            print(f"  Warning: Profile agent for {profile_file} liked a non-existent job: {posting_file}")

# --- 5. Run Judge Agent for EACH posting ---
print("\n--- Running Judge Agents ---")
print("==========================================")

for posting_file, data in match_database.items():
    print(f"\n--- FINAL VERDICT FOR: {posting_file} ---")
    
    # The input for the judge is the "session lists" we built
    judge_input = {
        "target_posting_filename": posting_file,
        "recruiter_picks_list": data["recruiter_picks"],
        "interested_profiles_list": data["interested_profiles"]
    }

    # Run the judge graph
    judge_state = judge_agent.invoke(judge_input)
    
    # Print the final verdict from the judge
    print(judge_state["messages"][-1].content)
    print("==========================================")

print("\n--- Matchmaking complete. ---")