#!/usr/bin/env python
"""
This is a NodeServer for Polyglot v2 written in Python3
by timekillerj (Jason Donahue) timekillerj@gmail.com
"""
import polyinterface

import sys

from lutron_caseta_nodes.LutronCasetaController import LutronCasetaController

LOGGER = polyinterface.LOGGER

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('LutronCaseta')
        """
        Start MQTT and connects to Polyglot.
        """
        polyglot.start()
        """
        Create the Controller Node and pass in the Interface
        """
        control = LutronCasetaController(polyglot)
        """
        Sit around and do nothing forever.
        """
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
