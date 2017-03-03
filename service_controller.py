from enum import Enum


class Service(Enum):
    STATIC_LIGHT = 0
    LIGHTSHOWPI = 1
    MOPIDY = 2
    ALERT = 3

# This array stores the statuses of the four services
# The index of each service is defined by the above enum
# 0 - stopped, 1 - running
service_status = [0, 0, 0, 0]


def setup():
    pass


def start_service(service):
    pass


def stop_service(service):
    pass


def get_service_status(service):
    pass

