# OFW Server - Quick Start Guide

## What is ofw-server?

A mock API server that mimics Our Family Wizard's endpoints using data exported from the real OFW site. Perfect for:
- 🧪 Testing without hitting the real API
- 💻 Offline development
- 🐛 Debugging API interactions
- 🚀 Integration testing

## 5-Minute Setup

### Step 1: Export Data from Real OFW

```bash
# In the ofw-client directory
cd ../ofw-client
python example_complete_workflow.py

# Login and browse some messages
# This creates debug/*.json files
```

### Step 2: Install OFW Server

```bash
cd ofw-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run the Server

```bash
python app.py
```

Output:
```
======================================================================
OFW MOCK SERVER
======================================================================

Data directory: /path/to/ofw-client/debug
Auth token: mock_auth_token_12345

✓ Loaded folders from /path/to/ofw-client/folders.json
✓ Loaded messages from /path/to/ofw-client/messages.json
✓ Data loaded from /path/to/ofw-client

 * Running on http://0.0.0.0:5000
```

### Step 4: Test It

```bash
# In another terminal
python test_server.py
```

Expected output:
```
======================================================================
OFW MOCK SERVER TEST SUITE
======================================================================

TEST: Health Check
✓ PASSED

TEST: LocalStorage
✓ PASSED

TEST: Folders
✓ PASSED

ALL TESTS PASSED ✓
```

## Using with OFW Client

### Option 1: Environment Variable

```bash
export OFW_BASE_URL=http://localhost:5000
python your_script.py
```

### Option 2: Modify Client Code

```python
from ofw_messages_client import OFWMessagesClient

# Override BASE_URL
class MockOFWClient(OFWMessagesClient):
    BASE_URL = "http://localhost:5000"
    API_BASE = f"{BASE_URL}/pub"

# Use it
client = MockOFWClient()
client.authenticate_with_token("mock_auth_token_12345")
folders = client.get_folders()
```

### Option 3: Configuration File

Create `config.py`:
```python
import os

if os.environ.get('OFW_MOCK') == 'true':
    BASE_URL = "http://localhost:5000"
else:
    BASE_URL = "https://ofw.ourfamilywizard.com"
```

Then in your code:
```python
from config import BASE_URL

class OFWMessagesClient:
    BASE_URL = BASE_URL
    # ...
```

## Common Commands

```bash
# Start server
python app.py

# Start with custom data directory
export OFW_DATA_DIR=//path/to/ofw-client/debug
python app.py

# Start on different port
export PORT=8080
python app.py

# Reload data without restarting
curl -X POST http://localhost:5000/reload

# Check health
curl http://localhost:5000/health
```

## Docker

### Build and Run

```bash
# Build
docker build -t ofw-server .

# Run
docker run -p 5000:5000 \
  -v /path/to/ofw-client/debug:/data:ro \
  ofw-server
```

### Docker Compose

```bash
docker-compose up
```

## Project Structure

```
ofw-server/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
├── README.md             # Full documentation
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker Compose config
├── test_server.py        # Test suite
└── .gitignore           # Git ignore rules
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/ofw/appv2/localstorage.json` | GET | No | Get auth token |
| `/pub/v1/messageFolders` | GET | Yes | Get folders |
| `/pub/v3/messages` | GET | Yes | Get messages |
| `/pub/v3/messages/<id>` | GET | Yes | Get single message |
| `/reload` | POST | No | Reload data from files |

## Configuration

### Environment Variables

```bash
# Data directory 
export OFW_DATA_DIR=/path/to/ofw-client/debug

# Auth token (default: mock_auth_token_12345)
export OFW_AUTH_TOKEN=your_token

# Port (default: 5000)
export PORT=8080

# Debug mode (default: true)
export FLASK_DEBUG=false
```

## Data Files

The server reads these files from the data directory:

| File | Required | Purpose |
|------|----------|---------|
| `folders.json` | No | Message folders |
| `messages.json` | No | Messages (one folder) |
| `all_messages.json` | No | All messages |
| `full_message.json` | No | Message with body |
| `localstorage_data.json` | No | Auth token & user data |

If files are missing, the server uses default/empty data.

## Example: End-to-End Workflow

### 1. Export Real Data

```bash
cd ofw-client
python example_complete_workflow.py
# Login, browse folders and messages
```

Files created:
```
debug/
├── folders.json
├── messages.json
├── full_message.json
└── localstorage_data.json
```

### 2. Start Mock Server

```bash
cd ofw-server
python app.py
```

### 3. Test with Client

```python
# test_with_mock.py
from ofw_messages_client import OFWMessagesClient

# Point to mock server
client = OFWMessagesClient()
client.BASE_URL = "http://localhost:5000"
client.API_BASE = f"{client.BASE_URL}/pub"

# Authenticate with mock token
client.authenticate_with_token("mock_auth_token_12345")

# Use API normally
folders = client.get_folders()
print(f"Folders: {len(folders['systemFolders'])}")

messages = client.get_messages()
print(f"Messages: {len(messages['data'])}")
```

Run it:
```bash
python test_with_mock.py
```

Output:
```
Folders: 3
Messages: 10
```

## Troubleshooting

### Server won't start

```bash
# Check if port is in use
lsof -i :5000

# Use different port
export PORT=8080
python app.py
```

### No data loaded

```bash
# Check data directory
ls -lh /path/to/ofw-client/debug/*.json

# Or specify directory
export OFW_DATA_DIR=/path/to/ofw-client/debug
python app.py
```

### 401 Unauthorized

```bash
# Use correct token
curl -H "Authorization: Bearer mock_auth_token_12345" \
  http://localhost:5000/pub/v1/messageFolders
```

## Next Steps

- ✅ Start the server
- ✅ Run tests
- ✅ Point your client to `http://localhost:5000`
- ✅ Develop and test offline!

For full documentation, see [README.md](README.md)
