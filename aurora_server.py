import service_controller as sc
from service_controller import Service
from flask import Flask
from flask import jsonify
from flask import request


app = Flask(__name__)
sc.setup()


@app.route('/api/v1', methods=['GET'])
def api_docs():
    """returns the api docs"""
    return jsonify({"message": "The api docs will eventually be here."})


@app.route('/api/v1/service', methods=['GET'])
def list_services():
    """returns a json array with all the statuses of the services"""
    services = []
    for s in Service:
        services.append({"name": s.name, "status": sc.get_service_status(s)})
    return jsonify(services)


@app.route('/api/v1/service/<name>', methods=['GET', 'POST'])
def list_service(name):
    """returns the status of the specific service"""
    if name in Service:
        # TODO: parse json for start/stop command
        return jsonify({"name": name, "status": sc.get_service_status(Service[name])})
    res = jsonify({
        "type": "UnknownServiceException",
        "message": "The server can not find a service by that name."
    })
    res.status_code = 400
    return res


@app.route('/api/v1/s/static-light')
def static_light():
    return 'this controls static light'


@app.route('/api/v1/s/alert')
def alert():
    return 'this controls alerts'


@app.route('/api/v1/s/alert/speech/<text>')
def speech_only_alert(text):
    return 'this speaks the given text'


if __name__ == '__main__':
    app.run()
