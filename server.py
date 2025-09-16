import uvicorn
import yaml

with open("env.yaml", "r") as file:
    env = yaml.safe_load(file)["server"]
    port = env["port"]
    host = env["host"]
    log = env["log-level"]
    worker = env["worker"]

    if __name__ == "__main__":
        uvicorn.run("main:app", host=host, port=port, log_level=log, workers=4)