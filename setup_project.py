import os

BASE_DIR = "ET"

structure = {
    "app": {
        "main.py": "",
        "orchestrator": {
            "orchestrator.py": "",
            "state.py": "",
            "router.py": "",
        },
        "agents": {
            "base_agent.py": "",
            "classifier": {
                "agent.py": "",
                "prompt.txt": "",
            },
            "sla": {
                "agent.py": "",
            },
            "workload": {
                "agent.py": "",
            },
            "execution": {
                "agent.py": "",
                "rag.py": "",
                "kb_loader.py": "",
            },
            "prediction": {
                "agent.py": "",
            },
            "escalation": {
                "agent.py": "",
            },
        },
        "integrations": {
            "odoo": {
                "client.py": "",
                "mapper.py": "",
            },
            "bedrock": {
                "client.py": "",
                "embeddings.py": "",
            },
        },
        "services": {
            "ticket_service.py": "",
            "sla_service.py": "",
            "assignment_service.py": "",
        },
        "memory": {
            "session_store.py": "",
            "history.py": "",
        },
        "db": {
            "models.py": "",
            "repository.py": "",
            "connection.py": "",
        },
        "utils": {
            "logger.py": "",
            "config.py": "",
            "helpers.py": "",
        },
        "api": {
            "routes.py": "",
            "controllers.py": "",
        },
    },
    "data": {
        "tickets.json": "[]",
        "knowledge_base": {},
    },
    "scripts": {
        "run_worker.py": "",
        "seed_data.py": "",
    },
    "tests": {},
    ".env": "",
    "requirements.txt": """fastapi
uvicorn
boto3
langchain
langgraph
faiss-cpu
pydantic
sqlalchemy
psycopg2-binary
python-dotenv
requests
numpy
scikit-learn
""",
    "README.md": "# AI Ticketing System\n\nPOC for multi-agent SLA automation.\n",
    "docker-compose.yml": "",
}


def create_structure(base_path, structure_dict):
    for name, content in structure_dict.items():
        path = os.path.join(base_path, name)

        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


def main():
    print("🚀 Creating project structure...\n")

    os.makedirs(BASE_DIR, exist_ok=True)
    create_structure(BASE_DIR, structure)

    print(f"✅ Project created at: {BASE_DIR}")
    print("\nNext steps:")
    print("cd ai-ticketing-system")
    print("pip install -r requirements.txt")


if __name__ == "__main__":
    main()