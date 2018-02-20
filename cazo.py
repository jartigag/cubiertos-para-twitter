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
from tenedor import basics, over_time

__version__ = '0.1'

from secrets3 import consumer_key, consumer_secret, access_token, access_token_secret

def main():
    """ To run with python cazo.py """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True) 

    username = "jartigag"

    n_tweets, t_ratio, n_followers, f_ratio = basics(api, username)
    n_days, start_date, end_date, num_tweets, tweets_day_avg, retweets_percent = over_time(api, username)

    # Prints to test if importing tenedor works:
    print("___ getting @\033[1m%s\033[0m's data..." % username)

    print("[+] tweets         : \033[1m%s\033[0m" % n_tweets)
    print("[+] tws/likes ratio: \033[1m%.2f\033[0m"% t_ratio)
    print("[+] followers      : \033[1m%s\033[0m" % n_followers)
    print("[+] fwrs/fwng ratio: \033[1m%.2f\033[0m"% f_ratio)

    print("[+] %d tweets in  : \033[1m%d\033[0m days (from %s to %s)" %
        (num_tweets, n_days, start_date, end_date))

    print("[+] on average     : \033[1m%.2f\033[0m tweets/day, \033[1m%.2f\033[0m %% RTs" % (tweets_day_avg, retweets_percent))

if __name__ == '__main__':
    try:
        main()
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)