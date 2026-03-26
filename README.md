# SLA Agentic AI for Ticketing (L1 Resolution) – POC


## Overview

This project is a multi-agent AI system designed to automate Level 1 (L1) ticket resolution while managing SLA commitments.

Instead of a single AI model, the system uses multiple specialized agents coordinated by an orchestrator to simulate a real support team.

It integrates with **Odoo (Helpdesk)** as the ticketing UI and uses **AWS Bedrock** for AI capabilities.

---

## What This System Does

- Automatically classifies tickets
- Assigns SLA deadlines
- Allocates tickets to the best-fit agent
- Resolves simple issues automatically (L1)
- Predicts SLA risks
- Escalates complex cases

End-to-end automation of the support lifecycle.

---

## System Architecture
```
Odoo (UI)
   |
Backend (FastAPI / Python)
   |
Orchestrator (Brain)
   |
Multi-Agent System
   |
Response back to Odoo
```

---

## Core Components

### Orchestrator
- Central controller of the system
- Decides which agent runs next
- Maintains shared state

### Agents

Each agent has a single responsibility:

| Agent | Responsibility |
|---|---|
| Classifier Agent | Understands and categorizes the ticket |
| SLA Agent | Assigns deadlines based on priority |
| Workload Agent | Assigns ticket to the best available owner |
| Execution Agent | Resolves ticket using RAG + LLM |
| Prediction Agent | Detects SLA breach risk |
| Escalation Agent | Escalates if resolution is not possible |

---

## Folder Structure

### `app/` – Core Application

#### `app/orchestrator/`
Controls the entire workflow.

- `orchestrator.py` – Main execution flow (calls agents)
- `state.py` – Shared data between agents
- `router.py` – Decision logic (what happens next)

#### `app/agents/`
All AI agents are defined here.

- `base_agent.py` – Common structure for all agents

Each subfolder represents one agent:

- `classifier/` – Ticket understanding
- `sla/` – SLA logic
- `workload/` – Assignment logic
- `execution/` – Resolution (primary agent)
- `prediction/` – Risk detection
- `escalation/` – Escalation handling

Each agent reads and updates shared state.

#### `app/integrations/`
External system connectors.

- `odoo/client.py` – Connect to Odoo API
- `odoo/mapper.py` – Convert Odoo data to/from internal format
- `bedrock/client.py` – Call AWS Bedrock models
- `bedrock/embeddings.py` – Embeddings for RAG (vector search)

#### `app/services/`
Business logic layer.

- `ticket_service.py` – Ticket handling
- `sla_service.py` – SLA rules
- `assignment_service.py` – Assignment logic

#### `app/memory/`
Stores agent interactions.

- `session_store.py` – Current session state
- `history.py` – Logs of decisions

#### `app/db/`
Database layer.

- `models.py` – Data models
- `repository.py` – DB operations
- `connection.py` – DB connection

#### `app/utils/`
Common utilities.

- `logger.py` – Logging
- `config.py` – Environment configs
- `helpers.py` – Helper functions

#### `app/api/` (Optional)
Expose backend as a service.

- `routes.py` – API endpoints
- `controllers.py` – Request handling

### `data/`
- `tickets.json` – Sample tickets
- `knowledge_base/` – Used for RAG

### `scripts/`
- `run_worker.py` – Background worker
- `seed_data.py` – Test data generation

### `tests/`
Basic test coverage.

### Root Files
- `.env` – Environment variables
- `requirements.txt` – Dependencies
- `README.md` – Documentation
- `docker-compose.yml` – Optional container setup

---

## How the System Works

1. Ticket is created in Odoo
2. Backend fetches the ticket
3. Orchestrator starts
4. Agents run in sequence: Classifier → SLA → Workload → Execution → Prediction → Escalation (if needed)
5. Result is sent back to Odoo
6. Ticket is updated

---

## Shared State

Every agent reads from and writes to a shared state object. Example:
```json
{
  "ticket": "VPN not working",
  "priority": 2,
  "assigned_to": "Alice",
  "resolution": "Restart VPN",
  "risk_score": 0.3
}
```

---

## Setup
```bash
pip install -r requirements.txt
```

Configure the following credentials:
- AWS Bedrock
- Odoo API

---

## Notes

- This is a proof of concept (POC) and is not production-hardened
- Focus is on architecture and flow
- Accuracy improves with better training data

---

## Why This Project Stands Out

- True multi-agent system, not a simple chatbot
- Real-world integration with Odoo
- End-to-end automation from intake to resolution
- Built-in decision-making and escalation logic

## Authors

<div align="center">

**Built with ❤️ by PhoenixCyberSec**

⭐ **Star this repo if it helped you!** ⭐
</div>