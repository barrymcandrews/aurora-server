#!/usr/bin/env python3
from service_controller import ServiceType
from flask import Flask
from flask import jsonify
from flask import request
import threading
import service_controller as sc

app = Flask(__name__)
sc.setup()


@app.route('/api/v1', methods=['GET'])
def api_docs():
    """returns the api docs"""
    return jsonify({'message': 'The api docs will eventually be here.'})


@app.route('/api/v1/service', methods=['GET'])
def list_services():
    """returns a json array with all the statuses of the services"""
    services = []
    for s in ServiceType:
        services.append({'name': s.name, 'status': sc.get_service_status(s)})
    at = threading.active_count()

    return jsonify({'services': services, 'active-threads': at})


@app.route('/api/v1/service/<name>', methods=['GET', 'POST'])
def list_service(name):
    """returns the status of the specific service"""
    name = name.upper()
    if name in ServiceType.__members__:
        if request.json is not None and 'status' in request.json:
            if request.json['status'] == 'started':
                sc.start_service(ServiceType[name])
            elif request.json['status'] == 'stopped':
                sc.stop_service(ServiceType[name])
        return jsonify({'name': name, 'status': sc.get_service_status(ServiceType[name])})
    else:
        res = jsonify({
            'type': 'UnknownServiceException',
            'message': 'The server can not find a service by that name.'
        })
        res.status_code = 400
        return res


@app.route('/api/v1/s/static-light', methods=['GET', 'POST'])
def static_light():
    if request.method == 'POST' and request.json is not None:
        sc.send_message(ServiceType.STATIC_LIGHT, request.json)
    return 'this controls static light'


@app.route('/api/v1/s/alert')
def alert():
    return 'this controls alerts'


@app.route('/api/v1/s/alert/speech/<text>')
def speech_only_alert(text):
    return 'this speaks the given text'


if __name__ == '__main__':
    app.run()
