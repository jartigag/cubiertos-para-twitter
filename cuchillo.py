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
from datetime import datetime

__version__ = '0.1'

from secrets import consumer_key, consumer_secret, access_token, access_token_secret

APP = "cuchillo"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
WHITELIST_FILE = os.path.join(CONFIG_APP_DIR, "whitelist.json")

me = "jartigag" #TODO: get me.screen_name
last_date = 0
last_time_checked = datetime(2018, 2, 16, 22, 00, 00) #TODO: save last_time_checked

def has_tweeted(api, id):
    global last_date
    status = api.user_timeline(id=id, count=1)[0] #is it faster with Cursor(..).items()?
    last_date = status.created_at
    return (last_date > last_time_checked)

def has_liked(api, id):
    global last_date
    status = api.favorites(id=id, count=1)[0] #is it faster with Cursor(..).items()?
    #TODO:
    last_date = status.created_at
    return (last_date > last_time_checked)

def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True) 
   
    
    following = []
    n = 0
    for page in tweepy.Cursor(api.friends_ids, screen_name=me).pages():
        following.extend(page)
    #    if n==1:            print("-- " + me + " follows +5k. retreiving them in pages..")
    #    if n>0:             print("-- [+] page " + str(n)) #TODO: progress bar
    #    if len(page)==5000: n += 1
    #print(str(len(following)) + " following")

    followers = []
    m = 0
    for page in tweepy.Cursor(api.followers_ids, screen_name=me).pages():
        followers.extend(page)
    #    if m==1:            print("-- " + me + " +5k followers. retreiving them in pages..")
    #    if m>0:             print("-- [+] page " + str(m)) #TODO: progress bar
    #    if len(page)==5000: m += 1
    #print(str(len(followers)) + " followers")

    # WHITELIST filter
    afterWL = []
    for f in following:
        with open(WHITELIST_FILE, encoding="utf-8") as file:
            whitelist = json.load(file)
            if f not in whitelist: afterWL.append(f)
    #print(str(len(afterWL)) + " in afterWL")

    # FOLLOWBACK filter
    afterFB = list(set(afterWL) - set(followers))
    #print(str(len(afterFB)) + " in afterFB")

    print("checking if " + str(len(afterFB)) + " non-reciprocal users have been active..")

    # ACTIVITY filter:
    afterA = []
    for f in afterFB:
        if has_tweeted(api, f): afterA.append(f)
        #if has_liked(api, f):
    #print(str(len(afterA)) + " in afterA")

    print(str(len(afterA)) + " has been active since last time checked:")

    for f in afterA:
        print(" - " + api.get_user(f).screen_name)
    #TODO: unfollow this users?
    print("unfollow this users?")

    #PRINT screen-names
    #for f in list:
    #    print(api.get_user(f).screen_name)

if __name__ == '__main__':
    try:
        main()
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)