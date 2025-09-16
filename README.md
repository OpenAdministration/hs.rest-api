# hs.rest-api

Converts Hostsharing eG’s XML-RPC API into a more modern, opinionated REST API.

---

## Features

- Wraps Hostsharing eG’s XML-RPC API and exposes REST endpoints
- Opinionated: makes design decisions to simplify usage and common patterns
- Multi PAC Environment-based configuration fully supported via YAML (`env.yaml`)
- Secures each application with a seperate API key, which can have different permissions
---

## Requirements

- Python 3.10+ (or compatible version)
- Virtual environment recommended
- Hostsharing PAC Account credentials
- Setup `env.yaml` with your credentials (see below)

---

## Installation

### Step 1: Clone the Repository and Install Dependencies

```bash
git clone https://github.com/OpenAdministration/hs.rest-api.git
cd hs.rest-api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure Your Environment

Copy the `env.example.yaml` file and configure your credentials:

```bash
cp env.example.yaml env.yaml
vim env.yaml  # Add your Hostsharing credentials
```

- PAC credentials are in the format `username:password`.
- API key determines which PACs are accessible.

---

### Step 3: Running the Application

#### Production

Run the application as a systemd service for production environments:

```bash
mkdir -p ~/.config/systemd/user
cp ~/hs.rest-api/hs-rest-api.service ~/.config/systemd/user
systemctl --user daemon-reload
systemctl --user enable hs-rest-api.service
systemctl --user start hs-rest-api.service
```

You can adjust the `env.yaml` file to specify the desired host and port.

---

#### Development

Use the built-in FastAPI server for local testing:

```bash
cd ~/hs.rest-api
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If you want the server accessible externally in a test environment via `xyz00.hostsharing.net`, set the host to `0.0.0.0`. Example:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
> **Warning:** Do not use the built-in server in production!

---

## Using the API

### Authorization

To interact with the API, you must include the following HTTP headers in your requests:

- **Authorization:** API key defined in `env.yaml`.
- **PAC (optional):** Specify which PAC to use. Only required if multiple PACs are linked to the API key.

---

### Sample Requests with `curl`

**1. Retrieve All Domains**
```bash
curl -X GET "http://127.0.0.1:8000/domains" \
     -H "Authorization: superdupersecretapikeyforanoterapplicationheaderPlsChange" \
     -H "PAC: xyz00"
```

**2. Create a New Domain**
```bash
curl -X POST "http://127.0.0.1:8000/domain" \
     -H "Authorization: superdupersecretapikeyforanoterapplicationheaderPlsChange" \
     -H "PAC: xyz00" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "example.com",
           "user": "xyz00-domain_admin",
         }'
```

**3. Delete a Domain**
```bash
curl -X DELETE "http://127.0.0.1:8000/domains" \
     -H "Authorization: superdupersecretapikeyforanoterapplicationheaderPlsChange" \
     -H "PAC: xyz00" \
     -H "Content-Type: application/json" \
     -d '{"name": "example.com"}'
```

**4. Get Email Addresses**
```bash
curl -X GET "http://127.0.0.1:8000/email/hello@example.com" \
     -H "Authorization: superdupersecretapikeyforanoterapplicationheaderPlsChange" \
     -H "PAC: xyz00"
```

**5. Add a New Email**
```bash
curl -X POST "http://127.0.0.1:8000/email" \
     -H "Authorization: superdupersecretapikeyforanoterapplicationheaderPlsChange" \
     -H "PAC: xyz00" \
     -H "Content-Type: application/json" \
     -d '{
           "email": "hello@example.com",
           "targets": ["example-target"],
           "active": true
         }'
```

---

## FAQ

### How can I debug missing headers like `PAC`?
If an API key is associated with multiple PACs and no `PAC` header is provided, you’ll receive an HTTP 400 error with detailed information.

---

## License and Contributing

This project is open-source and welcomes contributions! Submit a pull request or raise an issue if you encounter problems or have feature proposals.

---