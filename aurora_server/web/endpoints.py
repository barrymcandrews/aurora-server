import setproctitle

from flask import Blueprint
from flask import jsonify
from flask import request

from aurora_server import configuration
from aurora_server.web import audio_controller as am
from aurora_server.web import light_controller as lm

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
    return jsonify(lm.get_devices() if request.method == 'GET' else lm.set_devices(request.json))


@endpoints.route('/api/v2/lights/<name>', methods=['GET', 'POST'])
def light(name):
    return jsonify(lm.get_device(name) if request.method == 'GET' else lm.set_devices({name: request.json}))


@endpoints.route('/api/v2/audio/sources', methods=['GET', 'POST'])
def audio_sources():
    return jsonify(am.get_sources() if request.method == 'GET' else am.set_sources(request.json))


@endpoints.route('/api/v2/audio/tts/<message>', methods=['POST'])
def audio_tts(message):
    pass


@endpoints.route('/api/v2/subscriptions', methods=['POST'])
async def subscriptions_handler():
    pass


