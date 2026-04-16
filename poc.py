import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db import initialize_db
from simulator import run_master_simulator
from evaluator import run_evaluation
import time

st.set_page_config(page_title="AgentCity Simulation", layout="wide")

def fetch_data(simulation_id: str):
    db = initialize_db()
    
    # Fetch simulation metadata
    sim_meta = db.simulations.find_one({"simulation_id": simulation_id})
    
    # Fetch screened agents
    agent_ids = sim_meta.get("screened_agents", []) if sim_meta else []
    agents = list(db.agents.find({"agent_id": {"$in": agent_ids}}))
    
    # Fetch events
    events = list(db.events.find({"simulation_id": simulation_id}))
    
    # Fetch base reactions
    reactions = list(db.base_reactions.find({"simulation_id": simulation_id}))
    
    # Fetch evaluations (we need all evaluations where event_id is matched with events in this string)
    event_ids = [e["event_id"] for e in events]
    evaluations = list(db.evaluations.find({"event_id": {"$in": event_ids}}))
    
    # Fetch decisions
    decisions = list(db.agent_decisions.find({"simulation_id": simulation_id}))
    
    # Fetch social media posts
    posts = list(db.social_media_posts.find({"simulation_id": simulation_id}))
    
    # Exclude _id to prevent serialization issues
    for item in agents + events + reactions + evaluations + decisions + posts:
        item.pop("_id", None)
    
    return {
        "metadata": sim_meta,
        "agents": agents,
        "events": events,
        "reactions": reactions,
        "evaluations": evaluations,
        "decisions": decisions,
        "posts": posts
    }

def main():
    st.title("AgentCity Simulation Analysis")
    
    policy_input = st.text_area("Enter Policy to be Tested", height=100, placeholder="e.g., The city will ban all single-use plastics starting next month.")
    run_sim = st.button("Run Simulation", type="primary")
    
    if run_sim and policy_input:
        with st.spinner("Running Simulation Process..."):
            status_container = st.empty()
            
            # Since running is a single blocking call, we'll indicate progress simply
            status_container.info("Analyzing the policy and Creating the city...")
            
            simulation_id = run_master_simulator(policy_input)
            
            status_container.info("Screening agents and running the policy...")
            
            status_container.info("Evaluating the reactions...")
            run_evaluation()
            
            status_container.success(f"Simulation completed! ID: {simulation_id}")
            st.session_state['simulation_id'] = simulation_id

    if 'simulation_id' in st.session_state:
        st.divider()
        data = fetch_data(st.session_state['simulation_id'])
        
        agent_dict = {a.get("agent_id"): a for a in data["agents"]}
        
        tab_metrics, tab_agents, tab_reactions, tab_decisions, tab_social = st.tabs([
            "Metrics & Results", 
            "Screened Agents", 
            "Events & Reactions", 
            "Decisions", 
            "Social Media Feed"
        ])
        
        # 1. Metrics & Results
        with tab_metrics:
            st.header("Evaluation Metrics")
            if data["evaluations"]:
                df_evals = pd.DataFrame(data["evaluations"])
                
                avg_happiness = df_evals['happiness'].mean()
                avg_angriness = df_evals['angriness'].mean()
                avg_loyalty = df_evals['loyalty_to_party'].mean()
                
                std_happiness = df_evals['happiness'].std()
                std_angriness = df_evals['angriness'].std()
                std_loyalty = df_evals['loyalty_to_party'].std()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Happiness", f"{avg_happiness:.3f}", delta=f"±{std_happiness:.3f}" if pd.notna(std_happiness) else "")
                col2.metric("Average Angriness", f"{avg_angriness:.3f}", delta=f"±{std_angriness:.3f}" if pd.notna(std_angriness) else "")
                col3.metric("Average Loyalty", f"{avg_loyalty:.3f}", delta=f"±{std_loyalty:.3f}" if pd.notna(std_loyalty) else "")
                
                st.subheader("Distribution of Emotional Metrics")
                fig = px.box(df_evals, y=['happiness', 'angriness', 'loyalty_to_party'], points="all", title="Metrics Distribution")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No evaluation data found for this simulation.")
                
        # 2. Agent Information
        with tab_agents:
            st.header("Screened Agents")
            for agent in data["agents"]:
                with st.expander(f"{agent.get('name', 'Unknown')}"):
                    st.write(f"**Age:** {agent.get('age', 'N/A')}")
                    st.write(f"**Occupation:** {agent.get('occupation', 'N/A')}")
                    st.write(f"**Income Level:** {agent.get('financial_score', 'N/A')}")
                    st.write(f"**Political Leaning:** {agent.get('political_leaning', 'N/A')}")
                    st.write(f"**Background:** {agent.get('persona', 'N/A')}")
        
        # 3. Events & Base Reactions
        with tab_reactions:
            st.header("Events & Base Reactions")
            # Map events easily
            event_dict = {e["event_id"]: e for e in data["events"]}
            
            for reaction in data["reactions"]:
                event = event_dict.get(reaction["event_id"], {})
                agent = agent_dict.get(reaction["agent_id"], {})
                
                with st.container():
                    st.markdown(f"### Agent: {agent.get('name', 'Unknown')}")
                    st.info(f"**Event Context:**\n{event.get('event_description', 'No description available')}")
                    st.warning(f"**Base Reaction:**\n{reaction.get('base_reaction', 'No reaction')}")
                    st.divider()
                    
        # 4. Decisions
        with tab_decisions:
            st.header("Agent Decisions")
            if data["decisions"]:
                for decision in data["decisions"]:
                    agent = agent_dict.get(decision.get("agent_id"), {})
                    agent_name = agent.get("name", "Unknown Agent")
                    
                    dec_info = decision.get("decision", {})
                    # Clean out any ID fields from display
                    safe_dec_info = {k: v for k, v in dec_info.items() if not k.endswith("_id")}
                    
                    st.markdown(f"### {agent_name}")
                    for k, v in safe_dec_info.items():
                        st.write(f"**{k.capitalize()}:** {v}")
                    st.divider()
            else:
                st.info("No decisions recorded in this simulation.")
                
        # 5. Social Media Feed
        with tab_social:
            st.header("Social Media Feed")
            if data["posts"]:
                # Sort posts by time if possible
                sorted_posts = sorted(data["posts"], key=lambda x: x.get("timestamp", ""), reverse=True)
                for post in sorted_posts:
                    agent = agent_dict.get(post.get("agent_id"), {})
                    agent_name = agent.get("name", "Unknown User")
                    
                    post_content = post.get("post", {})
                    platform = post_content.get("platform", "Social Media")
                    content = post_content.get("content", "No content")
                    
                    with st.chat_message("user"):
                        st.markdown(f"**{agent_name}** on {platform}")
                        st.write(content)
            else:
                st.info("No social media posts were generated.")
                
if __name__ == "__main__":
    main()
