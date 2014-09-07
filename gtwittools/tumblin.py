import os

import pytumblr


def get_tumblr_client():
    consumer_key = os.environ.get('TUMBLR_CONSUMER_KEY', None)
    consumer_secret = os.environ.get('TUMBLR_CONSUMER_SECRET', None)
    oauth_token = os.environ.get('TUMBLR_OAUTH_TOKEN', None)
    oauth_secret = os.environ.get('TUMBLR_OAUTH_SECRET', None)
    blog_name = os.environ.get('TUMBLR_BLOG_NAME', None)
    assert consumer_key and consumer_secret and \
        oauth_token and oauth_secret and blog_name

    client = pytumblr.TumblrRestClient(
        consumer_key, consumer_secret, oauth_token, oauth_secret
    )
