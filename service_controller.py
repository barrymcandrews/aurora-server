from enum import Enum

import configuration_manager
from log import setup_logger
from services.Service import Service
from services.StaticLightService import StaticLightService
from services.LightShowService import LightShowService

cm = configuration_manager.Configuration()


class ServiceType(Enum):
    STATIC_LIGHT = 0
    LIGHT_SHOW = 1

classes = [StaticLightService, LightShowService]
instances = [Service(), Service()]
logger = setup_logger('Service Controller')


def setup():
    """Starts services that should be running initially"""
    logger.info('Setting up services...')
    if cm.light_show.run_at_start and cm.static_light.run_at_start:
        logger.error("Config Error: Static Light and Light Show can not run at the same time.")
    else:
        if cm.static_light.run_at_start:
            start_service(ServiceType.STATIC_LIGHT)

        if cm.light_show.run_at_start:
            start_service(ServiceType.LIGHT_SHOW)


def start_service(service: ServiceType):
    logger.info("Starting service " + service.name + "...")
    instances[service.value] = classes[service.value]()
    if instances[service.value].requires_gpio:
        for s, i in zip(instances, ServiceType):
            if s.isAlive() and s.requires_gpio:
                logger.info("Stopping conflicting services...")
                stop_service(i)
    instances[service.value].start()
    if instances[service.value].isAlive():
        logger.info(service.name + " started.")


def stop_service(service: ServiceType):
    if instances[service.value].isAlive():
        logger.info("Stopping service " + service.name + "...")
        instances[service.value].stop()
        instances[service.value].join(timeout=1000)
        message = " is not responding." if instances[service.value].isAlive() else " successfully stopped."
        logger.info(service.name + message)


def get_service_status(service: ServiceType) -> str:
    return 'started' if instances[service.value].isAlive() else 'stopped'


def send_message(service: ServiceType, message):
    if not instances[service.value].isAlive():
        if cm.core.start_messaged_service:
            logger.info("Service: " + service.name + " was not already running. Starting it.")
            start_service(service)
        else:
            logger.info("Service: " + service.name + " is not started.")

    if instances[service.value].isAlive():
        instances[service.value].message(message)


def request_var(service: ServiceType, name):
    return instances[service.value].request(name) if instances[service.value].isAlive() else None
