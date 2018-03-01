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
from datetime import datetime
from time import time,sleep
from random import randrange
from tenedor import basics, over_time

__version__ = '0.1'

from secrets3 import consumer_key, consumer_secret, access_token, access_token_secret

def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, compression=True)
    myUsername = api.me().screen_name
    myCount = api.me().followers_count
    print("you are: %s, you have %i followers. let's start!" % (myUsername, myCount))

    t = 2 # secs between tries
    n = 0
    while True:
        try:
            # note it only considers last 20 followers (just testing followers request)
            randFlwr = api.followers(screen_name=myUsername)[randrange(20)]
            randFlwrUsername = randFlwr.screen_name
            randFlwrOfFlwr = api.followers(screen_name=randFlwrUsername)[randrange(20)]
            randFlwrOfFlwrUsername = randFlwrOfFlwr.screen_name
            if randFlwrOfFlwrUsername is myUsername: return
            n+=1
            print("(%i) [sleep %i, reqs left: %s flwrs, %s tweets]" % (n,t,api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'],api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining']))
            n_tweets, t_ratio, n_followers, f_ratio = basics(api, randFlwrOfFlwrUsername)
            if f_ratio < 1:
                n_days, start_date, end_date, num_tweets, tweets_day_avg, retweets_percent = over_time(api, randFlwrOfFlwrUsername)
                if tweets_day_avg > 0.5:
                    print("    \033[1m%s\033[0m (%.2f fwrs/fwng, %.2f tweets/day)" % (randFlwrOfFlwrUsername,f_ratio,tweets_day_avg))
                    api.add_list_member(slug='cazo',owner_screen_name='@'+myUsername,screen_name=randFlwrOfFlwrUsername)
            sleep(t)
        except tweepy.error.RateLimitError as e:
            print('%s /followers/list requests left' % api.rate_limit_status()['resources']['followers']['/followers/list']['remaining'])
            print('%s /statuses/user_timeline left '% api.rate_limit_status()['resources']['statuses']['/statuses/user_timeline']['remaining'])
            reset_time = api.rate_limit_status()['resources']['followers']['/followers/list']['reset']
            current_time = int(time())
            wait_time = reset_time - current_time
            print("%i fetched with %i-secs pauses (sleeping %i secs)" % (n,t,wait_time))
            n=0
            #TODO: progressbar instead of this while
            while current_time<reset_time:
                current_time = int(time())
                wait_time = reset_time - current_time
                sleep(60)
                print("sleeping %i secs more.. (=%i minutes)" % (wait_time,wait_time/60))
        except Exception as e:
            pass

    #TODO: guardar los ids ya analizados (primero en array, más adelante en db)
    #              y comparar antes de analizar, para evitar
    #              malgastar peticiones a la api
    #TODO: rotar entre keys para acelerar el proceso

if __name__ == '__main__':
    main()