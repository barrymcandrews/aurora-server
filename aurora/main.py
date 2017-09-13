#!/usr/bin/env python3.6
from setproctitle import setproctitle
from sanic import Sanic
from sanic_openapi import swagger_blueprint, openapi_blueprint
from aurora.configuration import Configuration
from aurora import protocols
from aurora.api import api

app = Sanic(__name__)
config: Configuration = Configuration()
setproctitle(config.core.process_name)


if __name__ == '__main__':
    app.config.LOGO = config.core.logo
    app.add_task(protocols.read_fifo())
    app.blueprint(api)

    if config.core.openapi:
        app.blueprint(openapi_blueprint)
        app.blueprint(swagger_blueprint)
        app.config.API_VERSION = config.core.version
        app.config.API_TITLE = 'Aurora Light API'
        app.config.API_DESCRIPTION = 'Control one or more RGB LED strip.'
        app.config.API_PRODUCES_CONTENT_TYPES = ['application/json']
        app.config.API_CONTACT_EMAIL = 'bmcandrews@pitt.edu'

    app.run(host=config.core.hostname,
            port=config.core.port,
            workers=1,
            debug=config.core.debug)
