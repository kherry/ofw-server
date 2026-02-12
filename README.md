# OFW Mock Server

A Python Flask-based mock server that mimics Our Family Wizard's API endpoints. See [`ofw-server-java`](https://github.com/kherry/ofw-server-java) for a scalable Java solution.

## Purpose

This server allows you to:
- ✅ Test the OFW client without hitting the real API
- ✅ Develop offline
- ✅ Control test data
- ✅ Debug API interactions
- ✅ Run integration tests

## How It Works

The server reads JSON files exported by the OFW client (from the `debug/` folder) and serves them through the same API endpoints that OFW uses.

```
┌─────────────────┐
│   OFW Client    │
│  (Real site)    │
└────────┬────────┘
         │ Export data
         ↓
    debug/*.json
         ↓
┌─────────────────┐
│   OFW Server    │
│   (Mock API)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   OFW Client    │
│ (Testing mode)  │
└─────────────────┘
```

## Installation

```bash
cd ofw-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Export Data from Real OFW

First, use the OFW client to export data:

```bash
cd ..  # Go to ofw-client directory
python example_complete_workflow.py
# Login and browse messages - data saved to debug/
```

### 2. Run the Mock Server

```bash
cd ofw-server
python app.py
```

The server will:
- Load data from `/path/to/ofw-client/debug` 
- Start on `http://localhost:5000`
- Serve the data through OFW API endpoints

**Output:**
```
======================================================================
OFW MOCK SERVER
======================================================================

Data directory: /path/to/ofw-client/debug
Auth token: mock_auth_token_12345

✓ Loaded folders from /path/to/ofw-client/debug/folders.json
✓ Loaded messages from /path/to/ofw-client/debug/messages.json
✓ Loaded full message from /path/to/ofw-client/debug/full_message.json
✓ Loaded localstorage from /path/to/ofw-client/debug/localstorage_data.json

✓ Data loaded from ../debug
  Folders: Yes
  Message folders: 1
  Full messages: 1
  LocalStorage: Yes

======================================================================
Starting server...
======================================================================

Available endpoints:
  GET  /health
  GET  /ofw/appv2/localstorage.json
  GET  /pub/v1/messageFolders
  GET  /pub/v3/messages
  GET  /pub/v3/messages/<id>
  POST /reload

 * Running on http://0.0.0.0:5000
```

### 3. Test the Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Get folders
curl -H "Authorization: Bearer mock_auth_token_12345" \
     -H "ofw-client: WebApplication" \
     -H "ofw-version: 1.0.0" \
     http://localhost:5000/pub/v1/messageFolders

# Get messages
curl -H "Authorization: Bearer mock_auth_token_12345" \
     -H "ofw-client: WebApplication" \
     -H "ofw-version: 1.0.0" \
     "http://localhost:5000/pub/v3/messages?folders=1&page=1&size=10"
```

### 4. Use with OFW Client

Modify the OFW client to point to the mock server:

```python
# In ofw_messages_client.py, change:
BASE_URL = "http://localhost:5000"  # Instead of ofw.ourfamilywizard.com

# Or create a test version:
class OFWMessagesClientMock(OFWMessagesClient):
    BASE_URL = "http://localhost:5000"
    API_BASE = f"{BASE_URL}/pub"
```

## API Endpoints

All endpoints match the real OFW API:

### GET /ofw/appv2/localstorage.json

Returns localStorage data including auth token.

**Response:**
```json
{
  "auth": "mock_auth_token_12345",
  "userId": 123456,
  "firstName": "Test",
  "lastName": "User"
}
```

### GET /pub/v1/messageFolders

Returns message folders (requires auth).

**Headers:**
- `Authorization: Bearer <token>`
- `ofw-client: WebApplication`
- `ofw-version: 1.0.0`

**Query:**
- `includeFolderCounts` (optional): true/false

**Response:**
```json
{
  "systemFolders": [...],
  "userFolders": [...]
}
```

### GET /pub/v3/messages

Returns messages for a folder (requires auth).

**Query:**
- `folders`: Folder ID
- `page`: Page number (default: 1)
- `size`: Page size (default: 50)
- `sort`: Sort field (default: date)
- `sortDirection`: asc/desc (default: desc)

**Response:**
```json
{
  "metadata": {
    "page": 1,
    "count": 10,
    "first": true,
    "last": false
  },
  "data": [...]
}
```

### GET /pub/v3/messages/{id}

Returns a single message by ID (requires auth).

**Response:**
```json
{
  "id": 123,
  "subject": "Test",
  "body": "Message content...",
  ...
}
```

### POST /reload

Reload data from files (useful during development).

**Response:**
```json
{
  "status": "ok",
  "message": "Data reloaded"
}
```

## Configuration

Environment variables:

```bash
# Data directory
export OFW_DATA_DIR=/path/to/ofw-client/debug

# Auth token (default: mock_auth_token_12345)
export OFW_AUTH_TOKEN=your_token_here

# Port (default: 5000)
export PORT=8080

# Debug mode (default: true)
export FLASK_DEBUG=false

# Strict auth validation (default: false)
export OFW_STRICT_AUTH=true
```

## Data Files

The server loads these files from the data directory:

| File | Purpose |
|------|---------|
| `folders.json` | Message folders |
| `messages.json` | Messages for one folder |
| `all_messages.json` | All messages from all folders |
| `full_message.json` | Full message with body |
| `localstorage_data.json` | Browser localStorage data |

**Missing files:** Server will use default/empty data.

## Development

### Run in Debug Mode

```bash
export FLASK_DEBUG=true
python app.py
```

Changes to code will auto-reload the server.

### Reload Data Without Restart

```bash
# After updating JSON files
curl -X POST http://localhost:5000/reload
```

### View Logs

The server logs all requests with OFW headers:

```
INFO:app:OFW Headers - Client: WebApplication, Version: 1.0.0
```

## Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

```bash
# Start server in one terminal
python app.py

# Run tests in another
cd ../ofw-client
python -m pytest tests/test_with_mock_server.py
```

## Docker

### Build

```bash
docker build -t ofw-server .
```

### Run

```bash
docker run -p 5000:5000 \
  -v /path/to/ofw-client/debug:/data \
  -e OFW_DATA_DIR=/data \
  ofw-server
```

## Production Notes

⚠️ **This is a MOCK server for development/testing only!**

Do NOT use in production:
- No real authentication
- No data persistence
- No rate limiting
- No security features

For production, use the real OFW API.

## Troubleshooting

### "Data not loaded"

Make sure JSON files exist in the data directory:

```bash
ls -lh /path/to/ofw-client/debug/*.json
```

### "401 Unauthorized"

Check your auth token:

```bash
# Default token
Authorization: Bearer mock_auth_token_12345

# Or set custom token
export OFW_AUTH_TOKEN=my_token
```

### "404 Not Found"

Check the endpoint path - see available endpoints:

```bash
curl http://localhost:5000/health
```

## License

Same as the main OFW client project.

## Contributing

See the main project README for contribution guidelines.
