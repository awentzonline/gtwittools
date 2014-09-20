"""Use a separate process to perform cpu heavy tasks."""
from gevent.monkey import patch_all; patch_all()

import hashlib
import os
from StringIO import StringIO

import gevent
import gipc
import requests
from gevent.queue import Queue
from gtwittools.gutils import (
    echo_queue, spawn_greenlets, spawn_processes, fanout)
from gtwittools.tweetin import (
    echo_statuses, extract_statuses, filter_twitter, get_twitter_api)
from PIL import Image


def q_to_pipe(q, pipe):
    for item in q:
        pipe.put(item)


def pipe_to_q(pipe, q):
    while True:
        q.put(pipe.get())


# gather image urls from twitter

def twitter_process(url_writer, filter_phrases=[]):
    url_q = Queue()
    image_status_q = Queue()
    twitter_api = get_twitter_api()
    spawn_greenlets([
        (filter_twitter, twitter_api, image_status_q, filter_phrases),
        (extract_status_images, image_status_q, url_q),
        (q_to_pipe, url_q, url_writer)
    ])


def extract_status_files(status_q, url_q, file_exts=[], max_size_mb=2.0):
    for status in status_q:
        for entity in status.get('entities', {}).get('urls', []):
            if 'expanded_url' in entity:
                this_url = entity['expanded_url']
                if file_exts:
                    _, ext = os.path.splitext(this_url)
                    if ext in file_exts:
                        url_q.put(this_url)
                else:
                    url_q.put(this_url)


def extract_status_images(status_q, url_q):
    extract_status_files(status_q, url_q, file_exts=[
        '.jpg', '.jpeg', '.png'
    ])


# download the images and process them with opencv

def fetch_image_url(url_q, filename_q, storage_path='/tmp/', interval=1.0, max_size_mb=1.0):
    """Download a url, make sure it's an image."""
    try:
        os.makedirs(storage_path)
    except OSError:
        pass  # already exists
    max_bytes = max_size_mb * 1024 * 1024
    for url in url_q:
        url_hash = hashlib.sha1(url).hexdigest()
        filename = os.path.join(storage_path, url_hash + '.jpg')  # jpg for now?
        #print('checking {} {}'.format(url, filename))
        # maybe we've already downloaded it?
        if os.path.exists(filename):
            filename_q.put(filename)
            continue
        # make sure it's not too large
        head_req = requests.head(url)
        content_length = int(head_req.headers.get('content-length', max_bytes + 1))
        #print('head len={}'.format(content_length))
        if content_length is None:
            continue
        if content_length > max_bytes:
            #print('content too long')
            continue
        # download that image and check it out
        try:
            req = requests.get(url)
            img = Image.open(StringIO(req.content))
            #print('saving {} {}'.format(url, filename))
            img.save(filename)
        except:
            print('error fetching {}'.format(url))
        else:
            filename_q.put(filename)
        gevent.sleep(interval)


def image_fetch_process(url_reader, filename_writer, output_dir='/tmp/gtwitcv/'):
    url_q = Queue()
    rendered_q = Queue()
    filename_q = Queue()
    fetch_tmp_dir = '/tmp/gtwitimg/'
    spawn_greenlets([
        (pipe_to_q, url_reader, url_q),
        (fetch_image_url, url_q, filename_q, fetch_tmp_dir),
        (q_to_pipe, filename_q, filename_writer),
    ])


def detector_process(filename_reader):
    from detector import detect_in_files, eye_classifier, face_classifier
    # callback for when features are detected
    out_dir = '/tmp/detected/'
    try:
        os.makedirs(out_dir)
    except OSError:
        pass
    def echo_features(img, features, filename):
        import cv2
        if all(map(len, features.values())):
            for rects in features.values():
                for rect in rects:
                    cv2.rectangle(
                        img,
                        (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]),
                        (0,0,0)
                    )
            outfilename = os.path.split(filename)[1]
            cv2.imwrite(os.path.join(out_dir, outfilename), img)
            print('detected: {} {}'.format(filename, features))

    classifiers = dict(
        face=face_classifier,
        eye=eye_classifier
    )
    filename_q = Queue()
    spawn_greenlets([
        (pipe_to_q, filename_reader, filename_q),
        (detect_in_files, echo_features, filename_q, classifiers),
    ])


def main():
    filename_reader, filename_writer = gipc.pipe()
    url_reader, url_writer = gipc.pipe()
    filter_phrases = ['lol', 'haha', 'wow', 'incredible']
    #filter_phrases = []
    filter_phrases += ['jpg', 'jpeg']
    processes = spawn_processes([
        (twitter_process, url_writer, filter_phrases),
        (image_fetch_process, url_reader, filename_writer),
        (detector_process, filename_reader),
    ])
    while True:
        gevent.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
