"""Example which echos all tweets that contain 'lol'"""
from gevent.monkey import patch_all; patch_all()

import gevent
from gevent.queue import Queue

from gtwittools.gutils import spawn_greenlets
from gtwittools.tweetin import echo_statuses, filter_twitter, get_twitter_api


def main():
    incoming_tweets_q = Queue()
    twitter_api = get_twitter_api()
    conf = [
        (filter_twitter, twitter_api, incoming_tweets_q, ['lol']),
        (echo_statuses, incoming_tweets_q),
    ]
    spawn_greenlets(conf)


if __name__ == '__main__':
    main()
