"""Generated bounded agent specifications."""
from dataclasses import dataclass

@dataclass
class AgentSpec:
    name: str
    objective: str
    model_profile: str
    max_turns: int = 8

AGENTS = [
    AgentSpec(name='Extract Invoice Fields', objective='Extract Invoice Fields', model_profile='reasoning-default'),
    AgentSpec(name='Request Supplier Review', objective='Request Supplier Review', model_profile='reasoning-default'),
    AgentSpec(name='Assess Exception Reason', objective='Assess Exception Reason', model_profile='reasoning-default'),
]
