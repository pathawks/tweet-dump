#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''Load the latest update for a Twitter user and leave it in an XHTML fragment'''

__author__ = 'Pat Hawks <pat@pathawks.com>'
__version__ = '0.2'

import cgi
import codecs
import getopt
import sys
import twitter
import keyring
import webbrowser

TWEET_TEMPLATE = """
			<blockquote class="twitter-tweet tw-align-center" width="500"><p>{tweet_text}</p>&mdash; {user_name} (@{screen_name}) <a href="https://twitter.com/{screen_name}/status/{id}" data-datetime="{date_datetime}">{date_string}</a></blockquote>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="utf-8">
		<!--
			tweet-dump.py
			https://github.com/pathawks/tweet-dump
			Backup Date: {current_time}
		-->
		<title>{name} (@{screen_name})</title>
		<base href="http://twitter.com/">
		<link rel="icon" href="{url}" type="image/png"/>
		<style>
			body{text-align:center;color:#{color};padding:0;margin:0;font-family:"Helvetica Neue", Arial, sans-serif;font-size:14px;background:#{bg};background-attachment:fixed}
			a{color:#{color}}
			#container{margin:0 auto;width:500px;background:rgba(255,255,255,0.3);padding:8px 14px' )}
			#profile,blockquote{background:#fff;border:#DDD 1px solid;border-radius:5px;width:480px;margin:0 0 10px;padding:0 0 20px 20px;text-align:left}
			#profile{color:#fff;background:#ccc;background:rgba(0,0,0,0.6);width:490px;text-align:center;padding:5px}
			#profile a{color:#fff}
			.profile-picture{margin:20px auto 6px;border:#fff 4px solid;border-radius:4px;display:block;width:73px;height:73px;background:#fff}
			.profile-picture .avatar{border-radius:3px}
			.profile-card-inner h1{font-size:24px;text-shadow:rgba(0, 0, 0, 0.5) 0px 0.6px 0.6px}
			.profile-card-inner h2{font-size:18px;font-weight:normal}
		</style>
	</head>
	<body>
		<div id="container">
			<div id="profile">
				<a href="{avatar}" class="profile-picture">
					<img src="{avatar}" alt="{name}" class="avatar">
				</a>
				<div class="profile-card-inner">
				<h1 class="fullname">{name}</h1>
				<h2 class="username"><span class="screen-name">@{screen_name}</span></h2>
				<p class="bio ">{bio}</p>
				<p class="location-and-url">
					<span class="location">{location}</span> &middot; 
					<span class="url">
						<a href="{url}">{url}</a>
					</span>
				</p>
				</div>
			</div>
			{timeline}
		</div>
		<script src="http://platform.twitter.com/widgets.js" charset="utf-8"></script>
</body>
</html>
"""

def print_banner():
	print "tweet-dump %s ©2013 %s" % (__version__, __author__)
	print """     .-.
    (. .)__,')
    / V      )
    \  (   \/ .
     `._`.__\\ o ,
        <<  `'   .o..
	"""

def Usage():
	print_banner()
	print 'Usage: %s [options] twitterid' % __file__
	print
	print '  This script fetches a users latest twitter update and stores'
	print '  the result in a file as an XHTML fragment'
	print
	print '  Options:'
	print '    -h, --help        print this help'
	print '    -o, --output      the output file [default: stdout]'
	print '    -n, --number      the number of Tweets to retrieve [default: 1]'


def get_access_token(consumer_key, consumer_secret):
	try:
		from urlparse import parse_qsl
	except:
		from cgi import parse_qsl
	import webbrowser
	import oauth2 as oauth
	REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
	ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
	AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
	SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'
	signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
	oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
	oauth_client = oauth.Client(oauth_consumer)

	print 'Requesting temp token from Twitter'

	resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'POST', body="oauth_callback=oob")

	if resp['status'] != '200':
		print 'Invalid respond from Twitter requesting temp token: %s' % resp['status']
	else:
		request_token = dict(parse_qsl(content))
		url = '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])

		print ''
		print 'I will try to start a browser to visit the following Twitter page'
		print 'if a browser will not start, copy the URL to your browser'
		print 'and retrieve the pincode to be used'
		print 'in the next step to obtaining an Authentication Token:'
		print ''
		print url
		print ''

		webbrowser.open(url)
		pincode = raw_input('Pincode? ')

		token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
		token.set_verifier(pincode)

		print ''
		print 'Generating and signing request for an access token'
		print ''

		oauth_client = oauth.Client(oauth_consumer, token)
		resp, content = oauth_client.request(ACCESS_TOKEN_URL, method='POST', body='oauth_callback=oob&oauth_verifier=%s' % pincode)
		access_token = dict(parse_qsl(content))

		if resp['status'] != '200':
			print 'The request for a Token did not succeed: %s' % resp['status']
			print access_token
		else:
			print 'Your Twitter Access Token key: %s' % access_token['oauth_token']
			print '          Access Token secret: %s' % access_token['oauth_token_secret']
			print ''
			keyring.set_password(__file__, 'oauth_consumer', consumer_key)
			keyring.set_password(__file__, 'oauth_consumer_secret', consumer_secret)
			keyring.set_password(__file__, 'oauth_token', access_token['oauth_token'])
			keyring.set_password(__file__, 'oauth_token_secret', access_token['oauth_token_secret'])


def UserSignIn():
	print_banner()
	print 'Before you can use %s, you must sign in with Twitter' % __file__
	print
	print 'Setup a new Twitter Application at https://dev.twitter.com/apps/new'
	print 'Then provide your applications details below'
	print
	webbrowser.open('https://dev.twitter.com/apps/new')
	consumer_key = raw_input('Enter your consumer key: ')
	consumer_secret = raw_input("Enter your consumer secret: ")
	get_access_token(consumer_key, consumer_secret)



def FetchTwitter(user, output, number):
	assert user
	statuses = twitter.Api(
			consumer_key=keyring.get_password(__file__, 'oauth_consumer'),
			consumer_secret=keyring.get_password(__file__, 'oauth_consumer_secret'),
			access_token_key=keyring.get_password(__file__, 'oauth_token'),
			access_token_secret=keyring.get_password(__file__, 'oauth_token_secret')
		).GetUserTimeline(screen_name=user, count=number)
	for s in statuses:
		xhtml = TWEET_TEMPLATE.format(
			tweet_text = cgi.escape(s.text).encode('ascii', 'xmlcharrefreplace'),
			user_name = s.user.name,
			screen_name = s.user.screen_name,
			id = s.id,
			date_datetime = s.created_at_in_seconds,
			date_string = s.relative_created_at
		)
		if output:
			Save(xhtml, output)
		else:
			print xhtml


def Save(xhtml, output):
	out = codecs.open(output, mode='w', encoding='ascii',
			              errors='xmlcharrefreplace')
	out.write(xhtml)
	out.close()

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], 'hon', ['help', 'output=', 'number='])
	except getopt.GetoptError:
		Usage()
		sys.exit(2)
	try:
		user = args[0]
	except:
		Usage()
		sys.exit(2)
	output = None
	number = 1
	for o, a in opts:
		if o in ("-h", "--help"):
			Usage()
			sys.exit(2)
		if o in ("-o", "--output"):
			output = a
		if o in ("-n", "--number"):
			number = a
	FetchTwitter(user, output, number)

if __name__ == "__main__":
	if keyring.get_password(__file__, 'oauth_consumer'):
		main()
	else:
		UserSignIn()
