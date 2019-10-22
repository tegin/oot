import uuid
from multiprocessing import Process

from oot import OotMultiProcessing

from .consumer import ReconnectingConsumer


class AmqpOot(OotMultiProcessing):
    def __init__(self, connection):
        super().__init__(connection)
        self.consumer = ReconnectingConsumer(
            "amqp://test:test@192.168.1.68",
            queue=str(uuid.uuid4()),
            options=[
                ("message", "topic", "example.text"),
                ("message2", "topic", "example2.text"),
            ],
        )

    def run(self, **kwargs):
        process = Process(target=self.consumer.run)
        process.start()
        self.jobs.append(process)
        return super().run(**kwargs)
