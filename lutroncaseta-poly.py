#!/usr/bin/env python
"""
This is a NodeServer for Polyglot v2 written in Python3
by timekillerj (Jason Donahue) timekillerj@gmail.com
"""
import polyinterface

import sys

LOGGER = polyinterface.LOGGER

# Lutron Caseta Controller
from lutron_caseta_nodes import LutronCasetaController

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('LutronCaseta')

        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = LutronCasetaController(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
