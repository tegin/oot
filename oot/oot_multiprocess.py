import time
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as QueueClass

from .oot import Oot


class OotMultiProcessing(Oot):
    functions = []
    queue = Queue()
    jobs = []

    def get_data(self, **kwargs):
        while True:
            value = self.queue.get()
            if value:
                return value
            time.sleep(0.1)

    def start_execute_function(self, function, *args, queue=False, **kwargs):
        pass

    def execute_function(self, function, *args, queue=False, **kwargs):
        if not isinstance(queue, QueueClass):
            raise Exception("A queue is required")
        self.start_execute_function(function, *args, queue=False, **kwargs)
        while True:
            value = function(*args, **kwargs)
            if value:
                queue.put(value)

    def run(self, **kwargs):
        for function in self.functions:
            process = Process(
                target=self.execute_function,
                args=function,
                kwargs={"queue": self.queue},
            )
            process.start()
            self.jobs.append(process)
        return super().run(**kwargs)
