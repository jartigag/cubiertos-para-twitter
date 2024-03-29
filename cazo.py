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

#TODO. last_date_tweet not working

import tweepy
import argparse
from datetime import datetime
from time import time,sleep
from random import randrange
from tenedor import basics, over_time
import os
import logging

__version__ = '0.1' # working on v0.2

# WHAT'S NEW (v0.2):
#
# + -d, --last_date_tweet: filter by last date tweet
# + secrets array of any size

from secrets import secrets

s = 0 # counter of the actual secret: secrets[i]

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

def checkOverTime(tweets_day_avg, end_date, retweets_percent):
	if args.tweets_day_average:
		if args.tweets_day_average > 0:
			if tweets_day_avg < args.tweets_day_average: return False
		if args.tweets_day_average < 0:
			if tweets_day_avg > -args.tweets_day_average: return False
	if args.last_tweet_date:
		if int(args.last_tweet_date) > 0:
			if end_date < datetime.strptime(args.last_tweet_date, '%y%m%d'): return False
		if int(args.last_tweet_date) < 0:
			if end_date > datetime.strptime(args.last_tweet_date, '-%y%m%d'): return False
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
		print("    %s just tweeted: \033[1m«\033[0m %s \033[1m»\033[0m" % (status.user.screen_name,status.text))
		self.targetUser = status.user.screen_name
		return False

	def on_error(self, status_code):
		print("error on KeywordListener: %i. retrying.." % status_code)
		return True # don't kill the stream
	def on_timeout(self):
		print("timeout on KeywordListener. retrying..")
		return True # don't kill the stream

