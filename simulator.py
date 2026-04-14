"""
MasterSimulatorGraph Implementation

Orchestrates a multi-node simulation workflow:
- Node 1: Screen agents based on policy vector
- Node 2: Generate events from policy and agent details
- Node 3: Generate base reactions from agents
- Node 4: Execute agents in parallel with tool calling
- Node 5: Push all results to MongoDB
"""

import os
import json
import uuid
from typing import List, Dict, Any, Annotated, TypedDict, Literal
import operator
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from langchain_core.messages import BaseMessage, HumanMessage
from schemas.screener import ScreenConfig, AgentScreener
from schemas.events import Event, EventList
from events.generator import create_event_objects
from events.runner.base_reaction import generate_base_reactions
from events.runner.agent_executor import build_agent_executor_graph
from llm.factory import LLMFactory, LLMConfig, LLMProvider
from utils.general import generate_agent_details_string, generate_agent_data, generate_event_objects
from utils.vectorize import vectorize_policy
from db import initialize_db

# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class ExecutionResult(TypedDict):
    """Result from executing a single agent on an event"""
    event_id: str
    agent_id: str
    event_description: str
    execution_trace: List[BaseMessage]
    decisions: List[Dict[str, Any]]
    social_media_posts: List[Dict[str, Any]]
    agent_interactions: List[Dict[str, Any]]
    termination_reason: str


class MasterSimulatorState(TypedDict):
    """Main state for the MasterSimulatorGraph"""
    # Input
    policy_text: str
    
    # Node 1: Screening
    screened_agent_ids: List[str]
    agent_details_string: str
    policy_vector: Dict[str, float]
    
    # Node 2: Event Generation
    event_list_objects: List[Event]
    
    # Node 3: Base Reactions
    base_reactions: List[Dict[str, str]]
    
    # Node 4: Agent Execution
    execution_details: Annotated[List[ExecutionResult], operator.add]
    
    # Metadata
    simulation_id: str
    timestamp: str
    status: str


# ============================================================================
# NODE 1: SCREENING AGENTS
# ============================================================================

def node_1_screening_agents(state: MasterSimulatorState) -> Dict[str, Any]:
    """
    Node 1: Convert policy text to vector and screen exactly 15 agents
    
    Steps:
    1. Vectorize policy text to get policy vector
    2. Initialize screener with policy vector
    3. Screen agents to get top 15
    4. Generate agent details string
    """
    print("=" * 80)
    print("NODE 1: SCREENING AGENTS")
    print("=" * 80)
    
    policy_text = state["policy_text"]
    
    # Step 1: Vectorize policy text to get policy vector
    print(f"\n1. Vectorizing policy text...")
    llm_config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile")
    llm = LLMFactory.build(llm_config)
    
    # Use vectorize_policy method to convert policy to vector
    policy_vector = vectorize_policy(llm, policy_text)
    print(f"✓ Policy vector obtained: {policy_vector}")
    
    # Step 2: Initialize screener with exactly 15 agents
    print(f"\n2. Screening exactly 15 agents based on policy vector...")
    policy_weight = policy_vector
    
    agent_profiles_path = os.path.join(os.path.dirname(__file__), "agent_profiles.json")
    screen_config = ScreenConfig(
        policy_weight=policy_weight,
        population_size=15,  # Screen exactly 15 agents
        profile_path=agent_profiles_path
    )
    
    screener = AgentScreener(config=screen_config)
    screened_agent_ids = screener.screen_agents()
    
    print(f"✓ Screened {len(screened_agent_ids)} agents: {screened_agent_ids}")
    
    # Step 3: Generate agent details string
    print(f"\n3. Generating agent details string...")
    agent_details_string = generate_agent_details_string(screened_agent_ids)
    print(f"✓ Agent details string generated (length: {len(agent_details_string)} chars)")
    
    return {
        "screened_agent_ids": screened_agent_ids,
        "agent_details_string": agent_details_string,
        "policy_vector": policy_vector,
        "status": "agents_screened"
    }


# ============================================================================
# NODE 2: EVENT GENERATION
# ============================================================================

