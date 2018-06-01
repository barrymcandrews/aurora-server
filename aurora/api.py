import json
from typing import List, Dict
from pyximport import pyximport
from sanic import Blueprint
from sanic import response
from sanic.exceptions import NotFound, InvalidUsage
from sanic.request import Request
from sanic_openapi import doc
from aurora.configuration import Configuration, Channel
from aurora.preset import Preset

pyximport.install()
from aurora import hardware

api = Blueprint('aurora-lights', url_prefix='/api/v2')
config: Configuration = Configuration()

presets: List[Preset] = []


async def add_presets(new_presets: List[Preset]):
    """Starts and adds each preset to the Global List."""

    for preset in new_presets:
        presets.append(preset.start())


async def put_presets(new_presets: List[Preset]):
    """Checks for conflicts then adds each preset.

    Checks whether the currently running presets are using channels that
    will be required by the new presets. If there are any conflicts the old
    preset will be stopped. Any channels that were used by a cancelled preset
    that aren't used by a new preset are set to off.

    """

    dropped_channels: List[Channel] = []

    for new_preset in new_presets:
        for new_channel in new_preset.channels:
            for running_preset in presets:
                if new_channel in running_preset.channels:
                    await running_preset.stop()
                    presets.remove(running_preset)
                    dropped_channels += running_preset.channels

    for new_preset in new_presets:
        for new_channel in new_preset.channels:
            if new_channel in dropped_channels:
                dropped_channels.remove(new_channel)

    await add_presets(new_presets)

    for dropped_channel in dropped_channels:
        hardware.set_pwm(dropped_channel.pin, 0)


@api.listener('before_server_stop')
async def remove_all_presets(*args, **kwargs):
    """Removes all presets from the list and sets their channels to off."""

    for preset in presets:
        await preset.stop()
        for channel in preset.channels:
            hardware.set_pwm(channel.pin, 0)
    presets.clear()


async def remove_presets(ids: List[int]):
    """Removes presets from the list with any of the given ids and
    sets their channels to off.
    """

    dropped_channels: List[Channel] = []

    for preset in presets:
        if preset.id in ids:
            await preset.stop()
            for channel in preset.channels:
                dropped_channels.append(channel)
            presets.remove(preset)

    for dropped_channel in dropped_channels:
        hardware.set_pwm(dropped_channel.pin, 0)


# --------------------------------------------------------------- #
# API Route: /
# --------------------------------------------------------------- #

@api.get('/')
@doc.summary('Gets version information for api consumers')
async def get_info(request: Request):
    return response.json({
        "name": config.core.serverName,
        "description": config.core.description,
        "version": config.core.version,
    })


# --------------------------------------------------------------- #
# API Route: /channels
# --------------------------------------------------------------- #

@api.get('/channels')
@doc.summary('Gets a list of channels on the physical device.')
async def get_channels(request: Request):
    return response.json(config.hardware.channels)


# --------------------------------------------------------------- #
# API Route: /presets
# --------------------------------------------------------------- #

@api.get('/presets')
@doc.summary('Gets a list of presets that are currently displaying.')
async def get_presets(request: Request):
    psets = []
    for preset in presets:
        psets.append(preset.as_dict())
    return response.json(psets)


@api.post('/presets')
@doc.summary('Creates a new preset with the given specifications. '
             'Any existing presets with conflicting channels are removed.')
async def post_presets(request: Request):
    body = json.loads(request.body)
    new_presets: List[Preset] = []

    if isinstance(body, list):
        for json_preset in body:
            new_presets.append(Preset(json_preset))
    else:
        new_presets = [Preset(body)]

    await put_presets(new_presets)

    psets = []
    for preset in presets:
        psets.append(preset.as_dict())
    return response.json({'status': 201, 'message': 'Created.', 'presets': psets}, status=201)


@api.delete('/presets')
@doc.summary('Stops all presets executing on the server.')
async def delete_presets(request: Request):
    await remove_all_presets()
    return response.json({'status': 200, 'message': 'Ok.'})


# --------------------------------------------------------------- #
# API Route: /presets/<preset_id>
# --------------------------------------------------------------- #

@api.get('/presets/<preset_id:int>')
@doc.summary('Gets a the value of a preset with a specific ID')
async def get(request: Request, preset_id):
    for preset in presets:
        if preset.id == int(preset_id):
            return response.json(preset.as_dict())
    raise NotFound('No preset exists with the given id.')


@api.delete('/presets/<preset_id:int>')
@doc.summary('Removes a preset with a specific ID')
async def delete(request: Request, preset_id):
    for preset in presets:
        if preset.id == int(preset_id):
            await remove_presets([preset_id])
            return response.json({'status': 200, 'message': 'Deleted.'})
    raise NotFound('No preset exists with the given id.')


# --------------------------------------------------------------- #
# Handle to CORS preflight requests
# --------------------------------------------------------------- #

@api.options('/presets/<preset_id:int>')
@api.options('/presets')
async def empty_response(*args, **kwargs):
    return response.text('', status=204)


