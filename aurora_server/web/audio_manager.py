from aurora_server.audio import sources


def get_sources() -> dict:
    return {
        'sources': list(sources.audio_sources.keys()),
        'active': sources.active_source
    }


def set_sources(data) -> dict:
    if 'active' in data and (data['active'] in sources.audio_sources or data['active'] == 'none'):
        sources.start_source(data['active'])

    return get_sources()
