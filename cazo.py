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
# pip3 install tweepy

import tweepy
import argparse
from datetime import datetime
from time import time,sleep
from random import randrange
from tenedor import basics, over_time

__version__ = '0.1'

from secrets2 import consumer_key, consumer_secret, access_token, access_token_secret

def checkBasics(n_tweets, l_ratio, n_followers, f_ratio):
	if args.tweets:
		if args.tweets > 0:
			if n_tweets < args.tweets: return False
		if args.tweets < 0:
			if n_tweets > -args.tweets: return False

	if args.likes_tweets_ratio:
		if args.likes_tweets_ratio > 0:
			if l_ratio < args.likes_tweets_ratio: return False
		if args.likes_tweets_ratio < 0:
			if l_ratio > -args.likes_tweets_ratio: return False

	if args.followers:
		if args.followers > 0:
			if n_followers < args.followers: return False
		if args.followers < 0:
			if n_followers > -args.followers: return False

	if args.followers_following_ratio:
		if args.followers_following_ratio > 0:
			if f_ratio < args.followers_following_ratio: return False
		if args.followers_following_ratio < 0:
			if f_ratio > -args.followers_following_ratio: return False

	return True

def checkOverTime(tweets_day_avg, retweets_percent):
	if args.tweets_day_average:
		if args.tweets_day_average > 0:
			if tweets_day_avg < args.tweets_day_average: return False
		if args.tweets_day_average < 0:
			if tweets_day_avg > -args.tweets_day_average: return False
	if args.retweets_percent:
		if args.retweets_percent > 0:
			if retweets_percent < args.retweets_percent: return False
		if args.retweets_percent < 0:
			if retweets_percent > -args.retweets_percent: return False

	return True

class KeywordListener(tweepy.StreamListener):

	def __init__(self):
	    self.targetUser = ""
	    super(KeywordListener,self).__init__()

	def on_status(self, status):
		print("    %s just tweeted: \033[1m<<\033[0m %s \033[1m>>\033[0m" % (status.user.screen_name,status.text))
		self.targetUser = status.user.screen_name
		return False

	def on_error(self, status_code):
		print("error on KeywordListener: " + status_code + ". retrying..")
		return True # don't kill the stream
	def on_timeout(self):
		print("timeout on KeywordListener. retrying..")
		return True # don't kill the stream
	
def main():
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth, compression=True)
	myUsername = api.me().screen_name
	myCount = api.me().followers_count
	print("[-] hi! you are %s, you have %i followers. let's start!" % (myUsername, myCount))

	if args.keyword:
		keywordList = args.keyword+'-'+datetime.now().strftime('%d%b%y_%H:%M')
		targetList = api.create_list(keywordList,'private')
	else:
		todayslist = 'cazo-'+datetime.now().strftime('%d%b%y_%H:%M')
		targetList = api.create_list(todayslist,'private')


	t = 1 # secs between reqs
	n = 0

	print("[>] target users match this params: ") #TODO: print target params
	if args.keyword:
		print("[_] capturing #%s hasthag on the fly.." % args.keyword)
	while True:
		try:
			if args.keyword:
				kwListener = KeywordListener()
				stream = tweepy.streaming.Stream(auth, kwListener)
				stream.filter(track=[args.keyword])
				targetUser = kwListener.targetUser
			else:
				randFlwr = api.followers_ids(screen_name=myUsername)[randrange(myCount)]
				randFlwrUsername = api.get_user(randFlwr).screen_name
				randFlwrCount = api.get_user(randFlwr).followers_count
				randFlwrOfFlwr = api.followers_ids(screen_name=randFlwrUsername)[randrange(randFlwrCount)]
				targetUser = api.get_user(randFlwrOfFlwr).screen_name

			n+=1
			
			print("(%i) [sleep %i, reqs left: %s flwrs, %s tweets]" % (n,t,api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'],api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining']))
			
			if targetUser==myUsername: continue
			
			n_tweets, l_ratio, n_followers, f_ratio = basics(api, targetUser)
			
			if not checkBasics(n_tweets, l_ratio, n_followers, f_ratio): continue
			
			n_days, start_date, end_date, num_tweets, tweets_day_avg, retweets_percent = over_time(api, targetUser)
			
			if not checkOverTime(tweets_day_avg, retweets_percent): continue
			
			print("    \033[1m%s\033[0m (%.2f fwrs/fwng, %.2f tweets/day) matches required params!" % (targetUser,f_ratio,tweets_day_avg))
			#TODO: in () print required params
			api.add_list_member(list_id=targetList.id,owner_screen_name='@'+myUsername,id=targetUser)

			sleep(t)

		except tweepy.error.RateLimitError as e:
			print(' [\033[91m!\033[0m] %s /followers/list requests left' % api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'])
			print(' [\033[91m!\033[0m] %s /statuses/user_timeline left '% api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining'])
			
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
			if e.args[0]=='Twitter error response: status code = 429':
				print(" [\033[91m!\033[0m] that means: tenedor.py has made too many requests.. give it a break ;)")
				sleep(30)
			pass

		sleep(t)

	#TODO: guardar los ids ya analizados (primero en array, más adelante en db)
	#              y comparar antes de analizar, para evitar
	#              malgastar peticiones a la api
	#TODO: rotar entre keys para acelerar el proceso

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description=
		">>\"serve from pot to dish\" - tool for twitter, version %s by @jartigag" % __version__,
									 usage='%(prog)s [arguments (+value: >value, -value: <value)]')
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

	parser.add_argument('-k', '--keyword',
						help='target users by keyword')

	args = parser.parse_args()

	if not any(vars(args).values()):
		print("[!] set some parameters to filter users!")
		parser.print_help()
	else:
		main()