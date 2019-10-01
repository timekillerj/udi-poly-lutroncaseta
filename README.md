# LutronCaseta Node Server

This is the LutronCaseta Poly for the [Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2).

This node server is intended to allow controlling Lutron devices through a Caseta Smart Bridge. Currently only Serena honeycomb shades are supported, but development is ongoing.

#### Configuration

Once the node server is installed in you polyglot instance you must add 2 custom parameters: `lutron_bridge_ip` and `oauth_code`. Thekeys for these params should be auto created when the node server is fully started.

The `lutron_bridge_ip` is the IP Address of your Caseta Smart Bridge. It is highly recommended you set a static IP for your smart bridge.

The `oauth_code` can be obtained by following the link generated on the Configuration page of the node server.

Once the IP and OAUTH code are saved, restart the node server to apply the changes.

The node server will then connect to your smart bridge and create nodes in the ISY994i for each of your Lutron devices.
