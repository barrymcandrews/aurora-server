import json
from typing import List, Dict
from sanic import Blueprint
from sanic import response
from sanic.exceptions import NotFound, InvalidUsage
from sanic.request import Request
from sanic_openapi import doc
from aurora.configuration import Configuration, Channel
from aurora.preset import Preset

api = Blueprint('aurora-lights', url_prefix='/api/v2')
config: Configuration = Configuration()

channels: List[Channel] = config.hardware.channels
presets: List[Preset] = []


async def remove_conflicts(preset: Preset):
    for channel in preset.channels:
        if channel not in channels:
            raise InvalidUsage('Pin ' + str(channel.pin) + ' not found.')
        for running_preset in presets:
            if channel in running_preset.channels:
                await running_preset.stop()
                presets.remove(running_preset)


# --------------------------------------------------------------- #
# API Route: /channels
# --------------------------------------------------------------- #

@api.get('/channels')
@doc.summary('Gets a list of channels on the physical device.')
async def get_channels(request: Request):
    return response.json(channels)


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
    preset = Preset(json.loads(request.body))
    await remove_conflicts(preset)
    presets.append(preset.start())
    return response.json({'status': 201, 'message': 'Created.'}, status=201)


@api.delete('/presets')
@doc.summary('Stops all presets executing on the server.')
async def delete_presets(request: Request):
    for preset in presets:
        await preset.stop()
        presets.remove(preset)
    return response.json({'status': 201, 'message': 'Ok.'})


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
    for i in range(0, len(presets)):
        for preset in presets:
            if preset.id == int(preset_id):
                await preset.stop()
                presets.remove(preset)
                return response.json({'status': 200, 'message': 'Deleted.'})
    raise NotFound('No preset exists with the given id.')
