import yaml

def load_config():
    config_path = "app/config/config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:  # ← add encoding="utf-8"
        config = yaml.safe_load(f)
    return config