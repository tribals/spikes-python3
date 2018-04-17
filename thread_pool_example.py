#!/usr/bin/env python3

import argparse
import signal
import sys
import threading
import time
from queue import Queue


sentinel = object() # guaranteed to be unique


def watcher(queue, event):
    # it is a producer of data
    print('starting watcher')

    while True:
        if event.is_set():
            break
        # do actual work
        queue.put(object())
        time.sleep(3)

    print('stopping watcher')


def worker(queue, n):
    # it is a consumer of data
    print(f'starting worker {n}')

    while True:
        task = queue.get()

        if task is sentinel:
            queue.put(sentinel)
            break

        # actually process a task
        print(f'worker {n} got: {task}')
        queue.task_done()

    print(f'stopping worker {n}')


def failer(seconds):
    print('starting failer')
    # wait for a while, then
    # raise an uncaught exception in thread
    time.sleep(seconds)
    raise RuntimeError


def monitor(event):
    print('starting monitor')
    while True:
        if event.is_set():
            break

        print(f'running threads: {threading.active_count()}')
        time.sleep(3)

    print('stopping monitor')


class Service(object):
    def __init__(self, nthreads, timeout):
        self._nthreads = nthreads
        self._timeout = timeout
        self._queue = Queue()
        self._event = threading.Event()
        self._threads = set()

    def _run(self, th):
        th.start()
        self._threads.add(th)

    def start(self):
        self._run(threading.Thread(target=watcher, args=(self._queue, self._event), name='Watcher'))

        for n in range(self._nthreads):
            self._run(threading.Thread(target=worker, args=(self._queue, n), name=f'Worker-{n}'))

        self._run(threading.Thread(target=failer, args=(self._timeout,), name='Failer'))
        self._run(threading.Thread(target=monitor, args=(self._event,), name='Monitor'))

    def stop(self):
        # stop watcher
        self._event.set()
        # stop workers and monitor
        self._queue.put(sentinel)

        for th in self._threads:
            th.join()
            print(f'thread {repr(th.name)} was successfully joined')

    def sigint(self, signo, frame):
        self.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--threads', default=3, type=int, help='number of threads to run', metavar='N')
    parser.add_argument('-t', '--timeout', default=10, type=int, help='interval after which "failer" should fail', metavar='T')

    args = parser.parse_args()

    svc = Service(args.threads, args.timeout)
    signal.signal(signal.SIGINT, svc.sigint)

    print("Let's roll! Hit ^C to exit.")
    svc.start()

if __name__ == '__main__':
    main()
