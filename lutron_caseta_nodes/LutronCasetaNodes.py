""" Node classes used by the Node Server. """
import polyinterface

import asyncio

LOGGER = polyinterface.LOGGER


class BaseNode(polyinterface.Node):
    def __init__(self,
                 controller,
                 primary,
                 address,
                 name,
                 sb,
                 type,
                 zone,
                 current_state):
        super().__init__(controller, primary, address, name)
        self.sb = sb
        self.name = name
        self.address = address
        self.type = type
        self.zone = zone
        self.current_state = current_state

    def send_command(self, device, value):
        LOGGER.info("Sending value to Smart Bridge for device {}: {}".format(device, value))
        if not self.sb.is_connected():
            LOGGER.info("Not connected to bridge, reconnecting...")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.sb.connect())
        result = self.sb.set_value(device, value)
        LOGGER.info("send_command result: {}".format(result))


class SerenaHoneycombShade(BaseNode):
    def setOpen(self, command):
        LOGGER.info("setOpen: command {}".format(command))
        self.send_command(command['address'], 100)
        self.setDriver('ST', 0)
        self.setDriver('OL', 100)

    def setClose(self, command):
        LOGGER.info("setClose: command {}".format(command))
        self.send_command(command['address'], 0)
        self.setDriver('ST', 100)
        self.setDriver('OL', 0)

    def setOpenLevel(self, command):
        LOGGER.info("setOpenLevel: command {}".format(command))
        if command.get('value'):
            ol = int(command['value'])
        else:
            ol = int(command.get('query', {}).get('OL.uom51'))
        self.send_command(command['address'], ol)
        if ol > 0:
            self.setDriver('ST', 0)
        else:
            self.setDriver('ST', 100)
        self.setDriver('OL', ol)

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 79},
        {'driver': 'OL', 'value': 0, 'uom': 51}
    ]
    id = 'serenashade'

    commands = {
        'DON': setOpen,
        'DOF': setClose,
        'OL': setOpenLevel,
    }
