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


def _normalized_url(value, default_scheme="http"):
    value = (value or "").strip()
    if value and "://" not in value:
        value = f"{default_scheme}://{value}"
    return value.rstrip("/")


def _with_default_port(url, port):
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.hostname and parsed.port is None:
        return f"{parsed.scheme}://{parsed.hostname}:{port}{parsed.path if parsed.path != '/' else ''}".rstrip("/")
    return url


def gonka_rpc_url(default="http://node1.gonka.ai:26657"):
    load_dotenv()
    value = _normalized_url(os.environ.get("GONKA_RPC_URL", default))
    if os.environ.get("GONKA_RPC_URL"):
        value = _with_default_port(value, 26657)
    return value


def gonka_api_url(default="http://node1.gonka.ai:8000"):
    load_dotenv()
    return _normalized_url(os.environ.get("GONKA_API_URL", default))


def gonka_rpc_source_label(default_label="http://node1.gonka.ai:26657"):
    load_dotenv()
    return "GONKA_RPC_URL" if os.environ.get("GONKA_RPC_URL") else default_label


def gonka_api_source_label(default_label="http://node1.gonka.ai:8000"):
    load_dotenv()
    return "GONKA_API_URL" if os.environ.get("GONKA_API_URL") else default_label