def node_2_event_generation(state: MasterSimulatorState) -> Dict[str, Any]:
    """
    Node 2: Generate events from policy text and agent details
    
    Steps:
    1. Initialize LLM
    2. Call create_event_objects with policy text and agent details
    3. Return event objects
    """
    print("\n" + "=" * 80)
    print("NODE 2: EVENT GENERATION")
    print("=" * 80)
    
    policy_text = state["policy_text"]
    agent_details_string = state["agent_details_string"]
    
    # Step 1: Initialize Groq LLM
    print(f"\n1. Initializing LLM for event generation...")
    llm_config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile")
    llm = LLMFactory.build(llm_config)
    print(f"✓ LLM initialized: {llm_config.model_name}")
    
    # Step 2: Create event objects
    print(f"\n2. Generating events from policy and agent details...")
    try:
        event_list_objects = create_event_objects(llm, policy_text, agent_details_string)
        print(f"✓ Generated {len(event_list_objects)} events")
        
        # Print event summary
        for i, event in enumerate(event_list_objects[:3], 1):
            print(f"   Event {i}: {event.event_id} (Agent: {event.agent_id}, Timeline: {event.timeline})")
        if len(event_list_objects) > 3:
            print(f"   ... and {len(event_list_objects) - 3} more events")
    except Exception as e:
        print(f"⚠️ Error generating events: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list to proceed to next node
        event_list_objects = []
    
    return {
        "event_list_objects": event_list_objects,
        "status": "events_generated"
    }


# ============================================================================
# NODE 3: BASE REACTION GENERATION
# ============================================================================

def node_3_base_reaction_generation(state: MasterSimulatorState) -> Dict[str, Any]:
    """
    Node 3: Generate base reactions for all events
    
    Steps:
    1. Initialize Groq LLM
    2. Call generate_base_reactions with event list
    3. Return base reaction list
    """
    print("\n" + "=" * 80)
    print("NODE 3: BASE REACTION GENERATOR")
    print("=" * 80)
    
    event_list_objects = state["event_list_objects"]
    
    if not event_list_objects:
        print("\n⚠️ No events provided. Skipping base reactions.")
        return {
            "base_reactions": [],
            "status": "base_reactions_generated"
        }
    
    # Step 1: Initialize Groq LLM
    print(f"\n1. Initializing LLM for base reactions...")
    llm_config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile")
    llm = LLMFactory.build(llm_config)
    print(f"✓ LLM initialized: {llm_config.model_name}")
    
    # Step 2: Generate base reactions
    print(f"\n2. Generating base reactions for {len(event_list_objects)} events...")
    try:
        base_reactions = generate_base_reactions(event_list_objects, llm)
        print(f"✓ Generated {len(base_reactions)} base reactions")
        
        # Print reaction summary
        for i, reaction in enumerate(base_reactions[:3], 1):
            print(f"   Reaction {i}: {reaction.get('event_id')} (Agent: {reaction.get('agent_id')})")
        if len(base_reactions) > 3:
            print(f"   ... and {len(base_reactions) - 3} more reactions")
    except Exception as e:
        print(f"⚠️ Error generating base reactions: {e}")
        base_reactions = []
    
    return {
        "base_reactions": base_reactions,
        "status": "base_reactions_generated"
    }


# ============================================================================
# NODE 4: AGENT EXECUTION (PARALLEL MAP-REDUCE)
# ============================================================================

def node_4_agent_execution(state: MasterSimulatorState) -> Dict[str, Any]:
    """
    Node 4: Execute all agents in parallel using map-reduce pattern
    
    For each event, execute the corresponding agent in parallel.
    Collects all execution results.
    """
    print(f"\n" + "=" * 80)
    print(f"NODE 4: AGENT EXECUTOR (PARALLEL)")
    print(f"=" * 80)
    
    event_list = state["event_list_objects"]
    
    if not event_list:
        print("\n⚠️ No events provided. Skipping agent execution.")
        return {
            "execution_details": [],
            "status": "agents_executed"
        }
    
    print(f"\n1. Executing {len(event_list)} agents in parallel...")
    
    execution_results = []
    
    # Execute each agent-event pair
    for event in event_list:
        event_description = " ".join(event.event_description) if isinstance(event.event_description, list) else event.event_description
        
        try:
            # Get agent data
            agent_data = generate_agent_data(event.agent_id)
            
            print(f"\n   Executing Agent {event.agent_id} on Event {event.event_id}...")
            
            # Build executor subgraph
            executor_graph = build_agent_executor_graph(
                agent_id=event.agent_id,
                event_id=event.event_id,
                event_description=event_description,
                agent_data=agent_data
            )
            
            # Execute the graph
            initial_input = {
                "messages": [HumanMessage(content=event_description)],
                "agent_id": event.agent_id,
                "event_id": event.event_id,
                "event_description": event_description,
                "agent_data": agent_data,
                "termination_reason": ""
            }
            
            result = executor_graph.invoke(initial_input)
            
            # Extract execution details from result
            execution_result: ExecutionResult = {
                "event_id": event.event_id,
                "agent_id": event.agent_id,
                "event_description": event_description,
                "execution_trace": result.get("messages", []),
                "decisions": [],
                "social_media_posts": [],
                "agent_interactions": [],
                "termination_reason": result.get("termination_reason", "completed")
            }
            
            # Parse messages for tool calls and results
            for msg in result.get("messages", []):
                if hasattr(msg, "tool_calls"):
                    for tool_call in msg.tool_calls:
                        if tool_call["name"] == "make_decision":
                            execution_result["decisions"].append(tool_call["args"])
                        elif tool_call["name"] == "post_social_media":
                            execution_result["social_media_posts"].append(tool_call["args"])
                        elif tool_call["name"] == "chat_with_agent":
                            execution_result["agent_interactions"].append(tool_call["args"])
            
            execution_results.append(execution_result)
            print(f"   ✓ Agent {event.agent_id} completed execution")
            
        except Exception as e:
            print(f"   ⚠️ Error executing Agent {event.agent_id}: {e}")
            execution_results.append({
                "event_id": event.event_id,
                "agent_id": event.agent_id,
                "event_description": event_description,
                "execution_trace": [],
                "decisions": [],
                "social_media_posts": [],
                "agent_interactions": [],
                "termination_reason": f"error: {str(e)}"
            })
    
    print(f"\n✓ Agent execution completed. Collected {len(execution_results)} execution results")
    
    return {
        "execution_details": execution_results,
        "status": "agents_executed"
    }


# ============================================================================
# NODE 5: PUSH TO DATABASE
# ============================================================================

def node_5_push_to_database(state: MasterSimulatorState) -> Dict[str, Any]:
    """
    Node 5: Push all results to MongoDB
    
    Stores:
    1. Base reactions
    2. Agent executions (decisions, interactions, social media posts)
    3. Events
    
    Each in separate collections
    """
    print("\n" + "=" * 80)
    print("NODE 5: PUSH TO DATABASE")
    print("=" * 80)
    
    db = initialize_db()
    simulation_id = state["simulation_id"]
    timestamp = state["timestamp"]
    
    # Prepare collections
    events_collection = db["events"]
    base_reactions_collection = db["base_reactions"]
    agent_decisions_collection = db["agent_decisions"]
    social_media_posts_collection = db["social_media_posts"]
    agent_interactions_collection = db["agent_interactions"]
    simulations_collection = db["simulations"]
    
    print(f"\n1. Pushing events...")
    events_to_insert = []
    for event in state.get("event_list_objects", []):
        event_doc = {
            "simulation_id": simulation_id,
            "event_id": event.event_id,
            "event_description": event.event_description,
            "timeline": event.timeline,
            "agent_id": event.agent_id,
            "timestamp": timestamp
        }
        events_to_insert.append(event_doc)
    
    if events_to_insert:
        result = events_collection.insert_many(events_to_insert)
        print(f"   ✓ Inserted {len(result.inserted_ids)} events")
    
    print(f"\n2. Pushing base reactions...")
    reactions_to_insert = []
    for reaction in state.get("base_reactions", []):
        reaction_doc = {
            "simulation_id": simulation_id,
            "event_id": reaction.get("event_id"),
            "agent_id": reaction.get("agent_id"),
            "base_reaction": reaction.get("base_reaction"),
            "timestamp": timestamp
        }
        reactions_to_insert.append(reaction_doc)
    
    if reactions_to_insert:
        result = base_reactions_collection.insert_many(reactions_to_insert)
        print(f"   ✓ Inserted {len(result.inserted_ids)} base reactions")
    
    print(f"\n3. Pushing agent executions...")
    decisions_list = []
    posts_list = []
    interactions_list = []
    
    for execution in state.get("execution_details", []):
        # Insert decisions
        for decision in execution.get("decisions", []):
            decision_doc = {
                "simulation_id": simulation_id,
                "event_id": execution["event_id"],
                "agent_id": execution["agent_id"],
                "decision": decision,
                "timestamp": timestamp
            }
            decisions_list.append(decision_doc)
        
        # Insert social media posts
        for post in execution.get("social_media_posts", []):
            post_doc = {
                "simulation_id": simulation_id,
                "event_id": execution["event_id"],
                "agent_id": execution["agent_id"],
                "post": post,
                "timestamp": timestamp
            }
            posts_list.append(post_doc)
        
        # Insert agent interactions
        for interaction in execution.get("agent_interactions", []):
            interaction_doc = {
                "simulation_id": simulation_id,
                "event_id": execution["event_id"],
                "agent_id": execution["agent_id"],
                "interaction": interaction,
                "timestamp": timestamp
            }
            interactions_list.append(interaction_doc)
    
    if decisions_list:
        result = agent_decisions_collection.insert_many(decisions_list)
        print(f"   ✓ Inserted {len(result.inserted_ids)} decisions")
    
    if posts_list:
        result = social_media_posts_collection.insert_many(posts_list)
        print(f"   ✓ Inserted {len(result.inserted_ids)} social media posts")
    
    if interactions_list:
        result = agent_interactions_collection.insert_many(interactions_list)
        print(f"   ✓ Inserted {len(result.inserted_ids)} agent interactions")
    
    # Insert simulation metadata
    print(f"\n4. Pushing simulation metadata...")
    simulation_doc = {
        "simulation_id": simulation_id,
        "policy_text": state["policy_text"],
        "screened_agents": state.get("screened_agent_ids", []),
        "total_events": len(state.get("event_list_objects", [])),
        "total_reactions": len(state.get("base_reactions", [])),
        "total_executions": len(state.get("execution_details", [])),
        "timestamp": timestamp,
        "status": "completed"
    }
    result = simulations_collection.insert_one(simulation_doc)
    print(f"   ✓ Inserted simulation metadata")
    
    print(f"\n✓ All data pushed to MongoDB successfully!")
    
    return {
        "status": "data_pushed"
    }


# ============================================================================
# BUILD MASTER SIMULATOR GRAPH
# ============================================================================

def build_master_simulator_graph():
    """
    Build and return the MasterSimulatorGraph
    
    Orchestrates:
    - Node 1: Screen agents
    - Node 2: Generate events
    - Node 3: Generate base reactions
    - Node 4: Execute agents in parallel
    - Node 5: Push to database
    """
    graph = StateGraph(MasterSimulatorState)
    
    # Add nodes
    graph.add_node("screen_agents", node_1_screening_agents)
    graph.add_node("generate_events", node_2_event_generation)
    graph.add_node("generate_reactions", node_3_base_reaction_generation)
    graph.add_node("execute_agents", node_4_agent_execution)
    graph.add_node("push_to_database", node_5_push_to_database)
    
    # Add edges
    graph.add_edge(START, "screen_agents")
    graph.add_edge("screen_agents", "generate_events")
    graph.add_edge("generate_events", "generate_reactions")
    graph.add_edge("generate_reactions", "execute_agents")
    graph.add_edge("execute_agents", "push_to_database")
    graph.add_edge("push_to_database", END)
    
    return graph.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_master_simulator(policy_text: str) -> str:
    """
    Execute the MasterSimulatorGraph with a given policy text
    
    Args:
        policy_text: The policy text to process
        
    Returns:
        simulation_id: The ID of the completed simulation
    """
    # Generate simulation ID and timestamp
    simulation_id = f"sim_{uuid.uuid4().hex[:16]}"
    timestamp = datetime.now().isoformat()
    
    print("\n" + "=" * 80)
    print("MASTER SIMULATOR GRAPH - STARTING")
    print("=" * 80)
    print(f"Simulation ID: {simulation_id}")
    print(f"Timestamp: {timestamp}")
    print(f"Policy: {policy_text[:100]}..." if len(policy_text) > 100 else f"Policy: {policy_text}")
    
    # Build the graph
    graph = build_master_simulator_graph()
    
    # Initialize state
    initial_state: MasterSimulatorState = {
        "policy_text": policy_text,
        "screened_agent_ids": [],
        "agent_details_string": "",
        "policy_vector": {},
        "event_list_objects": [],
        "base_reactions": [],
        "execution_details": [],
        "simulation_id": simulation_id,
        "timestamp": timestamp,
        "status": "initialized"
    }
    
    # Execute the graph
    try:
        final_state = graph.invoke(initial_state)
        
        print("\n" + "=" * 80)
        print("MASTER SIMULATOR GRAPH - COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Simulation ID: {simulation_id}")
        print(f"Status: {final_state.get('status')}")
        
        return simulation_id
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("MASTER SIMULATOR GRAPH - ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


