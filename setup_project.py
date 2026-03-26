import os
import argparse

DEFAULT_PROJECT_NAME = "agentic-ticketing-system"

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
"""
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
    parser = argparse.ArgumentParser(description="Create AI Ticketing Project Structure")
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Base directory where project will be created"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=DEFAULT_PROJECT_NAME,
        help="Project folder name"
    )

    args = parser.parse_args()

    base_dir = os.path.abspath(args.path)
    project_path = os.path.join(base_dir, args.name)

    if os.path.exists(project_path):
        print(f"⚠️  Directory '{project_path}' already exists. Please choose a different name or path.")
        return
    else :
        print(f"🚀 Creating project at: {project_path}\n")

        os.makedirs(project_path, exist_ok=True)
        create_structure(project_path, structure)

        print("✅ Project structure created successfully!")
        print("\nNext steps:")
        print(f"cd {project_path}")
        print("pip install -r requirements.txt")


if __name__ == "__main__":
    main()