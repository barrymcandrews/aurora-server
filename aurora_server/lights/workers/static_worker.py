import asyncio
from aurora_server.log import setup_logger
from .light_worker import LightWorker

logger = setup_logger("lights.workers.FilterWorker")


class StaticWorker(LightWorker):

    async def run(self):
        try:
            while True:
                preset_type = self.preset['type']

                if preset_type == 'levels':
                    await self.set_levels(self.preset)
                    break
                elif preset_type == 'none':
                    await self.set_off()
                    break
                elif preset_type == 'fade':
                    await self.set_fade(self.preset)
                elif preset_type == 'sequence':
                    await self.set_sequence(self.preset)
                else:
                    print('Unknown type: "' + preset_type + '"')
                    break
        except asyncio.CancelledError:
            pass
