#!/usr/bin/env python3.6
from setproctitle import setproctitle
import os
import asyncio
from sanic import Sanic
from sanic_cors import CORS
from sanic_openapi import swagger_blueprint, openapi_blueprint
from aurora.configuration import Configuration
from aurora import protocols, lights
from aurora.api import api

app = Sanic(__name__)
CORS(app)
config: Configuration = Configuration()
setproctitle(config.core.process_name)
fifo_task: asyncio.Task = None


@app.listener('before_server_start')
def start_fifo_task(app, loop):
    global fifo_task
    fifo_task = loop.create_task(protocols.read_fifo())


@app.listener('before_server_stop')
async def stop_fifo_task(app, loop):
    global fifo_task
    fifo_task.cancel()
    await fifo_task


@app.listener('before_server_stop')
async def stop_presets(app, loop):
    await lights.remove_all_presets()


if __name__ == '__main__':
    app.config.LOGO = config.core.logo
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
    os._exit(os.EX_OK)
