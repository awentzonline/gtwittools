"""Use a separate process to render a graph."""
from gevent.monkey import patch_all; patch_all()

import time

import gevent
import gipc
import matplotlib.pyplot as plt
from gevent.queue import Queue
from gtwittools.gutils import echo_queue, sampler, spawn_worker, spawn_processes


# sampler process

def sampler_process(buffer_writer, fn):
    spawn_worker([
        (sampler, buffer_writer, fn, 0.1, 5.0),
    ])


# renderer process

def plotter(conf_q, rendered_q, output_dir='/tmp/'):
    import os
    import shutil
    import tempfile

    if not output_dir:
        output_dir = tempfile.mkdtemp()
    num_plots = 0
    for plot_conf in conf_q:
        filename = os.path.join(output_dir, '{}.png'.format(num_plots))
        render_plot(plot_conf, filename)
        num_plots += 1
        rendered_q.put(filename)
    shutil.rmtree(output_dir, ignore_errors=True)  # clean up those files!


def render_plot(plot_conf, filename='/tmp/test.png'):
    # TODO: learn matlabplot
    plt.clf()
    values = plot_conf.pop('values')
    plt.plot(values)
    for key, value in plot_conf:
        getattr(plt, key)(value)  # it's a bunch of callables?
    plt.savefig(filename)


def configure_plots(buffer_reader, plot_q):
    """Transform the sample buffer into some plotting commands."""
    while True:
        values = buffer_reader.get()
        conf = dict(
            values=values
        )
        plot_q.put(conf)


def renderer_process(buffer_reader, output_dir='/tmp/'):
    plot_q = Queue()
    rendered_q = Queue()
    spawn_worker([
        (configure_plots, buffer_reader, plot_q),
        (plotter, plot_q, rendered_q, output_dir),
        (echo_queue, rendered_q),
    ])


# utils

def gen_t(f, scale=1.0, initial_t=0.0):
    t = initial_t
    last_t = None
    while True:
        if last_t is None:
            last_t = time.time()
        now = time.time()
        t += scale * (last_t - now)
        last_t = now
        yield f(t)


def main():
    import math
    sin = gen_t(math.sin, scale=5.0)

    buffer_reader, buffer_writer = gipc.pipe()
    processes = spawn_processes([
        (sampler_process, buffer_writer, sin),
        (renderer_process, buffer_reader,),
    ])
    while True:
        gevent.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