def main():
	global secrets,s
	auth = tweepy.OAuthHandler(secrets[s]['consumer_key'], secrets[s]['consumer_secret'])
	auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
	api = tweepy.API(auth, compression=True)
	myUsername = api.me().screen_name
	myCount = api.me().followers_count
	print("[-] hi %s! you have %i followers. let's start!" % (myUsername, myCount))
	logger.warning("[-] hi %s! you have %i followers. let's start!" % (myUsername, myCount))

	if args.keyword:
		keywordList = args.keyword+'-'+datetime.now().strftime('%d%b%Hh')
		targetList = api.create_list(keywordList,'private')
	elif args.user:
		userFlwrsList = args.user+'-'+datetime.now().strftime('%d%b%Hh')
		targetList = api.create_list(userFlwrsList,'private')
	else:
		todayslist = 'cazo-'+datetime.now().strftime('%d%b%H:%M')
		targetList = api.create_list(todayslist,'private')

	t = 1 # secs between reqs
	n = 0

	print("[_] targeting users who match this params: ")
	for arg in vars(args):
		if vars(args)[arg] is not None:
			if type(vars(args)[arg])==int or type(vars(args)[arg])==float:
				if vars(args)[arg]>=0:
					print(arg+':','>',vars(args)[arg])
					logger.warning(arg+': > '+str(vars(args)[arg]))
				else:
					print(arg+':','<',-vars(args)[arg])
					logger.warning(arg+': < '+str((-vars(args)[arg])))
			elif arg=='last_tweet_date':
				if arg.split()[0]=='-':
					print(arg+':','<',vars(args)[arg])
					logger.warning(arg+': < '+str(vars(args)[arg]))
				else:
					print(arg+':','>',vars(args)[arg])
					logger.warning(arg+': > '+str(vars(args)[arg]))
			else:
				print(arg+':','"%s"' % vars(args)[arg])
				logger.warning(arg+': "%s"' % vars(args)[arg])
	logger.warning("[_] targeting users who match this params: ")

	if args.keyword:
		print('[_] capturing "\033[1m%s\033[0m" on the fly..' % args.keyword)
		logger.warning('[_] capturing "%s" on the fly..' % args.keyword)

	init_time = time()

	while True:
		try:
			n+=1
			print("[%i]" % n)
			if args.keyword:
				kwListener = KeywordListener()
				stream = tweepy.streaming.Stream(auth, kwListener)
				stream.filter(track=[args.keyword])
				targetUser = kwListener.targetUser
			else:
				if args.user:
					#TODO: check if args.user is valid
					randFlwrUsername = args.user
				else:
					randFlwr = api.followers_ids(screen_name=myUsername)[randrange(myCount)]
					randFlwrUsername = api.get_user(randFlwr).screen_name
				randFlwrCount = api.get_user(screen_name=randFlwrUsername).followers_count
				randFlwrOfFlwr = api.followers_ids(screen_name=randFlwrUsername)[randrange(randFlwrCount)]
				targetUser = api.get_user(randFlwrOfFlwr).screen_name

			#print("(%i) [sleep %i, reqs left: %s flwrs, %s tweets]" % (n,t,api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'],api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining']))

			if targetUser==myUsername: continue

			n_tweets, l_ratio, n_followers, f_ratio = basics(api, targetUser)
			print("    > checking basics params..")
			if not checkBasics(n_tweets, l_ratio, n_followers, f_ratio):
				print("    >> it doesn't match. let's pick another target")
				continue

			n_days, start_date, end_date, num_tweets, tweets_day_avg, retweets_percent = over_time(api, targetUser)
			print("    > checking params over time..")
			if not checkOverTime(tweets_day_avg, end_date, retweets_percent):
				print("    >> it doesn't match. let's pick another target")
				continue

			print("    >> \033[1m%s\033[0m (%.2f fwrs/fwng, %.2f tweets/day) matches required params!" % (targetUser,f_ratio,tweets_day_avg))
			logger.warning("    >> %s (%.2f fwrs/fwng, %.2f tweets/day) matches required params!" % (targetUser,f_ratio,tweets_day_avg))
			#TODO: in () print required params
			api.add_list_member(list_id=targetList.id,owner_screen_name='@'+myUsername,id=targetUser)

			sleep(t)

		except tweepy.error.RateLimitError as e:
			#print('[!] %s /followers/list requests left' % api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'])
			#print('[!] %s /statuses/user_timeline left '% api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining'])

			#(no longer needed) reset_time = api.rate_limit_status()['resources']['followers']['/followers/list']['reset']
			current_time = time()
			#wait_time = reset_time - int(current_time)

			running_time = int(current_time - init_time)
			print("[\033[91m#\033[0m] api limit reached! \033[1m%i\033[0m users analysed (running time: %i secs, pauses: %i secs, secrets%i)." % (n,running_time,t,s))
			#(no longer needed) resuming in %i secs.. % (wait_time)
			logger.warning("[#] api limit reached! %i users analysed (running time: %i secs, pauses: %i secs, secrets%i)." % (n,running_time,t,s))

			# rotate secrets[s]
			if s < len(secrets)-1:
				s+=1
			else:
				s=0

			auth = tweepy.OAuthHandler(secrets[s]['consumer_key'], secrets[s]['consumer_secret'])
			auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
			api = tweepy.API(auth, compression=True)

			'''
			while current_time<reset_time:
				current_time = int(time())
				wait_time = reset_time - current_time
				sleep(60)
				print("sleeping %i secs more.. (=%i minutes)" % (wait_time,wait_time/60))
			'''

			n=0
			init_time = time()

		except Exception as e:
			running_time = int(time() - init_time)

			if e.args[0]=='Twitter error response: status code = 429':
				print("[\033[91m!\033[0m] error: tenedor.py made too many requests.. give it a break ;).")
				print("    %i users analysed (running time: %i secs, pauses: %i secs)." % (n,running_time,t))
				logger.warning("[!] error: 429. %i users analysed (running time: %i secs, pauses: %i secs)." % (n,running_time,t))
				sleep(10) # sleep(900)
			else:
				print("[\033[91m!\033[0m] error: "+str(e))
				logger.warning("[!] error: "+str(e))
			pass

		sleep(t)

	#TODO: guardar los ids ya analizados (primero en array, más adelante en db)
	#              y comparar antes de analizar, para evitar
	#              malgastar peticiones a la api
	#TODO: rotar entre keys para acelerar el proceso

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description=
		">> \"serve from pot to dish\"\ntool for twitter, v%s by @jartigag" % __version__,
		formatter_class=argparse.RawTextHelpFormatter,
		usage='%(prog)s [arguments (+value: >value, -value: <value)]')
	parser.add_argument('-f', '--followers', type=int,
						help='filter by number of followers')
	parser.add_argument('-l', '--likes_tweets_ratio', type=float,
						help='filter by likes/tweets ratio')
	parser.add_argument('-r', '--followers_following_ratio', type=float,
						help='filter by followers/following ratio')
	parser.add_argument('-t', '--tweets', type=int,
						help='filter by number of tweets')
	parser.add_argument('-d', '--last_tweet_date', metavar='yymmdd',
						help='filter by last tweet date. date format e.g.: 700101 (1st Jan 1970)')
	parser.add_argument('-a', '--tweets_day_average', type=float,
						help='filter by tweets/day average')
	parser.add_argument('-p', '--retweets_percent', type=float,
						help='filter by retweets percent')

	parser.add_argument('-k', '--keyword',
						help='target users by keyword')

	parser.add_argument('-u', '--user',
						help='target followers of user')

	args = parser.parse_args()

	logger = logging.getLogger()
	logger.setLevel(logging.WARNING)
	#TODO: if file_dir doesn't exist
	file_dir = os.path.join(os.path.expanduser("~"), ".config/cazo")

	if not any(vars(args).values()):
		print("[!] set some parameters to filter users!")
		parser.print_help()
	else:
		if args.keyword:
			logFile = logging.FileHandler(os.path.join(file_dir, datetime.now().strftime('%y%m%d-%H:%M') + " - " + args.keyword + ".log"))
		elif args.user:
			logFile = logging.FileHandler(os.path.join(file_dir, datetime.now().strftime('%y%m%d-%H:%M') + " - " + args.user + ".log"))
		else:
			logFile = logging.FileHandler(os.path.join(file_dir, datetime.now().strftime('%y%m%d-%H:%M') + " - cazo.log"))
		logger.addHandler(logFile)
		main()
