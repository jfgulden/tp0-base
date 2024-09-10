
from multiprocessing import Value, Lock, Condition

import logging

class SyncBarrier:
    def __init__(self, total_count):
        self.counter = Value('i', 0)  
        self.total_count = total_count  
        self.condition = Condition()

    def wait_for_all(self):
        with self.condition:
            self.counter.value += 1
            if self.counter.value == self.total_count:
                self.condition.notify_all()
            else:
                self.condition.wait()
