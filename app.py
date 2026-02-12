"""
OFW Mock Server
===============

A Flask-based mock server that mimics Our Family Wizard's API endpoints.
Serves data from JSON files exported by the OFW client.

This allows you to:
- Test the OFW client without hitting the real API
- Develop offline
- Control test data
- Debug API interactions
"""

from flask import Flask, jsonify, request, Response
from functools import wraps
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

app = Flask(__name__)

# Configuration
DATA_DIR = os.environ.get('OFW_DATA_DIR', '../debug')
AUTH_TOKEN = os.environ.get('OFW_AUTH_TOKEN', 'mock_auth_token_12345')

# In-memory data store (loaded from files)
data_store = {
    'folders': None,
    'messages': {},  # folder_id -> list of messages
    'full_messages': {},  # message_id -> full message
    'localstorage': None,
}


def load_data():
    """Load data from JSON files in the data directory."""
    global data_store
    
    data_path = Path(DATA_DIR)
    
    # Load folders
    folders_file = data_path / 'folders.json'
    if folders_file.exists():
        with open(folders_file, 'r') as f:
            data_store['folders'] = json.load(f)
        print(f"✓ Loaded folders from {folders_file}")
    
    # Load messages
    messages_file = data_path / 'messages.json'
    if messages_file.exists():
        with open(messages_file, 'r') as f:
            messages_data = json.load(f)
            # Extract folder_id from first message if available
            if messages_data.get('data'):
                folder_id = messages_data['data'][0].get('folder')
                data_store['messages'][folder_id] = messages_data
        print(f"✓ Loaded messages from {messages_file}")
    
    # Load all messages (if exists)
    all_messages_file = data_path / 'all_messages.json'
    if all_messages_file.exists():
        with open(all_messages_file, 'r') as f:
            all_messages = json.load(f)
            # Group by folder
            if all_messages:
                for msg in all_messages:
                    folder_id = msg.get('folder')
                    if folder_id not in data_store['messages']:
                        data_store['messages'][folder_id] = {'data': [], 'metadata': {}}
                    if isinstance(data_store['messages'][folder_id], dict):
                        data_store['messages'][folder_id]['data'].append(msg)
        print(f"✓ Loaded all messages from {all_messages_file}")
    
    # Load full message (if exists)
    full_message_file = data_path / 'full_message.json'
    if full_message_file.exists():
        with open(full_message_file, 'r') as f:
            full_msg = json.load(f)
            msg_id = full_msg.get('id')
            if msg_id:
                data_store['full_messages'][msg_id] = full_msg
        print(f"✓ Loaded full message from {full_message_file}")
    
    # Load localstorage
    localstorage_file = data_path / 'localstorage_data.json'
    if localstorage_file.exists():
        with open(localstorage_file, 'r') as f:
            data_store['localstorage'] = json.load(f)
        print(f"✓ Loaded localstorage from {localstorage_file}")
    
    print(f"\n✓ Data loaded from {DATA_DIR}")
    print(f"  Folders: {'Yes' if data_store['folders'] else 'No'}")
    print(f"  Message folders: {len(data_store['messages'])}")
    print(f"  Full messages: {len(data_store['full_messages'])}")
    print(f"  LocalStorage: {'Yes' if data_store['localstorage'] else 'No'}")


def require_auth(f):
    """Decorator to require Bearer token authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No Authorization header'}), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid Authorization header format'}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # For mock server, accept any token (or check against AUTH_TOKEN)
        # In production, you'd validate the token properly
        if token != AUTH_TOKEN and os.environ.get('OFW_STRICT_AUTH') == 'true':
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_ofw_headers(f):
    """Decorator to check for OFW-specific headers."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ofw_client = request.headers.get('ofw-client')
        ofw_version = request.headers.get('ofw-version')
        
        # Just log them, don't enforce (for flexibility)
        if ofw_client or ofw_version:
            app.logger.info(f"OFW Headers - Client: {ofw_client}, Version: {ofw_version}")
        
        return f(*args, **kwargs)
    
    return decorated_function


# Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'ofw-mock-server',
        'data_loaded': {
            'folders': data_store['folders'] is not None,
            'messages': len(data_store['messages']) > 0,
            'full_messages': len(data_store['full_messages']) > 0,
        }
    })


@app.route('/ofw/appv2/localstorage.json', methods=['GET'])
def get_localstorage():
    """Return localStorage data."""
    if data_store['localstorage']:
        # Return the actual localstorage data
        response_data = data_store['localstorage'].copy()
        # Ensure auth token is set
        if 'auth' not in response_data:
            response_data['auth'] = AUTH_TOKEN
        return jsonify(response_data)
    else:
        # Return minimal localstorage with auth token
        return jsonify({
            'auth': AUTH_TOKEN,
            'userId': 123456,
            'firstName': 'Mock',
            'lastName': 'User'
        })


