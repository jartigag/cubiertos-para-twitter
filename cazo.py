#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @jartigag
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Usage:
# python3 cazo.py
#
# Install:
# pip3 install tweepy numpy

import tweepy
import numpy
import argparse
from datetime import datetime
from time import time,sleep
from random import randrange
from tenedor import basics, over_time

__version__ = '0.1'

from secrets1 import consumer_key, consumer_secret, access_token, access_token_secret

def main():
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth, compression=True)
	myUsername = api.me().screen_name
	myCount = api.me().followers_count
	print("you are %s, you have %i followers. let's start!" % (myUsername, myCount))

	t = 140 # secs between tries
	n = 0
	while True:
		while True:
			try:
				randFlwr = api.followers_ids(screen_name=myUsername)[randrange(myCount)]
				randFlwrUsername = api.get_user(randFlwr).screen_name
				randFlwrCount = api.get_user(randFlwr).followers_count
				randFlwrOfFlwr = api.followers_ids(screen_name=randFlwrUsername)[randrange(randFlwrCount)]
				randFlwrOfFlwrUsername = api.get_user(randFlwrOfFlwr).screen_name
				n+=1
				print("(%i) [sleep %i, reqs left: %s flwrs, %s tweets]" % (n,t,api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'],api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining']))
				if randFlwrOfFlwrUsername==myUsername:
					print("    chosen myself. let's try again")
					break
				
				n_tweets, l_ratio, n_followers, f_ratio = basics(api, randFlwrOfFlwrUsername)
				
				if args.tweets:
					if n_tweets > args.tweets: break
				if args.likes_tweets_ratio:
					if l_ratio > args.likes_tweets_ratio: break
				if args.followers:
					if n_followers > args.followers: break
				if args.followers_following_ratio:
					if f_ratio > args.followers_following_ratio: break
				
				n_days, start_date, end_date, num_tweets, tweets_day_avg, retweets_percent = over_time(api, randFlwrOfFlwrUsername)
				
				if args.tweets_day_average:
					if tweets_day_avg < args.tweets_day_average: break
				if args.retweets_percent:
					if retweets_percent < args.retweets_percent: break
				
				print("    \033[1m%s\033[0m (%.2f fwrs/fwng, %.2f tweets/day)" % (randFlwrOfFlwrUsername,f_ratio,tweets_day_avg))
				api.add_list_member(slug='cazo',owner_screen_name='@'+myUsername,screen_name=randFlwrOfFlwrUsername)
				
				sleep(t)

			except tweepy.error.RateLimitError as e:
				print('    %s /followers/list requests left' % api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'])
				print('    %s /statuses/user_timeline left '% api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining'])
				reset_time = api.rate_limit_status()['resources']['followers']['/followers/list']['reset']
				current_time = int(time())
				wait_time = reset_time - current_time
				print(" == %i fetched with %i-secs pauses (sleeping %i secs)" % (n,t,wait_time))
				n=0
				#TODO: progressbar instead of this while
				while current_time<reset_time:
					current_time = int(time())
					wait_time = reset_time - current_time
					sleep(60)
					print("sleeping %i secs more.. (=%i minutes)" % (wait_time,wait_time/60))
			except Exception as e:
				print(e)
				pass
		sleep(t)

	#TODO: guardar los ids ya analizados (primero en array, más adelante en db)
	#              y comparar antes de analizar, para evitar
	#              malgastar peticiones a la api
	#TODO: rotar entre keys para acelerar el proceso

if __name__ == '__main__':

	#TODO: greater-than, less-than args

	parser = argparse.ArgumentParser(description=
		">>\"serve from pot to dish\" - tool for twitter, version %s by @jartigag" % __version__,
									 usage='%(prog)s [options]')
	parser.add_argument('-f', '--followers', type=int,
						help='filter by number of followers')
	parser.add_argument('-l', '--likes_tweets_ratio', type=float,
						help='filter by likes/tweets ratio')
	parser.add_argument('-r', '--followers_following_ratio', type=float,
						help='filter by followers/following ratio')
	parser.add_argument('-t', '--tweets', type=int,
						help='filter by number of tweets')
	parser.add_argument('-d', '--tweets_day_average', type=float,
						help='filter by tweets/day average')
	parser.add_argument('-p', '--retweets_percent', type=float,
						help='filter by retweets percent')

	args = parser.parse_args()

	main()