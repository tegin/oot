====================
Oot - Odoo of things
====================

The main goal of this package is to provide the necessary tools to configure a device
that will send information to odoo.

Device
------

A device is a processing unit that capable to send information to odoo.
All devices must be registered on odoo.
In order to send the data, it will use and HTTP Protocol.

Create your first device
------------------------

Oot class
~~~~~~~~~

First we define a class for the Oot to manage it configuration.
For example:

.. code-block:: python

    from oot import OotAmqp, api, Field
    from oot.device import CardReader
    import time


    class DemoOot(OotAmqp):
        """We are using AMQP as it allows to define some extra configuration"""
        template = "demo_template"
        # Template to be used on odoo
        oot_input = "demo_input"
        # Input to be used on odoo

        # Now we define the configuration fields
        admin_id = Field(name="Admin key", required=True)
        reader = CardReader(spd=10000)

        @api.oot
        def get_data_mfrc522(self, **kwargs):
            """We will return the card if a card is readed. Otherwise, we will wait"""
            time.sleep(5.0)
            while True:
                uid = self.reader.scan_card()
                if uid:
                    return uid

Launcher
~~~~~~~~

The second part will be defining a launcher.
The launcher is usually a folder that will contain:

* main file to execute
* a config for the logging
* a `log` folder that will store logs
* a `data` folder that will contain the configuration file

We will try to make an example:

.. code-block:: python

    import os
    import logging.config
    from ootdemo import DemoOot

    path = os.path.dirname(os.path.realpath(__file__))

    log_folder = path + "/log"

    if not os.path.isdir(log_folder):
        os.mkdir(log_folder)

    logging.config.fileConfig(path + "/ras.logging.conf")

    data_folder = path + "/data"

    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)

    DemoOot(data_folder + "/data.json").run()


The example provided on this file will only work on a Raspberry PI with an MFRC522.
