import logging
import subprocess
import uuid
from multiprocessing import Process

from .connection.consumer import Consumer
from .oot_multiprocess import OotMultiProcessing

_logger = logging.getLogger(__name__)


class OotAmqp(OotMultiProcessing):
    consumer = False

    def get_default_amqp_options(self):
        return ["reboot", "ssh"]

    def generate_connection(self):
        super().generate_connection()
        amqp_host = self.connection_data.get("amqp_host", False)
        if amqp_host:
            amqp_options = self.connection_data.get("amqp_options", [])
            self.routing_base = "oot.%s" % self.connection_data.get("name")
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

    def toggle_service(self, service):
        stat = subprocess.Popen(
            "systemctl is-active --quiet %s; echo $?" % service,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        ).communicate()
        _logger.info(stat)
        if stat[0] == b"0\n":
            subprocess.Popen(["systemctl", "stop", service])
            subprocess.Popen(["systemctl", "disable", service])
        else:
            subprocess.Popen(["systemctl", "enable", service])
            subprocess.Popen(["systemctl", "start", service])

    def _on_message(self, channel, basic_deliver, properties, body):
        if basic_deliver.routing_key == "oot.%s.reboot" % self.connection_data.get(
            "name"
        ):
            subprocess.Popen(["reboot"])
            return
        if basic_deliver.routing_key == "oot.%s.ssh" % self.connection_data.get("name"):
            self.toggle_service("ssh")
            return
        else:
            self.queue.put(body.decode("utf-8"))

    def _run(self, **kwargs):
        if self.consumer:
            process = Process(target=self.consumer.run)
            process.start()
            self.jobs.append(process)
        return super()._run(**kwargs)
