"""
Copyright (c) 2012 Casey Dunham <casey.dunham@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = 'Pat Hawks <pat@pathawks.com>'
__version__ = '0.2'

import argparse
import cgi
import codecs
import datetime
import sys
import time
import urllib

from urllib2 import (Request, urlopen, HTTPError, URLError)

try:
    # Python >= 2.6
    import json
except ImportError:
    try:
        # Python < 2.6
        import simplejson as json
    except ImportError:
        try:
            # Google App Engine
            from django.utils import simplejson as json
        except ImportError:
            raise ImportError, "Unable to load a json library"


class TweetDumpError(Exception):

    @property
    def message(self):
        return self.args[0]

class RateLimitError(TweetDumpError):
    pass

BASE_API_URL = "https://api.twitter.com/1/"
API_URL  = BASE_API_URL + "statuses/user_timeline.json?%s"
PIC_URL = BASE_API_URL + "users/profile_image/{screen_name}.png?size={size}"
USER_URL = BASE_API_URL + "users/show.json?%s"

# we are not authenticating so this will return the rate limit based on our IP
# see (https://dev.twitter.com/docs/api/1/get/account/rate_limit_status)
RATE_LIMIT_API_URL = BASE_API_URL + "account/rate_limit_status.json"

parser = argparse.ArgumentParser(description="dump all tweets from user")
parser.add_argument("handle", type=str, help="twitter screen name")


def get_user( screen_name ):
    params = {
        "screen_name": screen_name
    }

    encoded_params = urllib.urlencode( params )
    query = USER_URL % encoded_params
    resp = fetch_url(query)
    twitter_user = json.loads(resp.read())
    return twitter_user

def base64_image( image_url ):
    return "data:image/png;base64," + urllib.urlopen( image_url ).read().encode( "base64" ).replace( "\n", '' ).replace( "\r", '' )

def get_user_profile_pic( screen_name, size ):
    query = PIC_URL.format( screen_name=screen_name, size=size )
    return base64_image( query )

def get_tweets(screen_name, count, maxid=None):
    params = {
        "screen_name": screen_name,
        "count": count,
        "exclude_replies": "true",
        "include_rts": "true",
        "include_entities": "true"
    }

    # if we include the max_id from the last tweet we retrieved, we will retrieve the same tweet again
    # so decrement it by one to not retrieve duplicate tweets
    if maxid:
        params["max_id"] = int(maxid) - 1

    encoded_params = urllib.urlencode(params)
    query = API_URL % encoded_params
    resp = fetch_url(query)

    ratelimit_limit = resp.headers["X-RateLimit-Limit"]
    ratelimit_remaining = resp.headers["X-RateLimit-Remaining"]
    ratelimit_reset = resp.headers["X-RateLimit-Reset"]
    tweets = json.loads(resp.read())
    return ratelimit_remaining, tweets

def get_initial_rate_info():
    resp = fetch_url(RATE_LIMIT_API_URL)
    rate_info = json.loads(resp.read())
    return rate_info["remaining_hits"], rate_info["reset_time_in_seconds"], rate_info["reset_time"]

def fetch_url(url):
    try:
        return urlopen(Request(url))
    except HTTPError, e:
        if e.code == 400: # twitter api limit reached
            raise RateLimitError(e.code)
        if e.code == 502: # Bad Gateway, sometimes get this when making requests. just try again
            raise TweetDumpError(e.code)
        print >> sys.stderr, "[!] HTTP Error %s: %s" % (e.code, e.msg)
    except URLError, e:
        print  >> sys.stderr, "[!] URL Error: %s   URL: %s" % (e.reason, url)
    exit(1)

def print_banner():
    print "tweet-dump %s (c) 2012 %s" % (__version__, __author__)
    print """     .-.
    (. .)__,')
    / V      )
    \  (   \/ .
     `._`.__\\ o ,
        <<  `'   .o..
    """

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="tweet-dump")
    parser.add_argument('username', help="Twitter Screen Name")
    parser.add_argument('file', help="File to write tweeets to")
    parser.add_argument('--count', help="Number of tweets to retrieve per request", default=200)
    parser.add_argument('--maxid', help="ID of Tweet to start dumping after", default=None)
    args = parser.parse_args()

    screen_name = args.username
    count = args.count
    maxid = args.maxid
    out_file_name = args.file

    out_file = None
    try:
        out_file = open(out_file_name, 'w')
    except IOError, e:
        print >> sys.stderr, "[!] error creating file %s" % out_file_name
        exit(1)

    print_banner()
    print "[*] writing tweets to %s \n[*] dumping tweets for user %s" % (out_file_name, screen_name)
    #print "[*] dumping tweets for user %s" % screen_name,

    max_requests = 5
    requests_made = 0
    tweet_count = 0

    twitter_user = get_user(screen_name)

    out_file.write('<!DOCTYPE html>\n<html lang="en">\n\t<head>\n\t\t<meta charset="utf-8">\n')
    out_file.write('\t\t<!--\n\t\t\t{title}\n\t\t\t{url}\n\t\t\t{date}\n\t\t-->\n'.format( title='tweet-dump.py',url='https://github.com/pathawks/tweet-dump', date='Backup Date: '+datetime.date.today().strftime("%B %d, %Y") ) )
    out_file.write('\t\t<title>{name} ({screen_name}) - Tweet Dump</title>\n'.format( name=twitter_user["name"], screen_name=twitter_user["screen_name"] ) )
    out_file.write('\t\t<base href="http://twitter.com/">\n' )
    out_file.write('\t\t<link rel="icon" href="{url}" type="image/png"/>\n'.format( url=twitter_user["profile_image_url"] ) )
    out_file.write('\t\t<style>\n')
    out_file.write('\t\t\tbody{')
    out_file.write('text-align:center;color:#{color};padding:0;margin:0;font-family:"Helvetica Neue", Arial, sans-serif;font-size:14px;'.format( color=twitter_user["profile_text_color"] ) )
    
    if twitter_user["profile_use_background_image"]:
        if twitter_user["profile_background_tile"]:
            out_file.write('background:#{bg} url("{url}") repeat top left;'.format( bg=twitter_user["profile_background_color"], url=base64_image( twitter_user["profile_background_image_url"] ) ) )
        else:
            out_file.write('background:#{bg} url("{url}") no-repeat top left;'.format( bg=twitter_user["profile_background_color"], url=base64_image( twitter_user["profile_background_image_url"] ) ) )
    else:
        out_file.write('background:#{bg};'.format( bg=twitter_user["profile_background_color"] ) )
    
    out_file.write('background-attachment:fixed}\n')
    out_file.write('\t\t\ta{')
    out_file.write('color:#{color}'.format( color=twitter_user["profile_link_color"] ) )
    out_file.write('}\n')
    out_file.write('\t\t\t#container{')
    out_file.write('margin:0 auto;width:500px;background:rgba(255,255,255,0.3);padding:8px 14px' )
    out_file.write('}\n')
    out_file.write('\t\t\t#profile,blockquote{background:#fff;border:#DDD 1px solid;border-radius:5px;width:480px;margin:0 0 10px;padding:0 0 20px 20px;text-align:left}\n')
    out_file.write('\t\t\t#profile{color:#fff;background:#ccc;background:rgba(0,0,0,0.6);width:490px;text-align:center;padding:5px}\n')
    out_file.write('\t\t\t#profile a{color:#fff}\n')
    out_file.write('\t\t\t.profile-picture{margin:20px auto 6px;border:#fff 4px solid;border-radius:4px;display:block;width:73px;height:73px;background:#fff}\n')
    out_file.write('\t\t\t.profile-picture .avatar{border-radius:3px}\n')
    out_file.write('\t\t\t.profile-card-inner h1{font-size:24px;text-shadow:rgba(0, 0, 0, 0.5) 0px 0.6px 0.6px}\n')
    out_file.write('\t\t\t.profile-card-inner h2{font-size:18px;font-weight:normal}\n')
    out_file.write('\t\t</style>\n')
    out_file.write('\t</head>\n\t<body>\n')
    out_file.write('\t\t<div id="container">')

    out_file.write('\n\t\t<div id="profile">')
    out_file.write('\n\t\t\t<a href="{avatar}" class="profile-picture">'.format( avatar=get_user_profile_pic( screen_name, 'original' ) ) )
    out_file.write('\n\t\t\t\t<img src="{avatar}" alt="{name}" class="avatar">'.format( avatar=get_user_profile_pic( screen_name, 'bigger' ), name=twitter_user["name"] ) )
    out_file.write('\n\t\t\t</a>')
    out_file.write('\n\t\t\t<div class="profile-card-inner">')
    out_file.write('\n\t\t\t<h1 class="fullname">{name}</h1>'.format( name=twitter_user["name"] ) )
    out_file.write('\n\t\t\t<h2 class="username"><span class="screen-name">@{screen_name}</span></h2>'.format( screen_name=twitter_user["screen_name"] ) )
    out_file.write('\n\t\t\t<p class="bio ">{bio}</p>'.format( bio=twitter_user["description"] ) )
    out_file.write('\n\t\t\t<p class="location-and-url">')
    out_file.write('\n\t\t\t\t<span class="location">{location}</span>'.format( location=twitter_user["location"] ) )

    if ( twitter_user["url"] and twitter_user["location"] ):
        out_file.write(' &middot; ')

    out_file.write('\n\t\t\t\t<span class="url">')

    if twitter_user["url"]:
        out_file.write('\n\t\t\t\t\t<a href="{url}">{url}</a>'.format( url=twitter_user["url"] ) )

    out_file.write('\n\t\t\t\t</span>')
    out_file.write('\n\t\t\t</p>')
    out_file.write('\n\t\t\t</div>')
    out_file.write('\n\t\t</div>\n')

    while True:
        # get initial rate information
        (remaining, rst_time_s, rst_time) = get_initial_rate_info()

        while remaining > 0:
            try:
                (remaining, tweets) = get_tweets(screen_name, count, maxid)
            except RateLimitError:
                pass
            except TweetDumpError, e:
                pass
            else:
                requests_made += 1
                if len(tweets) > 0:
                    for tweet in tweets:
                        date_data     = time.strptime( tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y" )
                        date_datetime = time.strftime( "%Y-%m-%dT%H:%M:%S+00:00", date_data )
                        date_string   = time.strftime( "%I:%M %p - %d %b %y", date_data )
                        maxid = tweet["id"]
                        tweet_count += 1
                        tweet["text"] = cgi.escape(tweet["text"]).encode('ascii', 'xmlcharrefreplace')

                        if tweet.has_key('entities'):

                            if tweet["entities"].has_key('urls'):
    		                        for entity in tweet["entities"]["urls"]:
			                            if entity.has_key('expanded_url') and entity.has_key('display_url') and entity.has_key('url'):
			                                tweet["text"] = tweet["text"].replace( entity['url'], '<a href="{0}">{1}</a>'.format( cgi.escape(entity['expanded_url'] ).encode('ascii', 'xmlcharrefreplace'), cgi.escape(entity['display_url'] ).encode('ascii', 'xmlcharrefreplace') ) )
                            else:
			                          r = re.compile(r"(http://[^ ]+)")
			                          tweet["text"] = r.sub(r'<a href="\1">\1</a>', tweet["text"])

                        out_file.write('\t\t\t<blockquote class="twitter-tweet tw-align-center" width="500"><p>{tweet_text}</p>&mdash; {user_name} (@{screen_name}) <a href="https://twitter.com/{screen_name}/status/{id}" data-datetime="{date_datetime}">{date_string}</a></blockquote>\n'.format( tweet_text=tweet["text"], id=tweet["id"], screen_name=tweet["user"]["screen_name"], user_name=tweet["user"]["name"], user_id=tweet["user"]["id"], date_string=date_string, date_datetime=date_datetime ) )
                else:
                    print "[*] reached end of tweets"
                    break

        break

    out_file.write('\t\t</div>\n')
    out_file.write('\t\t<script src="http://platform.twitter.com/widgets.js" charset="utf-8"></script>\n')
    out_file.write('\t</body>\n</html>')

    print "[*] %d tweets dumped!" % tweet_count
