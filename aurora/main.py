import json
from typing import List, Dict
from sanic import Sanic
from sanic import response
from sanic.exceptions import NotFound, InvalidUsage
from sanic.request import Request
from sanic.views import HTTPMethodView
from aurora.configuration import Configuration, Channel
from aurora.models import Preset
from aurora import protocols

app = Sanic(__name__)
config: Configuration = Configuration()
channels_dict: Dict[int, Channel] = config.hardware.channels_dict
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


class ChannelsView(HTTPMethodView):

    async def get(self, request: Request):
        return response.json(channels)


class PresetsView(HTTPMethodView):

    async def get(self, request: Request):
        psets = []
        for preset in presets:
            psets.append(preset.as_dict())
        return response.json(psets)

    async def post(self, request: Request):
        preset = Preset(json.loads(request.body))
        await remove_conflicts(preset)
        presets.append(preset.start())
        return response.json({'status': 201, 'message': 'Created.'}, status=201)

    async def delete(self, request: Request):
        for preset in presets:
            await preset.stop()
            presets.remove(preset)
        return response.json({'status': 201, 'message': 'Ok.'})


class PresetItemView(HTTPMethodView):
    async def get(self, request: Request, preset_id):
        for preset in presets:
            if preset.id == int(preset_id):
                return response.json(preset.as_dict())
        raise NotFound('No preset exists with the given id.')

    async def delete(self, request: Request, preset_id):
        for i in range(0, len(presets)):
            for preset in presets:
                if preset.id == int(preset_id):
                    await preset.stop()
                    presets.remove(preset)
                    return response.json({'status': 200, 'message': 'Deleted.'})
        raise NotFound('No preset exists with the given id.')


if __name__ == '__main__':
    app.add_task(protocols.read_fifo())
    app.add_route(ChannelsView.as_view(), '/api/v2/channels')
    app.add_route(PresetsView.as_view(), '/api/v2/presets')
    app.add_route(PresetItemView.as_view(), '/api/v2/presets/<preset_id>')

    app.run(host=config.core.hostname,
            port=config.core.port,
            workers=1,
            debug=True)
