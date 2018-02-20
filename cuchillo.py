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
# python3 cuchillo.py
#
# Install:
# pip3 install tweepy

#TODO: logging
#TODO: spinner while long processes

import argparse
import tweepy
import os
import json
from datetime import datetime, timedelta

__version__ = '0.1'

from secrets1 import consumer_key, consumer_secret, access_token, access_token_secret

APP = "cuchillo"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
WHITELIST_FILE = os.path.join(CONFIG_APP_DIR, "whitelist.json")

me = ""
last_date = 0
last_time_checked = datetime(2018, 2, 19, 12, 30, 00) #TODO(119): last_time_checked = followed_date

def last_date_tweeted(api, id):
    global last_date
    tweet = api.user_timeline(id = id, count = 1)[0]
    if tweet:
        last_date = tweet.created_at
    return last_date

def last_date_liked(api, id):
    global last_date
    status = api.favorites(id=id, count=1)[0] #is it faster with Cursor(..).items()?
    #TODO: get last like date. store number of likes, compare with actual number of likes
    return last_date

def main():
    """ To run with python cuchillo.py """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True) 

    me = api.me().screen_name
    print("___ getting @\033[1m%s\033[0m's data..." % me)

    following = []
    n = 0
    for page in tweepy.Cursor(api.friends_ids, screen_name=me).pages():
        following.extend(page)
        if n==1:            print("-- you follow +5k. retreiving them in pages..")
        if n>0:             print("-- [+] page " + str(n))
        if len(page)==5000: n += 1
    print("    " + str(len(following)) + " following")

    followers = []
    m = 0
    for page in tweepy.Cursor(api.followers_ids, screen_name=me).pages():
        followers.extend(page)
        if m==1:            print("-- you follow +5k followers. retreiving them in pages..")
        if m>0:             print("-- [+] page " + str(m))
        if len(page)==5000: m += 1
    print("    " + str(len(followers)) + " followers")

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

    # ACTIVITY filter:
    afterA = []
    inactives = []
    unfollowed = []

    if args.clean:
        if len(afterFB)==1: print("checking " + str(len(afterFB)) + " non-reciprocal user inactivity for " + str(args.clean) + " days..")
        if len(afterFB)>1:  print("checking " + str(len(afterFB)) + " non-reciprocal users inactivity for " + str(args.clean) + " days..")
        for f in afterFB:
            if last_date_tweeted(api, f)+timedelta(days=args.clean) < datetime.today():
                print(" - @\033[1m%s\033[0m has not been active" % api.get_user(f).screen_name)
                inactives.append(f)
        print(str(len(inactives)) + " has not been active for " + str(args.clean) + " days")
        if not len(inactives)==0:
            if len(inactives)==1: unfollow_msg = ("\033[1m unfollow %i user?\033[0m (y/n) " % len(inactives))
            if len(inactives)>1: unfollow_msg = ("\033[1m unfollow %i users?\033[0m (y/n) " % len(inactives))
            if input(unfollow_msg) == "y":
                for f in inactives:
                    api.destroy_friendship(f)
                    unfollowed.append(f)
    else:
        if len(afterFB)==1: print("checking " + str(len(afterFB)) + " non-reciprocal user activity..")
        if len(afterFB)>1:  print("checking " + str(len(afterFB)) + " non-reciprocal users activity..")

        for f in afterFB:
            if last_date_tweeted(api, f) > last_time_checked: #TODO: last_time_checked = followed_date
                afterA.append(f)
                if input(" - @\033[1m%s\033[0m has been active. unfollow? (y/n) " % api.get_user(f).screen_name) == "y":
                    api.destroy_friendship(f)
                    unfollowed.append(f)
            #elif has_liked(api, f):
        print(str(len(afterA)) + " has been active since last time checked")

    #print(str(len(afterA)) + " in afterA")
    print(str(len(unfollowed)) + " has been unfollowed")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=
        ">>\"separate meat from bone\" tool for twitter, version %s by @jartigag" % __version__,
                                     usage='%(prog)s [options]')
    parser.add_argument('-c', '--clean', type=int, metavar='N_DAYS',
                        help='unfollow inactive ones for > N_DAYS')

    args = parser.parse_args()

    try:
        main()
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)
