import os
import subprocess
import tempfile
import stat
import json
import yaml

from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()

AWS_CLI = r"C:\Program Files\Amazon\AWSCLIV2\aws.exe"

# ================================================================
# LOAD CONFIG
# ================================================================
def _load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "config", "aws_config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)["infrastructure"]

CFG = _load_config()

# ================================================================
# HELPERS
# ================================================================
def _aws_env():
    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = CFG["aws"]["access_key_id"]
    env["AWS_SECRET_ACCESS_KEY"] = CFG["aws"]["secret_access_key"]
    env["AWS_DEFAULT_REGION"] = CFG["aws"]["region"]
    return env


def _run(cmd, env=None):
    logger.info(f"EXEC: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def _save(ticket_id, action, status, output, route):
    conn = get_connection()

    try:
        data = json.dumps(output, indent=2)
    except:
        data = str(output)

    conn.execute("""
        UPDATE tickets SET
            execution_action=?,
            execution_status=?,
            execution_output=?,
            execution_route=?,
            execution_time=datetime('now')
        WHERE ticket_id=?
    """, (action, status, data[:4000], route, ticket_id))

    conn.commit()


def _ssh(script):
    key = CFG["ssh"]["private_key_path"]
    user = CFG["ssh"]["ec2_user"]
    ip   = CFG["ssh"]["ec2_public_ip"]

    os.chmod(key, stat.S_IRUSR)

    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
        f.write(script)
        tmp = f.name

    cmd = [
        "ssh", "-i", key,
        "-o", "StrictHostKeyChecking=no",
        f"{user}@{ip}",
        "bash -s"
    ]

    with open(tmp) as s:
        res = subprocess.run(cmd, stdin=s, capture_output=True, text=True)

    os.unlink(tmp)
    return res.returncode == 0, res.stdout + res.stderr


# ================================================================
# EC2 SCALE
# ================================================================
def execute_ec2(ticket):
    env = _aws_env()
    steps = []

    instance = CFG["aws"]["ec2_instance_id"]
    scale_map = CFG.get("scale_up", {})

    rc, cur, err = _run([
        AWS_CLI, "ec2", "describe-instances",
        "--instance-ids", instance,
        "--query", "Reservations[0].Instances[0].InstanceType",
        "--output", "text"
    ], env)

    steps.append({"step": "describe", "rc": rc, "out": cur, "err": err})

    if rc != 0:
        return "FAILED", steps

    target = scale_map.get(cur)
    if not target:
        return "ESCALATED", steps

    rc, _, err = _run([AWS_CLI, "ec2", "stop-instances", "--instance-ids", instance], env)
    steps.append({"step": "stop", "rc": rc, "err": err})

    rc, _, err = _run([
        AWS_CLI, "ec2", "modify-instance-attribute",
        "--instance-id", instance,
        "--attribute", "instanceType",
        "--value", target
    ], env)
    steps.append({"step": "modify", "rc": rc, "err": err})

    if rc != 0:
        return "FAILED", steps

    rc, _, err = _run([AWS_CLI, "ec2", "start-instances", "--instance-ids", instance], env)
    steps.append({"step": "start", "rc": rc, "err": err})

    return "SUCCESS", steps


# ================================================================
# EBS
# ================================================================
def execute_ebs(ticket):
    env = _aws_env()
    steps = []

    cfg = CFG["ebs"]
    instance = CFG["aws"]["ec2_instance_id"]

    rc, vol, err = _run([
        AWS_CLI, "ec2", "create-volume",
        "--availability-zone", CFG["aws"]["availability_zone"],
        "--size", str(cfg["volume_size_gb"]),
        "--volume-type", "gp3",
        "--query", "VolumeId",
        "--output", "text"
    ], env)

    steps.append({"step": "create", "rc": rc, "vol": vol, "err": err})

    if rc != 0:
        return "FAILED", steps

    for device in cfg["device_names"]:
        rc, _, err = _run([
            AWS_CLI, "ec2", "attach-volume",
            "--volume-id", vol,
            "--instance-id", instance,
            "--device", device
        ], env)

        steps.append({"step": "attach", "device": device, "rc": rc})

        if rc == 0:
            ok, out = _ssh(f"""
            sudo mkfs -t ext4 {device}
            sudo mkdir -p {cfg['mount_point']}
            sudo mount {device} {cfg['mount_point']}
            """)
            steps.append({"step": "mount", "ok": ok})

            return ("SUCCESS" if ok else "PARTIAL_SUCCESS"), steps

    return "PARTIAL_SUCCESS", steps


# ================================================================
# POD
# ================================================================
def execute_pod(ticket):
    steps = []

    k = CFG["kubernetes"]

    script = f"""
    kubectl patch deployment {k['deployment_name']} -n {k['namespace']} \
    --type=json -p='[{{"op":"replace","path":"/spec/template/spec/containers/0/resources",
    "value":{{"requests":{{"cpu":"{k['cpu_request']}","memory":"{k['memory_request']}"}},
    "limits":{{"cpu":"{k['cpu_limit']}","memory":"{k['memory_limit']}"}}}}}}]'
    """

    ok, out = _ssh(script)
    steps.append({"step": "patch", "ok": ok})

    return ("SUCCESS" if ok else "FAILED"), steps


# ================================================================
# MAIN
# ================================================================
def run_execution_agent(ticket):
    issue = (ticket.get("ai_issue") or "").lower()
    tid = ticket["ticket_id"]

    if "ram" in issue:
        status, steps = execute_ec2(ticket)
        action = "EC2_SCALE"
        route = "EC2"

    elif "storage" in issue or "disk" in issue:
        status, steps = execute_ebs(ticket)
        action = "EBS_ATTACH"
        route = "EBS"

    elif "pod" in issue:
        status, steps = execute_pod(ticket)
        action = "K8S_PATCH"
        route = "K8S"

    else:
        status = "ESCALATED"
        steps = [{"reason": "no handler"}]
        action = "UNKNOWN"
        route = "UNKNOWN"

    _save(tid, action, status, {"steps": steps}, route)

    return {"status": status}