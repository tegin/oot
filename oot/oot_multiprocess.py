import time
from inspect import getmembers
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

    def get_callback_function(self, function):
        def callback(*args, **kwargs):
            return function(self, *args, **kwargs)

        return callback

    def _get_functions(self):
        def is_command(func):
            return callable(func) and hasattr(func, "_oot_process")

        functions = []
        cls = type(self)
        for _attr, func in getmembers(cls, is_command):
            functions.append([self.get_callback_function(func)])
        return self.functions + functions

    def _run(self, **kwargs):
        for function in self._get_functions():
            process = Process(
                target=self.execute_function,
                args=function,
                kwargs={"queue": self.queue},
            )
            process.start()
            self.jobs.append(process)
        return super()._run(**kwargs)
