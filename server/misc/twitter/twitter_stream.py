# Requires tweepy (pip install tweepy)
from tweepy import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from datetime import datetime
import os
import sys
import time
import json
import atexit
import pymongo

from libs.carmen import get_resolver

# A configuration is required for authentication purposes or else
# streaming service won't work.
minerva_twitter_config = json.load(open(
    os.path.join(os.path.dirname(__file__), "twitter.json")
))

# TODO why a different format between streaming and search apis?
dateformat = '%a %b %d %H:%M:%S %Y'

def datestring_to_epoch(datestring):
    d = datestring
    if not isinstance(d, datetime):
        # TODO yuck, clean up date handling generally
        # strip off tzoffset
        parts = datestring.split()
        parseableParts = parts[0:-2]
        parseableParts.append(parts[-1])
        datestring = ' '.join(parseableParts)
        d = datetime.strptime(datestring, dateformat)
    epoch = int((d - datetime(1970, 1, 1)).total_seconds())
    return epoch


class TwitterStreamListener(StreamListener):
    """ A listener handles tweets are the received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    def __init__(self, query):
        """Initialize twitter stream"""
        StreamListener.__init__(self)
        self._mongo = pymongo.MongoClient().minerva[query]
        self._filters = []

    def add_filter(self, filter):
        """A filter takes JSON  as input and outputs a JSON as well"""
        if filter not in self._filters:
            self._filters.append(filter)

    def on_data(self, data):
        """Receive tweet and save it to the database"""
        json_data = json.loads(data)

        for filter in self._filters:
            json_data = filter(json_data)

        retweet_cont = 0
        if 'retweet_cont' in json_data.keys():
            retweet_cont = json_data['retweet_cont']

        if 'location' in json_data:
            rec = {
                "id": json_data['id_str'],
                "location": json_data['location'],
                "text": json_data['text'],
                "timestamp_ms": json_data['timestamp_ms'],
                "created_at": datestring_to_epoch(json_data['created_at']),
                "retweeted": json_data['retweeted'],
                "retweet_cont": retweet_cont
            }

            print(rec)

            # Insert data in mongodb
            self._mongo.insert(rec)

        return True

    def on_error(self, status):
        """Handle any error encountered during streaming"""
        print(status)

    def on_timeout(self):
        sys.stderr.write("Timeout, sleeping for 60 seconds...\n")
        time.sleep(60)
        return

_exit = False


def exitHandler():
    global _exit
    _exit = True

atexit.register(exitHandler)


def createTweetGeocoder():
    resolver = get_resolver()
    resolver.load_locations()

    def tweetGeocoder(tweet):
        location = resolver.resolve_tweet(tweet)
        if location is not None:
            tweet["location"] = location[1].__dict__
        return tweet

    return tweetGeocoder


def stream(query):
    listn = TwitterStreamListener(query)
    listn.add_filter(createTweetGeocoder())

    auth = OAuthHandler(minerva_twitter_config["twitter"]["CONSUMER_KEY"],
                        minerva_twitter_config["twitter"]["CONSUMER_SECRET"])
    auth.set_access_token(minerva_twitter_config["twitter"]["ACCESS_KEY"],
                          minerva_twitter_config["twitter"]["ACCESS_SECRET"])
    stream = Stream(auth, listn)
    stream.filter(track=[query], async=False)

if __name__ == '__main__':
    stream(sys.argv[1])

