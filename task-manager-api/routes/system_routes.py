from datetime import datetime

from flask import Blueprint

system_bp = Blueprint('system', __name__)

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


@system_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now())}


@system_bp.route('/')
def index():
    return {'message': API_NAME, 'version': API_VERSION}