@app.route('/pub/v1/messageFolders', methods=['GET'])
@require_auth
@require_ofw_headers
def get_folders():
    """Return message folders."""
    include_counts = request.args.get('includeFolderCounts', 'true').lower() == 'true'
    
    if data_store['folders']:
        return jsonify(data_store['folders'])
    else:
        # Return default folders
        return jsonify({
            'systemFolders': [
                {
                    'id': 1,
                    'name': 'Inbox',
                    'folderOrder': 1,
                    'totalMessageCount': 0,
                    'unreadMessageCount': 0,
                    'folderType': 'INBOX'
                },
                {
                    'id': 2,
                    'name': 'Action Items',
                    'folderOrder': 2,
                    'totalMessageCount': 0,
                    'unreadMessageCount': 0,
                    'folderType': 'ACTION_ITEMS'
                },
                {
                    'id': 3,
                    'name': 'Notifications',
                    'folderOrder': 3,
                    'totalMessageCount': 0,
                    'unreadMessageCount': 0,
                    'folderType': 'SYSTEM_MESSAGES'
                }
            ],
            'userFolders': []
        })


@app.route('/pub/v3/messages', methods=['GET'])
@require_auth
@require_ofw_headers
def get_messages():
    """Return messages for a folder."""
    folder_id = request.args.get('folders', type=int)
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 50, type=int)
    sort = request.args.get('sort', 'date')
    sort_direction = request.args.get('sortDirection', 'desc')
    
    # Get messages for this folder
    if folder_id and folder_id in data_store['messages']:
        messages_data = data_store['messages'][folder_id]
        
        # Handle pagination
        if isinstance(messages_data, dict) and 'data' in messages_data:
            all_msgs = messages_data['data']
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            page_msgs = all_msgs[start_idx:end_idx]
            
            return jsonify({
                'metadata': {
                    'page': page,
                    'count': len(page_msgs),
                    'first': page == 1,
                    'last': end_idx >= len(all_msgs)
                },
                'data': page_msgs
            })
        else:
            # Old format - return as-is
            return jsonify(messages_data)
    else:
        # No messages for this folder
        return jsonify({
            'metadata': {
                'page': page,
                'count': 0,
                'first': True,
                'last': True
            },
            'data': []
        })


@app.route('/pub/v3/messages/<int:message_id>', methods=['GET'])
@require_auth
@require_ofw_headers
def get_message(message_id):
    """Return a single message by ID."""
    if message_id in data_store['full_messages']:
        return jsonify(data_store['full_messages'][message_id])
    else:
        # Try to find it in the messages lists
        for folder_msgs in data_store['messages'].values():
            if isinstance(folder_msgs, dict) and 'data' in folder_msgs:
                for msg in folder_msgs['data']:
                    if msg.get('id') == message_id:
                        # Return with mock body if not present
                        result = msg.copy()
                        if 'body' not in result:
                            result['body'] = f"This is a mock message body for message {message_id}."
                        return jsonify(result)
        
        return jsonify({'error': 'Message not found'}), 404


@app.route('/reload', methods=['POST'])
def reload_data():
    """Reload data from files (useful for development)."""
    load_data()
    return jsonify({'status': 'ok', 'message': 'Data reloaded'})


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'path': request.path,
        'available_endpoints': [
            '/health',
            '/ofw/appv2/localstorage.json',
            '/pub/v1/messageFolders',
            '/pub/v3/messages',
            '/pub/v3/messages/<id>',
            '/reload'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


def main():
    """Run the Flask server."""
    print("="*70)
    print("OFW MOCK SERVER")
    print("="*70)
    print()
    print(f"Data directory: {DATA_DIR}")
    print(f"Auth token: {AUTH_TOKEN}")
    print()
    
    # Load data from files
    load_data()
    
    print()
    print("="*70)
    print("Starting server...")
    print("="*70)
    print()
    print("Available endpoints:")
    print("  GET  /health")
    print("  GET  /ofw/appv2/localstorage.json")
    print("  GET  /pub/v1/messageFolders")
    print("  GET  /pub/v3/messages")
    print("  GET  /pub/v3/messages/<id>")
    print("  POST /reload")
    print()
    print("To use with OFW client:")
    print("  Set BASE_URL = 'http://localhost:5000'")
    print()
    
    # Run server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
