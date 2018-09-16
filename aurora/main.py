#!/usr/bin/env python3.6
from setproctitle import setproctitle
import os
import asyncio

import uvloop
from sanic import Sanic
from sanic_openapi import swagger_blueprint, openapi_blueprint
from signal import signal, SIGINT

from aurora.configuration import Configuration
from aurora import protocols, lights
from aurora.api import api

app = Sanic(__name__)
config: Configuration = Configuration()
setproctitle(config.core.process_name)
fifo_task: asyncio.Task = None
server_task: asyncio.Task = None


async def stop_fifo_task():
    fifo_task.cancel()
    try:
        await fifo_task
    except asyncio.CancelledError:
        pass


@app.listener('before_server_stop')
async def stop_presets(app, loop):
    await lights.clear_presets()


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

    server = app.create_server(host=config.core.hostname,
                               port=config.core.port,
                               debug=config.core.debug)

    asyncio.set_event_loop(uvloop.new_event_loop())
    loop = asyncio.get_event_loop()

    server_task = asyncio.ensure_future(server)
    fifo_task = loop.create_task(protocols.read_fifo())

    signal(SIGINT, lambda s, f: loop.stop())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(lights.clear_presets())
        loop.run_until_complete(stop_fifo_task())
        os._exit(0)
