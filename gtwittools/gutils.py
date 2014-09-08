import gevent
from gevent.pool import Group


def fanout(in_q, out_qs):
    for item in in_q:
        for q in out_qs:
            q.put(item)


def echo_queue(q):
    for item in q:
        print item


def spawn_worker(conf):
    """Some sugar to wrap up all of your greenlets."""
    group = Group()
    for args in conf:
        group.spawn(*args)
    try:
        while True:
            gevent.sleep(1)
    except KeyboardInterrupt:
        pass
