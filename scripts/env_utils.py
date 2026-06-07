import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path=ROOT / ".env"):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def gonka_rpc_url(default="http://node1.gonka.ai:8000"):
    load_dotenv()
    value = os.environ.get("GONKA_RPC_URL", default).strip()
    if value and "://" not in value:
        value = f"http://{value}"
    return value.rstrip("/")


def gonka_rpc_source_label(default_label="http://node1.gonka.ai:8000"):
    load_dotenv()
    return "GONKA_RPC_URL" if os.environ.get("GONKA_RPC_URL") else default_label
