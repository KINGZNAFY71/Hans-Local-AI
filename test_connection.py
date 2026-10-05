"""
test_connection.py - Diagnostic utility to test Ollama connectivity,
inspect local network IPv4 addresses, and check model availability.
"""

import os
import socket
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Load .env manually or via python-dotenv if available
env_file = Path(__file__).parent / ".env"
config = {
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODEL": "qwen2.5:latest",
}

if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()


def get_local_ip_addresses():
    """Retrieve all local IPv4 network addresses of this machine."""
    ips = []
    hostname = socket.gethostname()
    try:
        addr_infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
        for info in addr_infos:
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    # Alternative socket probe if getaddrinfo only returned loopback
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and ip not in ips:
                ips.append(ip)
        except Exception:
            pass

    return ips


def check_endpoint(url: str, timeout: float = 3.0):
    """Check if an HTTP URL responds with status 200."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Ollama-Diagnostic/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                return True, body
            return False, f"HTTP {response.status}"
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 65)
    print("      OLLAMA & LOCAL NETWORK DIAGNOSTIC UTILITY")
    print("=" * 65)

    base_url = config.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    target_model = config.get("OLLAMA_MODEL", "qwen2.5:latest")
    port = "11434"
    if ":" in base_url.split("//")[-1]:
        port = base_url.split("//")[-1].split(":")[-1]

    # 1. Local Network IPs
    print("\n[1] Detecting Laptop Local Network (IPv4) Addresses:")
    local_ips = get_local_ip_addresses()
    if local_ips:
        for ip in local_ips:
            print(f"    - Wi-Fi / LAN IP: http://{ip}:{port}")
        primary_ip = local_ips[0]
        print(f"\n    Use this address on your iPhone: http://{primary_ip}:{port}")
    else:
        print("    [!] Could not automatically detect a Wi-Fi IP.")
        print("        Run 'ipconfig' in PowerShell to find your IPv4 Address.")
        primary_ip = None

    # 2. Localhost Test
    print(f"\n[2] Testing Localhost Connection ({base_url})...")
    ok, result = check_endpoint(f"{base_url}/api/tags")
    models = []
    if ok:
        print("    [OK] Ollama server is responding locally!")
        try:
            data = json.loads(result)
            models = [m.get("name") for m in data.get("models", [])]
            print(f"    Available Local Models ({len(models)} found):")
            for m in models:
                indicator = " [TARGET MATCH]" if m == target_model or m.startswith(target_model.split(":")[0]) else ""
                print(f"      * {m}{indicator}")
        except Exception:
            print("      (Could not parse model list JSON)")

        if target_model not in models and not any(m.startswith(target_model.split(":")[0]) for m in models):
            print(f"\n    [WARNING] Configured model '{target_model}' is not installed yet.")
            print(f"    Run: ollama pull {target_model}")
    else:
        print(f"    [FAIL] Could not connect to {base_url}")
        print(f"    Reason: {result}")
        print("    -> Make sure Ollama is running. Start it with:")
        print("       .\\start_ollama.ps1  OR  ollama serve")

    # 3. LAN Binding Test
    if primary_ip:
        lan_url = f"http://{primary_ip}:{port}"
        print(f"\n[3] Testing External LAN Exposure ({lan_url})...")
        lan_ok, lan_result = check_endpoint(f"{lan_url}/api/tags")
        if lan_ok:
            print("    [SUCCESS] Ollama is accepting connections over the local network!")
            print("    Your iPhone client should be able to connect.")
        else:
            print(f"    [NOTICE] Could not connect via LAN IP: {lan_result}")
            print("    This usually means:")
            print("    a) OLLAMA_HOST is not bound to 0.0.0.0 (run .\\start_ollama.ps1)")
            print("    b) Windows Firewall is blocking inbound port 11434.")
            print("       Run in Admin PowerShell:")
            print("       New-NetFirewallRule -DisplayName 'Ollama Inbound' -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
