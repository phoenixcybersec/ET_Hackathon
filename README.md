# SLA Agentic AI for Ticketing (L1 Resolution) – POC

## Overview

This project is a proof-of-concept (POC) for an agentic AI system that automates Level 1 (L1) ticket resolution while managing SLA commitments.

The system uses multiple AI agents to classify tickets, assign priorities, track SLAs, suggest solutions, and escalate when needed.

---

## Goal

* Reduce manual effort in L1 support
* Improve SLA adherence
* Enable smart ticket routing and resolution

---

## Core Agents

### 1. Classifier Agent

* Reads incoming ticket text
* Predicts:

  * Priority (1–5)
  * Category (IT / HR / Finance)
  * Complexity (Low / Medium / High)

### 2. SLA Agent

* Assigns SLA deadlines based on priority
* Tracks time
* Flags SLA breaches

### 3. Prediction Agent

* Predicts risk of SLA failure
* Uses historical patterns and workload signals

### 4. Workload Agent

* Assigns tickets to the best available employee
* Considers workload and past performance

### 5. Execution Agent (L1 Automation)

* Suggests solutions using knowledge base (RAG)
* Auto-resolves simple issues

### 6. Escalation Agent

* Escalates complex or risky tickets
* Notifies managers or reassigns tasks

---

## Flow

1. Ticket created in Odoo
2. Classifier Agent processes ticket
3. SLA Agent assigns deadline
4. Workload Agent assigns owner
5. Execution Agent attempts resolution
6. Prediction Agent evaluates risk
7. Escalation Agent triggers if needed

---

## Tech Stack (POC)

* **LLM:** AWS Bedrock
* **Ticket System:** Odoo
* **Backend:** Python (FastAPI)
* **Agent Framework:** LangChain / LangGraph (optional)
* **Database:** Any (SQLite / PostgreSQL for POC)
* **Vector Store:** FAISS / simple embedding store

---

## Project Structure

```
project/
│
├── agents/
│   ├── classifier.py
│   ├── sla_agent.py
│   ├── prediction.py
│   ├── workload.py
│   ├── execution.py
│   └── escalation.py
│
├── services/
│   ├── odoo_client.py
│   ├── bedrock_client.py
│
├── db/
│   ├── models.py
│   └── storage.py
│
├── main.py
└── requirements.txt
```

---

## Setup (POC)

1. Clone repo
2. Install dependencies:

```
pip install -r requirements.txt
```

3. Configure AWS credentials for Bedrock
4. Connect Odoo API (URL + API key)
5. Run service:

```
python main.py
```

---

## Notes

* This is a POC, not production-ready
* Accuracy depends on data quality
* RAG performance depends on knowledge base

---

## Future Improvements

* Fine-tuned models for classification
* Better SLA prediction models
* UI dashboard for monitoring
* Feedback loop for continuous learning

---

## Authors

<div align="center">

**Built with ❤️ by PhoenixCyberSec**

⭐ **Star this repo if it helped you!** ⭐
</div>
