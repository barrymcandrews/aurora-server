import os
import subprocess
import signal
from aurora_server import configuration

config = configuration.Configuration()
config_path = os.path.dirname(os.path.realpath(__file__)) + '/../../config/mopidy.conf'
audio_sources = {
    'mopidy': ['mopidy', '--config', config_path]
}

process: subprocess.Popen = None
active_source = 'none'


def start_source(name):
    global process, active_source

    if name in audio_sources or name == 'none':
        stop_current_source()
        active_source = name
        if name != 'none':
            setup_fifo()
            process = subprocess.Popen(audio_sources[name],
                                       stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE,
                                       preexec_fn=os.setsid)


def stop_current_source():
    global active_source

    if process is not None and process.poll() is None:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        os.unlink(config.lights.fifo_path)
        active_source = 'none'


def setup_fifo():
    if os.path.exists(config.lights.fifo_path):
        os.remove(config.lights.fifo_path)
    os.mkfifo(config.lights.fifo_path, 0o0777)
