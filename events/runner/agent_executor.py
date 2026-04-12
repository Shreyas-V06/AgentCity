import json
from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, ToolMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
from db import initialize_redis
from llm.factory import LLMConfig, LLMFactory, LLMProvider
from tools.definition import make_decision, post_social_media, chat_with_agent
from prompts import AGENT_EXECUTION_PROMPT


class AgentExecutionState(TypedDict):
    """State for individual agent execution during event simulation."""
    messages: Annotated[list[BaseMessage], add_messages]
    agent_id: str
    event_id: str
    event_description: str
    agent_data: Dict[str, Any]
    termination_reason: str  


def _build_agent_executor_graph(llm, agent_id: str, event_id: str, event_description: str, agent_data: Dict[str, Any]):
    """
    Build a LangGraph subgraph for a single agent's tool-calling execution phase.
    
    The agent can call three tools:
    - make_decision: Terminating tool
    - post_social_media: Terminating tool
    - chat_with_agent: Continuing tool (can loop if end_conversation=False)
    """
    
    # Bind the three tools to the LLM
    tools = [make_decision, post_social_media, chat_with_agent]
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentExecutionState) -> AgentExecutionState:
        """
        The main agent node: invoke the LLM with tools and current message history.
        """
        agent_name = agent_data.get("name", agent_id)
        
        # Format relations for the prompt
        relations = agent_data.get("relations", {})
        relations_str = ""
        if relations:
            relations_str = "\n".join([f"- {rel_name} ({rel_id}): {relation_type}" 
                                       for rel_id, relation_type in relations.items()
                                       for rel_name in [agent_data.get("name", rel_id)]])  # Use relation name if available
        else:
            relations_str = "No known contacts"
        
        # Build the system prompt
        system_prompt = AGENT_EXECUTION_PROMPT.format(
            agent_name=agent_name,
            agent_persona=agent_data.get("persona", "Average citizen"),
            agent_occupation=agent_data.get("occupation", "Unknown"),
            agent_age=agent_data.get("age", "Unknown"),
            agent_gender=agent_data.get("gender", "Unknown"),
            agent_language=agent_data.get("language", "English"),
            agent_tone=agent_data.get("tone", "Neutral"),
            agent_political_leaning=agent_data.get("political_leaning", 0.5),
            agent_morality=agent_data.get("morality", 0.5),
            agent_selfishness=agent_data.get("selfishness", 0.5),
            event_description=event_description,
            available_contacts=relations_str,
        )
        

        if not state["messages"]:
            messages = [HumanMessage(content=system_prompt)]
        else:
            messages = state["messages"]

        response = llm_with_tools.invoke(messages)
        state["messages"].append(response)
        
        return state
    
    def tools_node(state: AgentExecutionState) -> Dict[str, Any]:
        """
        Execute tool calls and append results back to the message history.
        Uses LangGraph's ToolNode to handle the execution automatically.
        """
        tool_node_executor = ToolNode(tools)
        return tool_node_executor.invoke(state)
    
    def should_continue(state: AgentExecutionState) -> Literal["tools", "end"]:
        """
        Conditional edge: determine if we should call tools or end the execution.
        """
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return "end"
    
    
    # Build the state graph
    graph = StateGraph(AgentExecutionState)
    
    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    
    # Add edges
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", END)
    
    return graph.compile()


def build_agent_executor_graph(agent_id: str, event_id: str, event_description: str, agent_data: Dict[str, Any]):
    """
    Factory function to build an agent executor graph with proper LLM initialization.
    
    Args:
        agent_id: The ID of the agent executing
        event_id: The ID of the event being simulated
        event_description: Description of the event
        agent_data: Full profile data of the agent
    
    Returns:
        Compiled LangGraph runnable
    """
    try:
        llm_config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile", temperature=0.7)
        llm = LLMFactory.build(llm_config)
    except BaseException:
        llm_config = LLMConfig(provider=LLMProvider.OPENAI, model_name="gpt-4o-mini", temperature=0.7)
        llm = LLMFactory.build(llm_config)
    
    return _build_agent_executor_graph(llm, agent_id, event_id, event_description, agent_data)
