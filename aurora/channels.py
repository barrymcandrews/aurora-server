
class Channel(object):
    def __init__(self, d):
        self.pin: int = None
        self.label: str = None
        self.device: str = None
        self.__dict__ = d

    def __eq__(self, other):
        return self.pin == other.pin \
               and self.label == other.label \
               and self.device == other.device

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.pin, self.label, self.device))
