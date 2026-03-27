# Agentic SLA System

## Overview

This project implements an agentic, multi-step incident management system designed to detect system failures, predict SLA risks, and autonomously execute remediation workflows with minimal human intervention.

The system integrates monitoring, ticketing, and multi-agent orchestration to create a closed-loop workflow that ensures faster resolution and SLA compliance while maintaining a complete audit trail.

---

## Key Capabilities

* Automated incident detection from monitoring systems
* Automatic ticket creation without manual input
* Multi-agent orchestration for analysis, decision-making, execution, and verification
* SLA risk prediction and prioritization
* Autonomous remediation using predefined playbooks
* Human-in-the-loop fallback for low-confidence scenarios
* End-to-end audit logging for traceability and compliance

---

## System Architecture

The system follows a structured workflow:

Monitoring → Alert Handling → Ticket Creation → Agent Orchestration → Analysis → Decision → Execution → Verification → Ticket Update → Audit Logging

Refer to the architecture diagram included in this repository for detailed flow.

---

## Project Structure

```
agentic_sla_system/
│
├── app/
│   ├── main.py
│   ├── config/
│   ├── monitoring/
│   ├── ticketing/
│   ├── orchestrator/
│   ├── agents/
│   ├── playbooks/
│   ├── human_loop/
│   ├── audit/
│   └── utils/
│
├── scripts/
├── tests/
├── requirements.txt
```

---

## Components

### Monitoring Layer

* Collects system metrics and logs
* Triggers alerts based on predefined thresholds

### Alert Handler

* Processes alerts and formats them into structured events

### Ticketing (Odoo Integration)

* Automatically creates and updates incident tickets
* Acts as the system of record for incident lifecycle

### Agent Orchestrator

* Coordinates the execution of agents
* Routes tasks between agents based on workflow state

### Analyzer Agent

* Classifies incident type
* Estimates impact
* Predicts SLA breach risk

### Decision Agent

* Determines whether to auto-remediate or escalate
* Uses confidence score and SLA urgency

### Execution Agent

* Executes remediation playbooks
* Interacts with infrastructure (e.g., AWS via boto3)

### Verification Agent

* Validates system recovery
* Confirms SLA compliance

### Human Loop (Fallback)

* Handles low-confidence scenarios requiring manual approval

### Audit Module

* Logs all actions, decisions, and outcomes
* Enables traceability and compliance

---

## Workflow

1. Monitoring system detects anomaly
2. Alert is triggered and processed
3. Ticket is automatically created in Odoo
4. Orchestrator initiates agent workflow
5. Analyzer evaluates issue and SLA risk
6. Decision agent determines action:

   * Autonomous remediation
   * Human-assisted escalation
7. Execution agent performs action
8. Verification agent confirms recovery
9. Ticket is updated or closed in Odoo
10. All steps are logged in audit trail

---

## AWS Integration

The system integrates with AWS for both event ingestion and execution:

### Inbound

* Alerts are forwarded via AWS Lambda
* Lambda sends structured events to the application via HTTP endpoint

### Outbound

* Execution agent uses boto3 to perform actions such as:

  * Restarting instances
  * Scaling resources
  * Managing services

### Configuration

* AWS credentials are managed using IAM roles or access keys
* Local setup uses `aws configure`

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Running the System

```bash
python app/main.py
```

---

## Simulation

Use scripts to simulate incidents:

```bash
python scripts/simulate_cpu_issue.py
python scripts/simulate_db_issue.py
```

---

## Design Principles

* Modular agent-based architecture
* Clear separation of concerns
* Deterministic workflow with controlled branching
* Minimal external dependencies
* Extensible for additional agents and workflows

---

## Future Enhancements

* Real-time streaming integration (Kafka or Kinesis)
* Advanced anomaly detection models
* Dynamic playbook generation
* Multi-tenant support
* Dashboard for live agent monitoring
