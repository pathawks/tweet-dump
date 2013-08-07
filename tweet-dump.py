#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''Load the latest update for a Twitter user and leave it in an XHTML fragment'''

__author__ = 'Pat Hawks <pat@pathawks.com>'
__version__ = '0.2'

import codecs
import getopt
import sys
import twitter
import keyring

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
    (. .)__,')
    / V      )
    \  (   \/ .
     `._`.__\\ o ,
        <<  `'   .o..
	print "tweet-dump %s ©2013 %s" % (__version__, __author__)
	print """     .-.
	"""

def Usage():
	print_banner()
	print 'Usage: %s [options] twitterid' % __file__
	print
	print '  This script fetches a users latest twitter update and stores'
	print '  the result in a file as an XHTML fragment'
	print
	print '  Options:'
	print '    --help -h : print this help'
	print '    --output : the output file [default: stdout]'


def FetchTwitter(user, output):
	assert user
	statuses = twitter.Api().GetUserTimeline(id=user, count=1)
	s = statuses[0]
	xhtml = TWEET_TEMPLATE.format(
		tweet_text = s.text,
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
		opts, args = getopt.gnu_getopt(sys.argv[1:], 'ho', ['help', 'output='])
	except getopt.GetoptError:
		Usage()
		sys.exit(2)
	try:
		user = args[0]
	except:
		Usage()
		sys.exit(2)
	output = None
	for o, a in opts:
		if o in ("-h", "--help"):
			Usage()
			sys.exit(2)
		if o in ("-o", "--output"):
			output = a
	FetchTwitter(user, output)

if __name__ == "__main__":
	main()
