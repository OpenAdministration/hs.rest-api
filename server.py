import subprocess
import yaml

with open("env.yaml", "r") as file:
    env = yaml.safe_load(file)["server"]
    port = env["port"]
    host = env["host"]
    log = env["log-level"]
    worker = env["worker"]
    if __name__ == "__main__":
        subprocess.run(["hypercorn", "main:app", "--bind", f"{host}:{port}", "--log-level", log, "--workers",str(worker)])