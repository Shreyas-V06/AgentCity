# AgentCity

AgentCity is a multi-agent simulation platform that models how different personas evaluate and respond to city policy decisions using LLM-based reasoning.

Each agent represents a distinct persona and independently evaluates policies to produce decisions such as positive, negative, or neutral.

---

## Features

* Persona-based multi-agent simulation
* LLM-driven decision making
* Independent reasoning per agent
* Aggregation of results across agents
* Redis caching for faster execution

---

## Installation

git clone [https://github.com/your-username/AgentCity.git](https://github.com/your-username/AgentCity.git)
cd AgentCity
pip install -r requirements.txt

---

## Run Redis

redis-server

---

## Run Application

streamlit run poc.py

---

## Project Structure

simulator.py → Core simulation engine
evaluator.py → Evaluation logic
db.py → Data handling and caching
poc.py → Streamlit UI
prompts.py → LLM prompts
agent_profiles.json → Persona definitions
tools → Utility modules
schemas → Data models
utils → Helper functions
events → Event system

---

## Workflow

1. Load agent personas
2. Input policy scenario
3. Each agent uses LLM to decide
4. Collect all decisions
5. Aggregate final output

---

## Note

This is a prototype system for experimenting with multi-agent LLM simulations.
