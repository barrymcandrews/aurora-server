import setproctitle

from flask import Blueprint
from flask import jsonify
from flask import request

from aurora_server import configuration
from . import service_controller as sc

setproctitle.setproctitle('aurora_server')
cm = configuration.Configuration()

endpoints = Blueprint('endpoints', __name__)


@endpoints.route('/api/v2', methods=['GET'])
def server_info():
    """returns the api docs"""
    return jsonify({
        'name': 'aurora_server',
        'version': '2.0',
        'author': 'M. Barry McAndrews'
    })


@endpoints.route('/api/v2/lights', methods=['GET', 'POST'])
def lights():
    return jsonify(sc.get_devices() if request.method == 'GET' else sc.set_devices(request.json))


@endpoints.route('/api/v2/lights/<name>', methods=['GET', 'POST'])
def light(name):
    return jsonify(sc.get_device(name) if request.method == 'GET' else sc.set_devices({name: request.json}))


@endpoints.route('/api/v2/audio/sources', methods=['GET', 'POST'])
def audio_sources():
    return jsonify(sc.get_sources() if request.method == 'GET' else sc.set_sources(request.json))


@endpoints.route('/api/v2/audio/tts/<message>', methods=['POST'])
def audio_tts(message):
    pass


@endpoints.route('/api/v2/subscriptions', methods=['POST'])
async def subscriptions_handler():
    pass

