import logging

import pika

_logger = logging.getLogger(__name__)


class Consumer(object):
    def __init__(
        self,
        amqp_url,
        routing_base="",
        queue=False,
        options=False,
        function=False,
        exchange_name="oot",
        exchange_type="topic",
    ):
        self.queue = queue
        self.options = options or {}
        self._url = amqp_url
        self.function = function or self.on_message
        self.exchange_type = exchange_type
        self.exchange_name = exchange_name
        self.routing_base = routing_base
        self.queue_options = {"exclusive": False, "auto_delete": True}

    def on_message(self, channel, basic_deliver, properties, body):
        _logger.info(
            "Received message # %s from %s / %s: %s",
            basic_deliver.delivery_tag,
            basic_deliver.exchange,
            basic_deliver.routing_key,
            body,
        )
        channel.basic_ack(basic_deliver.delivery_tag)

    def run(self):
        while True:
            try:
                _logger.info("Connecting amqp")
                connection = pika.BlockingConnection(pika.URLParameters(self._url))
                channel = connection.channel()
                channel.basic_qos(prefetch_count=1)
                channel.queue_declare(self.queue, **self.queue_options)
                channel.exchange_declare(
                    exchange=self.exchange_name,
                    exchange_type=self.exchange_type,
                    passive=True,
                )
                for routing_key in self.options:
                    channel.queue_bind(
                        self.queue,
                        self.exchange_name,
                        routing_key="{}.{}".format(self.routing_base, routing_key),
                    )
                channel.basic_consume(self.queue, self.function)
                try:
                    channel.start_consuming()
                except KeyboardInterrupt:
                    channel.stop_consuming()
                    connection.close()
                    break
            except pika.exceptions.ConnectionClosedByBroker:
                continue
            # Do not recover on channel errors
            except pika.exceptions.AMQPChannelError as err:
                _logger.info("Caught a channel error: {}, stopping...".format(err))
                break
            # Recover on all other connection errors
            except pika.exceptions.AMQPConnectionError:
                _logger.info("Connection was closed, retrying...")
                continue
