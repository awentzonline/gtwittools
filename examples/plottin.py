"""Use a separate process to render a graph."""
from gevent.monkey import patch_all; patch_all()

import time

import gevent
import matplotlib.pyplot as plt
from gevent.queue import Queue
from gtwittools.gutils import echo_queue, spawn_worker


def sampler(buffer_q, fn, interval=0.01, flush_size=100):
    buffer = []
    while True:
        value = fn()
        buffer.append(value)
        if len(buffer) == flush_size:
            buffer_q.put(buffer)
            buffer = []
        gevent.sleep(interval)


def plotter(conf_q, rendered_q):
    import os
    import shutil
    import tempfile

    temp_dir = '/tmp/' # tempfile.mkdtemp()
    num_plots = 0
    for plot_conf in conf_q:
        filename = os.path.join(temp_dir, '{}.png'.format(num_plots))
        render_plot(plot_conf, filename)
        num_plots += 1
        rendered_q.put(filename)
    shutil.rmtree(temp_dir, ignore_errors=True)  # clean up those files!


def render_plot(plot_conf, filename='/tmp/test.png'):
    values = plot_conf.pop('values')
    plt.plot(values)
    for key, value in plot_conf:
        getattr(plt, key)(value)  # it's a bunch of callables?
    plt.savefig(filename)


def sample_plotter(buffer_q, plot_q, rendered_q):
    for values in buffer_q:
        conf = dict(
            values=values
        )
        plot_q.put(conf)


class TWrap(object):
    """Wrap a function with a timer"""
    def __init__(self, f, scale=1.0, offset=0.0):
        self.f = f
        self.t = offset
        self.last_t = None
        self.scale = scale

    def __call__(self):
        if self.last_t is None:
            self.last_t = time.time()
        now = time.time()
        self.t += self.scale * (self.last_t - now)
        self.last_t = now
        return self.f(self.t)


def main():
    import math

    buffer_q = Queue()
    plot_q = Queue()
    rendered_q = Queue()
    sin = TWrap(math.sin, scale=5.0)
    conf = [
        (sampler, buffer_q, sin),
        (sample_plotter, buffer_q, plot_q, rendered_q),
        (plotter, plot_q, rendered_q),
        (echo_queue, rendered_q),
    ]
    spawn_worker(conf)


if __name__ == '__main__':
    main()
