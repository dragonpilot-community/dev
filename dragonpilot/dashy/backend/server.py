#!/usr/bin/env python3

"""
Copyright (c) 2025, Rick Lan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, and/or sublicense,
for non-commercial purposes only, subject to the following conditions:

- The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.
- Commercial use (e.g. use in a product, service, or activity intended to
  generate revenue) is prohibited without explicit written permission from
  the copyright holder.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
import json
import os
import logging
import time
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from aiohttp import web, ClientSession, ClientTimeout

from openpilot.common.params import Params
from openpilot.system.hardware import PC, HARDWARE
from openpilot.system.ui.lib.multilang import multilang as base_multilang
from dragonpilot.settings import SETTINGS

# --- Configuration ---
DEFAULT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..') if PC else '/data/media/0/realdata')
WEB_DIST_PATH = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
WEBRTC_TIMEOUT = ClientTimeout(total=10)
CAR_PARAMS_CACHE_TTL = 30  # seconds

logger = logging.getLogger("dashy")


# --- Caching Layer ---
class AppCache:
    """Centralized cache for expensive operations."""

    def __init__(self):
        self._params = None
        self._car_params = None
        self._car_params_time = 0
        self._context = None
        self._context_time = 0

    @property
    def params(self) -> Params:
        """Get shared Params instance."""
        if self._params is None:
            self._params = Params()
        return self._params

    def get_car_params(self):
        """Get cached CarParams data (brand, longitudinal control)."""
        now = time.time()
        if self._car_params is None or (now - self._car_params_time) > CAR_PARAMS_CACHE_TTL:
            self._car_params = self._parse_car_params()
            self._car_params_time = now
        return self._car_params

    def _parse_car_params(self):
        """Parse CarParams from Params store."""
        result = {'brand': '', 'openpilot_longitudinal_control': False}
        try:
            car_params_bytes = self.params.get("CarParams")
            if car_params_bytes:
                from cereal import car
                with car.CarParams.from_bytes(car_params_bytes) as cp:
                    result['brand'] = cp.brand
                    result['openpilot_longitudinal_control'] = cp.openpilotLongitudinalControl
        except Exception as e:
            logger.debug(f"Could not parse CarParams: {e}")
        return result

    def get_settings_context(self):
        """Get context dict for settings condition evaluation."""
        now = time.time()
        if self._context is None or (now - self._context_time) > CAR_PARAMS_CACHE_TTL:
            car_params = self.get_car_params()
            self._context = {
                'brand': car_params['brand'],
                'openpilotLongitudinalControl': car_params['openpilot_longitudinal_control'],
                'LITE': os.getenv("LITE") is not None,
                'MICI': self._check_mici()
            }
            self._context_time = now
        return self._context

    def _check_mici(self):
        """Check if device is MICI type."""
        try:
            return HARDWARE.get_device_type() == "mici"
        except Exception:
            return False

    def get_bool_safe(self, key, default=False):
        """Safely get a boolean param with default."""
        try:
            return self.params.get_bool(key)
        except Exception:
            return default

    def invalidate(self):
        """Invalidate all caches."""
        self._car_params = None
        self._context = None


# --- Helper Functions ---
def api_handler(func):
    """Decorator for API handlers with consistent error handling."""
    @wraps(func)
    async def wrapper(request):
        try:
            return await func(request)
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"{func.__name__} error: {e}", exc_info=True)
            return web.json_response({'error': str(e)}, status=500)
    return wrapper


def get_safe_path(requested_path):
    """Ensures the requested path is within DEFAULT_DIR."""
    combined_path = os.path.join(DEFAULT_DIR, requested_path.lstrip('/'))
    safe_path = os.path.realpath(combined_path)
    if os.path.commonpath((safe_path, DEFAULT_DIR)) == DEFAULT_DIR:
        return safe_path
    return None


def eval_condition(condition, context):
    """Safely evaluate a condition string."""
    if not condition:
        return True
    try:
        return eval(condition, {"__builtins__": {}}, context)
    except Exception as e:
        logger.debug(f"Condition evaluation failed: {condition}, error: {e}")
        return False


def resolve_value(value):
    """Resolve callable values (lambdas) for JSON serialization."""
    return value() if callable(value) else value


# --- API Endpoints ---
@api_handler
async def init_api(request):
    """Provide initial data to the client."""
    cache: AppCache = request.app['cache']
    car_params = cache.get_car_params()

    return web.json_response({
        'is_metric': cache.get_bool_safe("IsMetric"),
        'dp_dev_dashy': cache.get_bool_safe("dp_dev_dashy", True),
        'openpilot_longitudinal_control': car_params['openpilot_longitudinal_control'],
        'ublox_available': cache.get_bool_safe("UbloxAvailable", True),
        'dp_lat_alka': cache.get_bool_safe("dp_lat_alka", False),
    })


@api_handler
async def list_files_api(request):
    """List files and folders."""
    path_param = request.query.get('path', '/')
    safe_path = get_safe_path(path_param)

    if not safe_path or not os.path.isdir(safe_path):
        return web.json_response({'error': 'Invalid or Not Found Path'}, status=404)

    items = []
    for entry in os.listdir(safe_path):
        full_path = os.path.join(safe_path, entry)
        try:
            stat = os.stat(full_path)
            is_dir = os.path.isdir(full_path)
            items.append({
                'name': entry,
                'is_dir': is_dir,
                'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'size': stat.st_size if not is_dir else 0
            })
        except FileNotFoundError:
            continue

    # Sort: directories first (by mtime desc), then files (by mtime desc)
    dirs = sorted([i for i in items if i['is_dir']], key=lambda x: x['mtime'], reverse=True)
    files = sorted([i for i in items if not i['is_dir']], key=lambda x: x['mtime'], reverse=True)

    relative_path = os.path.relpath(safe_path, DEFAULT_DIR)
    return web.json_response({
        'path': '' if relative_path == '.' else relative_path,
        'files': dirs + files
    })


@api_handler
async def serve_player_api(request):
    """Serve the HLS player page."""
    file_path = request.query.get('file')
    if not file_path:
        return web.Response(text="File parameter is required.", status=400)

    player_html_path = os.path.join(WEB_DIST_PATH, 'pages', 'player.html')
    try:
        with open(player_html_path, 'r') as f:
            html_template = f.read()
    except FileNotFoundError:
        return web.Response(text="Player HTML not found.", status=500)

    html = html_template.replace('{{FILE_PATH}}', quote(file_path))
    return web.Response(text=html, content_type='text/html')


@api_handler
async def serve_manifest_api(request):
    """Dynamically generate m3u8 playlist."""
    file_path = request.query.get('file', '').lstrip('/')
    if not file_path:
        return web.Response(text="File parameter is required.", status=400)

    encoded_path = quote(file_path)
    manifest = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:60\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXTINF:60.0,\n/media/{encoded_path}\n#EXT-X-ENDLIST\n"
    return web.Response(text=manifest, content_type='application/vnd.apple.mpegurl')


@api_handler
async def get_settings_config_api(request):
    """Get the settings configuration from settings.py."""
    cache: AppCache = request.app['cache']
    params = cache.params

    # Update language if changed
    current_lang = params.get("LanguageSetting")
    if current_lang:
        lang_str = current_lang.decode() if isinstance(current_lang, bytes) else str(current_lang)
        lang_str = lang_str.removeprefix("main_")
        if lang_str != base_multilang.language and lang_str in base_multilang.languages.values():
            base_multilang._language = lang_str
            base_multilang.setup()

    context = cache.get_settings_context()
    settings_with_values = []

    for section in SETTINGS:
        if not eval_condition(section.get('condition'), context):
            continue

        section_copy = section.copy()
        settings_list = []

        for setting in section.get('settings', []):
            if not eval_condition(setting.get('condition'), context):
                continue

            setting_copy = setting.copy()
            key = setting['key']

            # Resolve callable values
            for field in ['title', 'description', 'suffix', 'special_value_text']:
                if field in setting_copy:
                    setting_copy[field] = resolve_value(setting_copy[field])
            if 'options' in setting_copy:
                setting_copy['options'] = [resolve_value(opt) for opt in setting_copy['options']]

            # Get current value based on type
            setting_copy['current_value'] = _get_setting_value(params, setting)
            settings_list.append(setting_copy)

        if settings_list:
            section_copy['settings'] = settings_list
            settings_with_values.append(section_copy)

    return web.json_response({'settings': settings_with_values})


def _get_setting_value(params, setting):
    """Get current value for a setting from Params."""
    key = setting['key']
    setting_type = setting['type']
    default = setting.get('default', 0)

    try:
        if setting_type == 'toggle_item':
            return params.get_bool(key)
        elif setting_type == 'double_spin_button_item':
            value = params.get(key)
            return float(value) if value is not None else float(default)
        else:  # spin_button_item, text_spin_button_item
            value = params.get(key)
            return int(value) if value is not None else int(default)
    except Exception as e:
        logger.warning(f"Error getting value for {key}: {e}")
        if setting_type == 'toggle_item':
            return False
        elif setting_type == 'double_spin_button_item':
            return float(default)
        return int(default)


@api_handler
async def save_param_api(request):
    """Save a single param value.

    Usage: POST /api/settings/params/{name}
    Body: { "value": <value> }
    """
    param_name = request.match_info.get('param_name')
    if not param_name:
        return web.json_response({'error': 'param_name is required'}, status=400)

    cache: AppCache = request.app['cache']
    params = cache.params
    data = await request.json()

    if 'value' not in data:
        return web.json_response({'error': 'value is required in body'}, status=400)

    _save_param(params, param_name, data['value'])
    logger.info(f"Param saved: {param_name}={data['value']}")

    return web.json_response({'status': 'success', 'key': param_name, 'value': data['value']})


def _save_param(params, key, value):
    """Save a single param value with proper type handling."""
    try:
        param_type = params.get_type(key)

        if param_type == 1:  # BOOL
            params.put_bool(key, bool(value))
        elif param_type == 2:  # INT
            params.put(key, int(value))
        elif param_type == 3:  # FLOAT
            params.put(key, float(value))
        elif isinstance(value, bool):
            params.put_bool(key, value)
        else:
            params.put(key, str(value) if not isinstance(value, str) else value)

        logger.debug(f"Saved {key}={value} (type={param_type})")
    except Exception as e:
        logger.error(f"Error saving param {key}={value}: {e}")
        raise


def _get_param_value(params, key):
    """Get a single param value with proper type handling."""
    try:
        return params.get_bool(key)
    except Exception:
        raw_value = params.get(key)
        if raw_value is None:
            return None
        elif isinstance(raw_value, bytes):
            return raw_value.decode('utf-8')
        return raw_value


@api_handler
async def get_param_api(request):
    """Get a single param value."""
    param_name = request.match_info.get('param_name')
    if not param_name:
        return web.json_response({'error': 'param_name is required'}, status=400)

    cache: AppCache = request.app['cache']
    params = cache.params
    value = _get_param_value(params, param_name)

    return web.json_response({'key': param_name, 'value': value})


@api_handler
async def get_model_list_api(request):
    """Get the model list and current selection."""
    cache: AppCache = request.app['cache']
    params = cache.params

    # Get model list
    model_list = {}
    try:
        model_list_raw = params.get("dp_dev_model_list")
        if model_list_raw:
            model_list = json.loads(model_list_raw)
    except Exception as e:
        logger.debug(f"Could not parse dp_dev_model_list: {e}")

    # Get current selection
    selected_model = ""
    try:
        selected_raw = params.get("dp_dev_model_selected")
        if selected_raw:
            selected_model = selected_raw.decode('utf-8') if isinstance(selected_raw, bytes) else str(selected_raw)
    except Exception as e:
        logger.debug(f"Could not get dp_dev_model_selected: {e}")

    return web.json_response({
        'model_list': model_list,
        'selected_model': selected_model
    })


@api_handler
async def save_model_selection_api(request):
    """Save the selected model."""
    cache: AppCache = request.app['cache']
    params = cache.params
    data = await request.json()

    selected_model = data.get('selected_model', '')

    if not selected_model or selected_model == "[AUTO]":
        params.put("dp_dev_model_selected", "")
        logger.info("Model selection cleared (AUTO mode)")
    else:
        params.put("dp_dev_model_selected", selected_model)
        logger.info(f"Model selection saved: {selected_model}")

    return web.json_response({'status': 'success'})


@api_handler
async def webrtc_stream_proxy(request):
    """Proxy WebRTC stream requests to webrtcd."""
    host = request.host.split(':')[0]
    body = await request.read()
    session: ClientSession = request.app['http_session']

    async with session.post(
        f'http://{host}:5001/stream',
        data=body,
        headers={'Content-Type': 'application/json'}
    ) as resp:
        response_body = await resp.read()
        return web.Response(
            body=response_body,
            status=resp.status,
            content_type=resp.content_type
        )


# --- CORS Middleware ---
@web.middleware
async def cors_middleware(request, handler):
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    # Disable caching for web assets
    path = request.path.lower()
    if path.endswith(('.html', '.js', '.css')) or path == '/':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response


async def handle_cors_preflight(request):
    return web.Response(status=200, headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
    })


# --- Application Setup ---
async def on_startup(app):
    """Initialize app-level resources."""
    app['cache'] = AppCache()
    app['http_session'] = ClientSession(timeout=WEBRTC_TIMEOUT)
    logger.info("Dashy server started")


async def on_cleanup(app):
    """Cleanup app-level resources."""
    await app['http_session'].close()
    logger.info("Dashy server stopped")


def setup_aiohttp_app(host: str, port: int, debug: bool):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = web.Application(middlewares=[cors_middleware])
    app['port'] = port

    # API routes
    app.router.add_get("/api/init", init_api)
    app.router.add_get("/api/files", list_files_api)
    app.router.add_get("/api/play", serve_player_api)
    app.router.add_get("/api/manifest.m3u8", serve_manifest_api)
    app.router.add_get("/api/settings", get_settings_config_api)
    app.router.add_get("/api/settings/params/{param_name}", get_param_api)
    app.router.add_post("/api/settings/params/{param_name}", save_param_api)
    app.router.add_get("/api/models", get_model_list_api)
    app.router.add_post("/api/models/select", save_model_selection_api)
    app.router.add_post("/api/stream", webrtc_stream_proxy)
    app.router.add_route('OPTIONS', '/{tail:.*}', handle_cors_preflight)

    # Static files
    app.router.add_static('/media', path=DEFAULT_DIR, name='media', show_index=False, follow_symlinks=False)
    app.router.add_static('/download', path=DEFAULT_DIR, name='download', show_index=False, follow_symlinks=False)
    app.router.add_get("/", lambda r: web.FileResponse(os.path.join(WEB_DIST_PATH, "index.html")))
    app.router.add_static("/", path=WEB_DIST_PATH)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app


def main():
    parser = argparse.ArgumentParser(description="Dashy Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to listen on")
    parser.add_argument("--port", type=int, default=5088, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    app = setup_aiohttp_app(args.host, args.port, args.debug)
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
