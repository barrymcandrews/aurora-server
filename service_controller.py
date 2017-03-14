from enum import Enum

from log import setup_logger
from services.Service import Service
from services.StaticLightService import StaticLightService
from services.LightShowService import LightShowService
from services.AlertService import AlertService


class ServiceType(Enum):
    STATIC_LIGHT = 0
    LIGHTSHOW = 1
    ALERT = 2

classes = [StaticLightService, LightShowService, AlertService]
instances = [Service(), Service(), Service()]
logger = setup_logger('Service Controller')


def setup():
    """Starts services that should be running initially"""
    logger.info('Setting up services...')
    start_service(ServiceType.LIGHTSHOW)


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
        instances[service.value].join(timeout=5)
        message = " is not responding." if instances[service.value].isAlive() else " successfully stopped."
        logger.info(service.name + message)


def get_service_status(service: ServiceType) -> str:
    return 'started' if instances[service.value].isAlive() else 'stopped'


def send_message(service: ServiceType, message):
    instances[service.value].message(message)
