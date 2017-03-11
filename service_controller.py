import logging
import sys
from enum import Enum

from log import setup_logger
from services.StaticLightService import StaticLightService
from services.LightshowPiService import LightshowPiService
from services.MopidyService import MopidyService
from services.AlertService import AlertService


class ServiceType(Enum):
    STATIC_LIGHT = 0
    LIGHTSHOWPI = 1
    MOPIDY = 2
    ALERT = 3

classes = [StaticLightService, LightshowPiService, MopidyService, AlertService]
instances = [StaticLightService(), LightshowPiService(), MopidyService(), AlertService()]
logger = setup_logger('Service Controller')


def setup():
    """Starts services that should be running initially"""
    logger.info('Setting up services...')
    start_service(ServiceType.STATIC_LIGHT)
    start_service(ServiceType.ALERT)


def start_service(service: ServiceType):
    logger.info("Starting service " + service.name + "...")
    instances[service.value] = classes[service.value]()
    instances[service.value].start()


def stop_service(service: ServiceType):
    logger.info("Stopping service " + service.name + "...")
    instances[service.value].stop()
    instances[service.value].join(timeout=5)
    message = " is not responding." if instances[service.value].isAlive() else " successfully stopped."
    logger.info(service.name + message)


def get_service_status(service: ServiceType) -> str:
    return 'started' if instances[service.value].isAlive() else 'stopped'


def send_message(service: ServiceType, message):
    instances[service.value].message(message)
