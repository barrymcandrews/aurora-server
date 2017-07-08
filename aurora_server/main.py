import setproctitle
import signal
import sys
from flask import Flask

from aurora_server.audio import sources
from aurora_server.lights import light_manager
from aurora_server.web.endpoints import endpoints
from aurora_server import configuration
from aurora_server import fifo

setproctitle.setproctitle('aurora_server')
config = configuration.Configuration()

app = Flask(__name__)
app.register_blueprint(endpoints)


def shutdown(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    sources.stop_current_source()
    sys.exit(1)


if __name__ == '__main__':

    lights_process = light_manager.start_process()
    audio_thread = fifo.start_reading()

    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    app.run(host=config.core.hostname, port=config.core.port)

