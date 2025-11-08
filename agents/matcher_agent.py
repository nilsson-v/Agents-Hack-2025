import os
import ast  # For safely evaluating the LLM's list-as-a-string output
# --- THIS IS THE FIX ---
from .profile_agent import get_profile_agent_graph
from .recruiter_agent import get_recruiter_agent_graph
from .judge_agent import get_judge_agent_graph
# -----------------------

# --- This is the main function your API server will call ---
def run_full_matchmaking():
    """
    Runs the entire matchmaking process and returns a dictionary of verdicts.
    """
    
    # --- 1. Get all files ---
    try:
        all_posting_files = [f for f in os.listdir("data/postings") if f.endswith('.txt')]
        all_profile_files = [f for f in os.listdir("data/profiles") if f.endswith('.txt')]
    except FileNotFoundError as e:
        print(f"Error: Directory not found. {e}")
        return {"error": f"Directory not found. {e}"}

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
            print(f"  [Recruiter Agent Debug]: LLM returned list: {recruiter_picks_list}")
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
            print(f"  [Profile Agent Debug]: LLM returned list: {profile_picks_list}")
        except Exception:
            print(f"  Warning: Profile LLM returned bad format for {profile_file}. Skipping.")
            profile_picks_list = []

        # Add this profile to the "interested_profiles" list for each job it liked
        for posting_file in profile_picks_list:
            if posting_file in match_database:
                match_database[posting_file]["interested_profiles"].append(profile_file)
            else:
                print(f"  Warning: Profile agent for {profile_file} liked a non-existent job: {posting_file}")

    # --- 5. Run Judge Agent (Optional: Only for collecting mutual matches) ---
    print("\n--- Running Judge Agents ---")
    
    # Initialize the list to store only the final mutual matches
    final_match_list = []

    for posting_file, data in match_database.items():
        # --- Run the Judge Agent to get the final verdict (if needed) ---
        # Note: We still run the judge agent, but we are primarily interested
        # in the 'mutual_matches' we calculated before the judge runs.
        judge_input = {
            "target_posting_filename": posting_file,
            "recruiter_picks_list": data["recruiter_picks"],
            "interested_profiles_list": data["interested_profiles"]
        }

        # Run the judge graph
        judge_state = judge_agent.invoke(judge_input)
        verdict = judge_state["messages"][-1].content # Keep the full verdict for completeness

        # Calculate the mutual matches
        mutual_matches = list(set(data["recruiter_picks"]) & set(data["interested_profiles"]))

        # Check if there are any mutual matches before adding to the list
        if mutual_matches:
            final_match_list.append({
                "posting_file": posting_file,
                "mutual_matches": mutual_matches,
                "verdict": verdict # Optionally include the full verdict string
            })


    print("\n--- Matchmaking complete. ---")
    
    # --- RETURN THE SIMPLIFIED LIST ---
    print(final_match_list)
    return final_match_list