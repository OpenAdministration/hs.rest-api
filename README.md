# hs.rest-api

Converts Hostsharing eG’s XML-RPC API into a more modern, opinionated REST API.

---

## Features

- Wraps Hostsharing eG’s XML-RPC API and exposes REST endpoints
- Opinionated: makes design decisions to simplify usage and common patterns
- Supports multiple database backends (MySQL, PostgreSQL) via internal model modules

---

## Requirements

- Python 3.10+ (or compatible version)
- Virtual environment recommended
- Hostsharing PAC Account credentials

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/OpenAdministration/hs.rest-api.git
cd hs.rest-api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then copy the `env.example.yaml` file to your custom `env.yaml` and put in your credentials to start.

## Running the Application

### Production

```bash
mkdir -p ~/.config/systemd/user
cp ~/hs.rest-api/hs-rest-api.service  ~/.config/systemd/user
systemctl --user daemon-reload
systemctl --user enable hs-rest-api.service
systemctl --user start hs-rest-api.service
```
Adapt the port in the service file as needed
### Development Mode

You can run the REST API with hot reload for development using `uvicorn`:

```bash
cd ~/hs.rest-api
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If you want it publicly available for tests you can use `0.0.0.0` as Host and find it under `xyz00.hostsharing.net:8000`
Exchange the port if needed. You should NOT use that in production!





