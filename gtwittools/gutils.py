import sys
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
    """Spawn subprocesses with a config similar to spawn_greenlets."""
    processes = []
    for conf in confs:
        p = gipc.start_process(target=conf[0], args=tuple(conf[1:]))
        processes.append(p)
    return processes


def never_surrender(fn):
    """Re-invoke a function if it dies from an exception."""
    def wrapped(*args, **kwargs):
        while True:
            try:
                fn(*args, **kwargs)
            except KeyboardInterrupt:
                break
            except:
                print('Error:{}'.format(sys.exc_info()[0]))
    return wrapped


def gen_t(f, scale=1.0, initial_t=0.0):
    """Turn a f of t into a generator based on wall clock."""
    t = initial_t
    last_t = None
    while True:
        if last_t is None:
            last_t = time.time()
        now = time.time()
        t += scale * (last_t - now)
        last_t = now
        yield f(t)
