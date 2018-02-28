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
#TODO: add to Whitelist

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

def last_date_tweeted(api, id):
    global last_date
    tweet = api.user_timeline(id = id, count = 1)[0]
    if tweet:
        last_date = tweet.created_at
    return last_date

#def last_date_liked(api, id):
#    global last_date
#    status = api.favorites(id=id, count=1)[0]
#    #TODO: 2 options
#       - get last like date
#       - store number of likes, compare with actual number of likes
#    return last_date

def main():
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
        if m==1:            print("-- you have +5k followers. retreiving them in pages..")
        if m>0:             print("-- [+] page " + str(m))
        if len(page)==5000: m += 1
    print("    " + str(len(followers)) + " followers")

    # WHITELIST filter:
    afterWL = []
    for f in following:
        with open(WHITELIST_FILE, encoding="utf-8") as file:
            whitelist = json.load(file)
            if f not in whitelist: afterWL.append(f)
    #print(str(len(afterWL)) + " in afterWL")

    # FOLLOWBACK filter:
    nonreciprocals = list(set(afterWL) - set(followers))
    #print(str(len(afterFB)) + " in afterFB")

    # ACTIVITY filter:
    results = []
    asktounfollow = []
    unfollowed = []

    if len(nonreciprocals)==0:
        return
    else:
        if args.active:
            active_or_inactive = "active"
            ndays=args.active
        if args.inactive:
            active_or_inactive = "inactive"
            ndays=args.inactive
        if len(nonreciprocals)==1: howmany_nonreciprocals = "1 non-reciprocal user has"
        if len(nonreciprocals)>1:  howmany_nonreciprocals = str(len(nonreciprocals)) + " non-reciprocal users have"
        print( "checking if %s been %s for %s days.." % (howmany_nonreciprocals, active_or_inactive, ndays) )

        for f in nonreciprocals:
            if args.active:
                if last_date_tweeted(api, f) + timedelta(days=ndays) > datetime.today():
                    print(" - @\033[1m%s\033[0m has been %s." % (api.get_user(f).screen_name, active_or_inactive) )
                    results.append(f)
                #elif has_liked(api, f) < datetime.today() - timedelta(days=ndays): actives.append(f)
                    if args.confirmation:
                        if input( "   unfollow? (y/n) ") == "y":
                            api.destroy_friendship(f)
                            unfollowed.append(f)
                    else:
                        asktounfollow.append(f)

            if args.inactive:
                if last_date_tweeted(api, f) + timedelta(days=ndays) < datetime.today():
                    print(" - @\033[1m%s\033[0m has been %s." % (api.get_user(f).screen_name, active_or_inactive) )
                    results.append(f)
                    if args.confirmation:
                        if input( "   unfollow? (y/n) ") == "y":
                            api.destroy_friendship(f)
                            print("   unfollowed!")
                            unfollowed.append(f)
                    else:
                        asktounfollow.append(f)

        if len(results)==0: howmany_results = "no one has"
        if len(results)==1: howmany_results = "1 user has"
        if len(results)>1: howmany_results = str(len(results)) + " users have"
        print( "%s been %s for %s days.." % (howmany_results, active_or_inactive, ndays) )

        if asktounfollow:
            if input( "unfollow %i? (y/n) " % len(asktounfollow) ) == "y":
                for f in asktounfollow:
                    api.destroy_friendship(f)
                    unfollowed.append(f)

        if len(unfollowed)==0: howmany_unfollowed = "no one has"
        if len(unfollowed)==1: howmany_unfollowed = "1 user has"
        if len(unfollowed)>1: howmany_unfollowed = str(len(unfollowed)) + " users have"
        print( "%s been unfollowed" % howmany_unfollowed )

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=
        ">>\"separate meat from bone\" tool for twitter, version %s by @jartigag" % __version__,
                                     usage='%(prog)s [options]')
    parser.add_argument('-c', '--confirmation', action='store_true',
                        help='ask for confirmation before each unfollow (otherwise, asked before massive unfollow after listing users)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--active', type=int, metavar='N_DAYS',
                        help='unfollow users who have been active for < N_DAYS')
    group.add_argument('-i', '--inactive', type=int, metavar='N_DAYS',
                        help='unfollow users who have been inactive for > N_DAYS')

    args = parser.parse_args()

    try:
        main()
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)
