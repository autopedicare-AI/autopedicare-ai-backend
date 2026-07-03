from enum import Enum


class MechanicStatus(str, Enum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    ON_THE_WAY = "on_the_way"
    ON_SERVICE = "on_service"
    BUSY = "busy"