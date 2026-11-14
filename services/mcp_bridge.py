"""Small, read-only laptop MCP service for the XiaoZhi external endpoint.

The endpoint credential is read only from the process environment. It is never
written to logs, the status file, firmware, or command-line arguments.
"""
import asyncio
from datetime import datetime, timezone, timedelta
import html
import json
import logging
import os
from pathlib import Path
import platform
import time
from urllib.parse import urlsplit, parse_qs

import psutil
import websockets

ROOT = Path(__file__).resolve().parent.parent
STATUS_PATH = ROOT / '.local/mcp-status.json'
STARTED = time.time()
TOOLS = [
    {'name': 'troko_pc_status', 'description': 'Read laptop CPU, memory and battery status; no file or process access.',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'troko_local_time', 'description': 'Read current date and time in Guayaquil, Ecuador (UTC-5).',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
]


def normalize_endpoint(value):
    value = html.unescape(value).strip().replace('\\:', ':')
    parsed = urlsplit(value)
    if (parsed.scheme != 'wss' or parsed.hostname != 'api.xiaozhi.me' or
            parsed.port not in (None, 443) or parsed.path not in ('/mcp', '/mcp/') or
            parsed.username or parsed.password or parsed.fragment):
        raise ValueError('Expected the secure XiaoZhi MCP endpoint')
    tokens = parse_qs(parsed.query).get('token', [])
    if len(tokens) != 1 or len(tokens[0].split('.')) != 3 or any(c.isspace() for c in value):
        raise ValueError('Invalid endpoint token format')
    return value


def error(request_id, code, message):
    return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': code, 'message': message}}


def dispatch(request):
    if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
        return error(None, -32600, 'Invalid request')
    if 'id' not in request:  # Notifications require no response.
        return None
    request_id = request['id']
    method = request.get('method')
    params = request.get('params', {})
    if not isinstance(params, dict):
        return error(request_id, -32602, 'Expected object parameters')
    if method == 'initialize':
        version = params.get('protocolVersion')
        supported = {'2024-11-05', '2025-03-26', '2025-06-18'}
        result = {'protocolVersion': version if isinstance(version, str) and version in supported else '2024-11-05',
                  'capabilities': {'tools': {'listChanged': False}},
                  'serverInfo': {'name': 'troko-laptop-readonly', 'version': '1.0.0'}}
    elif method == 'ping':
        result = {}
    elif method == 'tools/list':
        result = {'tools': TOOLS}
    elif method == 'tools/call':
        name = params.get('name')
        if not isinstance(name, str) or name not in {tool['name'] for tool in TOOLS}:
            return error(request_id, -32602, 'Unknown tool')
        if params.get('arguments', {}) != {}:
            return error(request_id, -32602, 'This tool accepts no arguments')
        if name == 'troko_local_time':
            result_data = {'timezone': 'America/Guayaquil',
                           'datetime': datetime.now(timezone(timedelta(hours=-5))).isoformat()}
        else:
            memory = psutil.virtual_memory()
            battery = psutil.sensors_battery()
            result_data = {'os': platform.system(), 'cpu_percent': psutil.cpu_percent(interval=None),
                           'memory_percent': memory.percent, 'memory_total_bytes': memory.total,
                           'battery_percent': battery.percent if battery else None,
                           'power_plugged': battery.power_plugged if battery else None}
        result = {'content': [{'type': 'text', 'text': json.dumps(result_data)}], 'isError': False}
    else:
        return error(request_id, -32601, 'Method not found')
    return {'jsonrpc': '2.0', 'id': request_id, 'result': result}


def write_status(**values):
    STATUS_PATH.parent.mkdir(exist_ok=True)
    status = {'pid': os.getpid(), 'started_unix': STARTED,
              'updated_utc': datetime.now(timezone.utc).isoformat(), **values}
    temporary = STATUS_PATH.with_suffix('.tmp')
    temporary.write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    temporary.replace(STATUS_PATH)


async def run(endpoint):
    backoff = 1
    while True:
        write_status(connected=False, initialized=False, state='connecting')
        try:
            async with websockets.connect(endpoint, max_size=65536, max_queue=8,
                                          open_timeout=15, ping_interval=20) as socket:
                backoff = 1
                initialized = False
                listed = False
                print('MCP WebSocket connected', flush=True)
                write_status(connected=True, initialized=False, tools_listed=False)
                async for message in socket:
                    try:
                        request = json.loads(message)
                    except (ValueError, UnicodeDecodeError):
                        await socket.send(json.dumps(error(None, -32700, 'Parse error')))
                        continue
                    response = dispatch(request)
                    if response is not None:
                        await socket.send(json.dumps(response))
                    if isinstance(request, dict):
                        method = request.get('method')
                        initialized |= method == 'initialize' and response is not None and 'result' in response
                        listed |= method == 'tools/list' and response is not None and 'result' in response
                        if method in ('initialize', 'tools/list', 'tools/call'):
                            # Log only the method, never request payloads, arguments or URLs.
                            print('MCP request:', method, flush=True)
                        write_status(connected=True, initialized=initialized, tools_listed=listed)
        except Exception as exception:
            # Exception text can contain credentials in library-generated messages.
            print('MCP reconnect:', type(exception).__name__, flush=True)
            write_status(connected=False, initialized=False, state='retrying',
                         error_type=type(exception).__name__)
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 60)


if __name__ == '__main__':
    logging.getLogger('websockets').setLevel(logging.CRITICAL)
    endpoint = normalize_endpoint(os.environ.get('MCP_ENDPOINT', ''))
    psutil.cpu_percent(interval=None)
    try:
        asyncio.run(run(endpoint))
    except KeyboardInterrupt:
        write_status(connected=False, initialized=False, state='stopped')
