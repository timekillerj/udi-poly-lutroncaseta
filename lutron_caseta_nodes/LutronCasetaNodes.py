""" Node classes used by the Node Server. """
import polyinterface

LOGGER = polyinterface.LOGGER


class SerenaHoneycombShade(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sb, type, zone, current_state):
        super().__init__(controller, primary, address, name)
        self.sb = sb
        self.name = name
        self.address = address
        self.type = type
        self.zone = zone
        self.current_state = current_state

    def setOpen(self, command):
        LOGGER.info("setOpen: command {}".format(command))
        self.sb.set_value(command['address'], 100)
        self.setDriver('ST', 100)

    def setClose(self, command):
        LOGGER.info("setClose: command {}".format(command))
        self.sb.set_value(command['address'], 0)
        self.setDriver('ST', 0)

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 51},
    ]
    id = 'serenashade'

    commands = {
        'DON': setOpen,
        'DOF': setClose,
    }
