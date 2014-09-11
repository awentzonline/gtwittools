"""Use a separate process to render a graph."""
from gevent.monkey import patch_all; patch_all()

import time

import gevent
import gipc
import matplotlib.pyplot as plt
from gevent.queue import Queue
from gtwittools.gutils import echo_queue, spawn_worker
from gtwittools.tweetin import (
    extract_statuses, filter_twitter, get_twitter_api)

# sampler process

def sampler(buffer_q, gen, interval=0.01, flush_size=10):
    buffer = []
    while True:
        value = next(gen)
        buffer.append(value)
        if len(buffer) == flush_size:
            buffer_q.put(buffer)
            buffer = []
        gevent.sleep(interval)


counter = 0
last_t = time.time()

def sample_counter():
    global counter, last_t
    
    while True:
        t = time.time()
        dt = t - last_t
        last_t = t
        count = counter
        counter = 0
        if not dt:
            dt = 1.0
        yield count / dt


def count_phrases(phrase_q, phrase):
    global counter
    for text in phrase_q:
        counter += text.count(phrase)


def sampler_process(buffer_writer, fn, phrase='lol'):
    raw_status_q = Queue()
    status_q = Queue()
    twitter_api = get_twitter_api()
    spawn_worker([
        (sampler, buffer_writer, fn, 2, 10),
        (filter_twitter, twitter_api, status_q, [phrase]),
        (extract_statuses, status_q, raw_status_q),
        (count_phrases, raw_status_q, phrase),
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


def spawn_processes(confs):
    processes = []
    for conf in confs:
        p = gipc.start_process(target=conf[0], args=tuple(conf[1:]))
        processes.append(p)
    return processes


def main():
    buffer_reader, buffer_writer = gipc.pipe()

    processes = spawn_processes([
        (sampler_process, buffer_writer, sample_counter()),
        (renderer_process, buffer_reader,),
    ])
    while True:
        gevent.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
