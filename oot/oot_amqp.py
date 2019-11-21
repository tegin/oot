import json
import logging
import uuid
from inspect import getmembers
from multiprocessing import Process

import pika
import psutil

from . import api
from .connection.consumer import Consumer
from .fields import Field
from .oot_multiprocess import OotMultiProcessing

_logger = logging.getLogger(__name__)


class OotAmqp(OotMultiProcessing):
    consumer = False
    amqp_host = Field(
        name="Host for AMQP",
        placeholder="amqp://user:password@hostname:port",
        required=False,
        sequence=100,
    )
    amqp_name = Field(
        name="Unique name for this device on AMQP, if "
        "blank, name of initial generated name on odoo will be used",
        required=False,
        sequence=102,
    )
    amqp_check_key = Field(
        name="Key For System AMQP Calls", required=False, sequence=101
    )

    def amqp_machine_stats(self, **kwargs):
        return {
            "cpu_percentage": psutil.cpu_percent(),
            "virtual_memory_percentage": psutil.virtual_memory().percent,
            "temp": psutil.sensors_temperatures()["cpu-thermal"][0].current,
        }

    @api.amqp("reboot")
    def amqp_reboot(self, channel, basic_deliver, properties, body):
        if body.decode("utf-8") == self.amqp_check_key:
            return self.reboot()

    @api.amqp("ssh")
    def amq_ssh(self, channel, basic_deliver, properties, body):
        if body.decode("utf-8") == self.amqp_check_key:
            return self.toggle_service_function("ssh")()

    @api.amqp("stats")
    def amqp_stats(self, channel, basic_deliver, properties, body):
        if body.decode("utf-8") == self.amqp_check_key:
            return self.amqp_machine_stats()

    def get_default_amqp_options(self):
        result = {}

        def is_command(func):
            return callable(func) and hasattr(func, "_amqp_command")

        cls = type(self)
        for _attr, func in getmembers(cls, is_command):
            result[func._amqp_command] = self.get_callback_function(func)
        return result

    def amqp_key_check(self, funct, key=False):
        if not key:
            key = self.amqp_check_key

        def new_func(channel, basic_deliver, properties, body):
            if not key or key == body.decode("utf-8"):
                return funct(
                    channel=channel,
                    basic_deliver=basic_deliver,
                    properties=properties,
                    body=body,
                )
            return False

        return new_func

    def generate_connection(self):
        super().generate_connection()
        amqp_host = self.amqp_host
        if amqp_host:
            amqp_options = []
            self.amqp_name = self.amqp_name or self.name
            self.routing_base = "oot.%s" % self.amqp_name
            self.amqp_check_key = self.amqp_check_key
            amqp_options += self.get_default_amqp_options()
            self.consumer = Consumer(
                amqp_host,
                queue=str(uuid.uuid4()),
                routing_base=self.routing_base,
                options=amqp_options,
                function=self.on_message,
            )

    def parse_amqp_data(self, data):
        if isinstance(data, dict):
            return json.dumps(data)
        return str(data)

    def on_message(self, channel, basic_deliver, properties, body):
        _logger.info(
            "Received message # %s from %s / %s: %s",
            basic_deliver.delivery_tag,
            basic_deliver.exchange,
            basic_deliver.routing_key,
            body.decode("utf-8"),
        )
        data = self._on_message(channel, basic_deliver, properties, body)
        if properties.correlation_id and properties.reply_to and data:
            response = self.parse_amqp_data(data)
            _logger.info(
                "Responding the message # %s with response: %s"
                % (basic_deliver.delivery_tag, response)
            )
            channel.basic_publish(
                exchange="",
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id
                ),
                body=response,
            )
        channel.basic_ack(basic_deliver.delivery_tag)

    def _on_message(self, channel, basic_deliver, properties, body):
        options = self.get_default_amqp_options()
        for key in options:
            if basic_deliver.routing_key == "oot.{}.{}".format(self.amqp_name, key):
                return options[key](
                    channel=channel,
                    basic_deliver=basic_deliver,
                    properties=properties,
                    body=body,
                )
        return False

    def _run(self, **kwargs):
        if self.consumer:
            process = Process(target=self.consumer.run)
            process.start()
            self.jobs.append(process)
        return super()._run(**kwargs)
