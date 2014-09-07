import os

import twitter


def get_twitter_api():
    api = twitter.Api(   
        consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
        consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
        access_token_key=os.environ['TWITTER_OAUTH_KEY'],
        access_token_secret=os.environ['TWITTER_OAUTH_SECRET']
    )
    return api


def sample_twitter(api, out_q):
    for item in api.GetStreamSample():
        out_q.put(item)


def filter_twitter(api, out_q, track=None, follow=None):
    for item in api.GetStreamFilter(track=track, follow=follow):
        out_q.put(item)
      

def post_to_twitter(api, status_q):
    for item in status_q:
        api.PostUpdate(item)


def extract_statuses(in_q, out_q):
    for item in in_q:
        out_q.put(item['text'])


def echo_statuses(in_q):
    for item in in_q:
        print u'{}: {}'.format(
            item['user']['name'],
            item['text']
        )
