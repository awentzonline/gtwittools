import time

import gevent
import gipc
from gevent.pool import Group


def fanout(in_q, out_qs):
    for item in in_q:
        for q in out_qs:
            q.put(item)


def echo_queue(q):
    for item in q:
        print item


def sampler(buffer_q, gen, interval=0.1, flush_interval=10.0):
    """Periodically poll an iterable and occasionally flush the samples."""
    buffer = []
    last_flush = time.time()
    while True:
        value = next(gen)
        buffer.append(value)
        now = time.time()
        if (now - last_flush >= flush_interval):
            buffer_q.put(buffer)
            buffer = []
            last_flush = now
        gevent.sleep(interval)


def spawn_greenlets(conf):
    """Some sugar to wrap up all of your greenlets."""
    group = Group()
    for args in conf:
        group.spawn(*args)
    try:
        while True:
            gevent.sleep(1)
    except KeyboardInterrupt:
        pass


def spawn_processes(confs):
    """Spawn subprocesses with a config similar to spawn_worker."""
    processes = []
    for conf in confs:
        p = gipc.start_process(target=conf[0], args=tuple(conf[1:]))
        processes.append(p)
    return processes
