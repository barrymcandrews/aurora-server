#!/usr/bin/env python3
from service_controller import ServiceType
from flask import Flask
from flask import jsonify
from flask import request
import threading
import signal
import sys
import service_controller as sc
import configuration_manager
import bor_parser as bor

app = Flask(__name__)
sc.setup()
cm = configuration_manager.Configuration()


@app.route('/api/v1', methods=['GET'])
def api_docs():
    """returns the api docs"""
    return jsonify({'message': 'The api docs will eventually be here.'})


@app.route('/api/v1/services', methods=['GET'])
def list_services():
    """returns a json array with all the statuses of the services"""
    services = []
    for s in ServiceType:
        services.append({'name': s.name, 'status': sc.get_service_status(s)})
    at = threading.active_count()

    return jsonify({'services': services, 'active-threads': at})


@app.route('/api/v1/services/<name>', methods=['GET', 'POST'])
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
    if request.method == 'POST':
        if request.headers['Content-Type'].lower() == "application/borealis":
            req = bor.parse(request.get_data().decode('utf-8'))
        elif request.headers['Content-Type'].lower() == "application/json":
            req = request.get_json()
        else:
            res = jsonify({
                'type': 'UnknownContentTypeException',
                'message': 'The server does not recognize the content-type you sent.'
            })
            res.status_code = 400
            return res

        sc.send_message(ServiceType.STATIC_LIGHT, req)
        return jsonify(req)
    return jsonify(sc.request_var(ServiceType.STATIC_LIGHT, 'current_preset'))


def shutdown(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)
    for s in sc.ServiceType:
        sc.stop_service(s)
    sys.exit(1)

if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, shutdown)
    app.run(port=cm.core.port, host=cm.core.hostname)
