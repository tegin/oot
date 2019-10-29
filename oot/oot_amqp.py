import logging
import uuid
from multiprocessing import Process

from .connection.consumer import Consumer
from .oot_multiprocess import OotMultiProcessing

_logger = logging.getLogger(__name__)


class OotAmqp(OotMultiProcessing):
    consumer = False
    fields = {
        "amqp_host": {
            "name": "Host for AMQP",
            "placeHolder": "amqp://user:password@hostname:port",
            "required": False,
        },
        "amqp_name": {
            "name": "Unique name for this device on AMQP, if "
            "blank, name of initial generated name on odoo will be used",
            "required": False,
        },
        "amqp_check_key": {"name": "Key For System AMQP Calls", "required": False},
    }

    def get_default_amqp_options(self):
        return {
            "reboot": self.amqp_key_check(self.reboot),
            "ssh": self.amqp_key_check(self.toggle_service_function("ssh")),
        }

    def amqp_key_check(self, funct):
        def new_func(channel, basic_deliver, properties, body):
            if not self.amqp_check_key or self.amqp_check_key == body.decode("utf-8"):
                funct(
                    channel=channel,
                    basic_deliver=basic_deliver,
                    properties=properties,
                    body=body,
                )

        return new_func

    def generate_connection(self):
        super().generate_connection()
        amqp_host = self.connection_data.get("amqp_host", False)
        if amqp_host:
            amqp_options = self.connection_data.get("amqp_options", [])
            self.amqp_name = self.connection_data.get(
                "amqp_name", self.connection_data.get("name")
            )
            self.routing_base = "oot.%s" % self.amqp_name
            self.amqp_check_key = self.connection_data.get("amqp_check_key")
            amqp_options += self.get_default_amqp_options()
            self.consumer = Consumer(
                amqp_host,
                queue=str(uuid.uuid4()),
                routing_base=self.routing_base,
                options=amqp_options,
                function=self.on_message,
            )

    def on_message(self, channel, basic_deliver, properties, body):
        _logger.info(
            "Received message # %s from %s / %s: %s",
            basic_deliver.delivery_tag,
            basic_deliver.exchange,
            basic_deliver.routing_key,
            body.decode("utf-8"),
        )
        self._on_message(channel, basic_deliver, properties, body)
        channel.basic_ack(basic_deliver.delivery_tag)

    def _on_message(self, channel, basic_deliver, properties, body):
        options = self.get_default_amqp_options()
        for key in options:
            if basic_deliver.routing_key == "oot.{}.{}".format(self.amqp_name, key):
                options[key](
                    channel=channel,
                    basic_deliver=basic_deliver,
                    properties=properties,
                    body=body,
                )
                return True
        return False

    def _run(self, **kwargs):
        if self.consumer:
            process = Process(target=self.consumer.run)
            process.start()
            self.jobs.append(process)
        return super()._run(**kwargs)
