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
# 
# Usage:
# python3 cuchillo.py
#
# Install:
# pip3 install tweepy

import tweepy
import os
import json

__version__ = '0.1'

from secrets3 import consumer_key, consumer_secret, access_token, access_token_secret

APP = "cuchillo"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
WHITELIST_FILE = os.path.join(CONFIG_APP_DIR, "whitelist.json")

following = []
analising = []
me = "jartigag"

def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True) 
   
    n = 0
    for page in tweepy.Cursor(api.friends_ids, screen_name=me).pages():
        following.extend(page)
        if n==1:            print(me + " follows +5k. retreiving them in pages..")
        if n>0:             print("page " + str(n)) #TODO: progress bar
        if len(page)==5000: n += 1

    print(str(len(following)) + " following\n")

    # WHITELIST
    for f in following:
        with open(WHITELIST_FILE, encoding="utf-8") as file:
            whitelist = json.load(file)

            if f in whitelist:
                print(api.get_user(f).screen_name + " is in whitelist")
            else:
                analising.append(f)

    print("\nanalising:")
    for u in analising:
        print(api.get_user(u).screen_name)

if __name__ == '__main__':
    try:
        main()
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)