import os

BASE_DIR = "agentic_sla_system"

folders = [
    "app/config",
    "app/monitoring",
    "app/ticketing",
    "app/orchestrator",
    "app/agents",
    "app/playbooks",
    "app/human_loop",
    "app/audit",
    "app/utils",
    "scripts",
    "tests"
]

files = {
    "app/main.py": "",
    "app/config/settings.py": "",
    "app/config/constants.py": "",
    "app/monitoring/prometheus_client.py": "",
    "app/monitoring/grafana_alerts.py": "",
    "app/monitoring/event_parser.py": "",
    "app/ticketing/odoo_client.py": "",
    "app/ticketing/ticket_schema.py": "",
    "app/orchestrator/orchestrator.py": "",
    "app/agents/analyzer_agent.py": "",
    "app/agents/decision_agent.py": "",
    "app/agents/execution_agent.py": "",
    "app/agents/verification_agent.py": "",
    "app/agents/base_agent.py": "",
    "app/playbooks/restart_service.py": "",
    "app/playbooks/scale_instance.py": "",
    "app/playbooks/clear_queue.py": "",
    "app/playbooks/db_restart.py": "",
    "app/human_loop/approval_handler.py": "",
    "app/audit/audit_logger.py": "",
    "app/audit/audit_schema.py": "",
    "app/utils/helpers.py": "",
    "app/utils/logger.py": "",
    "scripts/simulate_cpu_issue.py": "",
    "scripts/simulate_db_issue.py": "",
    "requirements.txt": ""
}

def create_structure():
    for folder in folders:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

    for file, content in files.items():
        file_path = os.path.join(BASE_DIR, file)
        with open(file_path, "w") as f:
            f.write(content)

    print("✅ Project structure created successfully!")

if __name__ == "__main__":
    create_structure()