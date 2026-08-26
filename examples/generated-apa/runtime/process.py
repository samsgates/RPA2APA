"""RPA2APA generated reference runtime.

This file is intentionally framework-light. Replace the execution seam with a LangGraph/OpenAI Agents adapter when desired.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class RunState:
    data: dict[str, Any] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)

class ApprovalRequired(RuntimeError):
    pass

PROCESS = [
  {
    "id": "node:Main:1:Sequence",
    "name": "Process Supplier Invoice",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:2:GetIMAPMailMessages",
    "name": "Read Invoice Email",
    "type": "tool",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:3:DocumentUnderstanding",
    "name": "Extract Invoice Fields",
    "type": "agent",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:4:ReadRange",
    "name": "Read Approved Supplier List",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "HIGH"
  },
  {
    "id": "node:Main:5:If",
    "name": "Validate Supplier",
    "type": "decision",
    "requires_approval": false,
    "risk": "LOW"
  },
  {
    "id": "node:Main:6:If.Then",
    "name": "If.Then",
    "type": "decision",
    "requires_approval": false,
    "risk": "LOW"
  },
  {
    "id": "node:Main:7:Sequence",
    "name": "Valid Supplier",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:8:Assign",
    "name": "Mark Supplier Valid",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "LOW"
  },
  {
    "id": "node:Main:9:If.Else",
    "name": "If.Else",
    "type": "decision",
    "requires_approval": false,
    "risk": "LOW"
  },
  {
    "id": "node:Main:10:Sequence",
    "name": "Invalid Supplier",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:11:ActionCenter",
    "name": "Request Supplier Review",
    "type": "agent",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:12:Click",
    "name": "Open SAP Invoice Entry",
    "type": "browser",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:13:TypeInto",
    "name": "Enter Invoice Data",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "MEDIUM"
  },
  {
    "id": "node:Main:14:If",
    "name": "Assess Exception Reason",
    "type": "agent",
    "requires_approval": false,
    "risk": "LOW"
  },
  {
    "id": "node:Main:15:If.Then",
    "name": "If.Then",
    "type": "decision",
    "requires_approval": false,
    "risk": "LOW"
  },
  {
    "id": "node:Main:16:ActionCenter",
    "name": "Approve High Value Payment",
    "type": "deterministic",
    "requires_approval": false,
    "risk": "HIGH"
  },
  {
    "id": "node:Main:17:HttpRequest",
    "name": "Create Payment API",
    "type": "api",
    "requires_approval": true,
    "risk": "HIGH"
  },
  {
    "id": "node:Main:18:SendSMTPMailMessage",
    "name": "Send Supplier Confirmation",
    "type": "tool",
    "requires_approval": false,
    "risk": "MEDIUM"
  }
]

def run(initial: dict[str, Any] | None = None, approvals: set[str] | None = None) -> RunState:
    state = RunState(data=initial or {})
    approvals = approvals or set()
    for step in PROCESS:
        state.audit.append({'event': 'step.enter', 'step': step['id']})
        if step['requires_approval'] and step['id'] not in approvals:
            raise ApprovalRequired(f"Approval required before {step['name']}")
        # Generated skeleton. Wire explicit deterministic tools or bounded agents here.
        state.audit.append({'event': 'step.complete', 'step': step['id']})
    return state

if __name__ == '__main__':
    print(run().audit)
