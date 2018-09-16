import json
from typing import List
from pyximport import pyximport
from sanic import Blueprint
from sanic import response
from sanic.exceptions import NotFound
from sanic.request import Request
from sanic_openapi import doc

from aurora import lights
from aurora.configuration import Configuration
from aurora.preset import Preset

pyximport.install()

api = Blueprint('aurora-lights', url_prefix='/api/v2')
config: Configuration = Configuration()


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
    for preset in lights.presets:
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
            new_presets.append(Preset.from_dictionary(json_preset))
    else:
        new_presets = [Preset.from_dictionary(body)]

    await lights.put_presets(new_presets)

    psets = []
    for preset in lights.presets:
        psets.append(preset.as_dict())
    return response.json({'status': 201, 'message': 'Created.', 'presets': psets}, status=201)


@api.delete('/presets')
@doc.summary('Stops all presets executing on the server.')
async def delete_presets(request: Request):
    await lights.clear_presets()
    return response.json({'status': 200, 'message': 'Ok.'})


# --------------------------------------------------------------- #
# API Route: /presets/<preset_id>
# --------------------------------------------------------------- #

@api.get('/presets/<preset_id:int>')
@doc.summary('Gets a the value of a preset with a specific ID')
async def get(request: Request, preset_id):
    for preset in lights.presets:
        if preset.id == int(preset_id):
            return response.json(preset.as_dict())
    raise NotFound('No preset exists with the given id.')


@api.delete('/presets/<preset_id:int>')
@doc.summary('Removes a preset with a specific ID')
async def delete(request: Request, preset_id):
    for preset in lights.presets:
        if preset.id == int(preset_id):
            await lights.remove_presets_by_id([preset_id])
            return response.json({'status': 200, 'message': 'Deleted.'})
    raise NotFound('No preset exists with the given id.')


# --------------------------------------------------------------- #
# Handle to CORS preflight requests
# --------------------------------------------------------------- #

@api.options('/presets/<preset_id:int>')
@api.options('/presets')
async def empty_response(*args, **kwargs):
    return response.text('', status=204)


