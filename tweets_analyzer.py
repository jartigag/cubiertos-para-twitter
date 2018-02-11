#!/usr/bin/env python
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
# based on tweets_analyzer by @x0rz
# 
# Usage:
# python tweets_analyzer.py -n screen_name
#
# Install:
# pip install tweepy tqdm numpy

from __future__ import unicode_literals

from tqdm import tqdm
import tweepy
import numpy
import argparse
import collections
import datetime
import os
import logging

__version__ = '0.1'

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from secrets2 import consumer_key, consumer_secret, access_token, access_token_secret

parser = argparse.ArgumentParser(description=
    "analyze twitter profiles, version %s" % __version__,
                                 usage='%(prog)s -n <screen_name> [options]')
parser.add_argument('name', metavar="screen_name",
                    help='target screen_name')
parser.add_argument('-g', '--group', metavar='N',
                    help='add the user to a group')
parser.add_argument('-l', '--likes', metavar='N', type=int, default=500,
                    help='limit the number of likes to retreive (default=500)')
parser.add_argument('-t', '--tweets', metavar='N', type=int, default=500,
                    help='limit the number of tweets to retreive (default=500)')

args = parser.parse_args()

# Here are globals used to store data - I know it's dirty, whatever
start_date = 0
end_date = 0

detected_hashtags = collections.Counter()
detected_domains = collections.Counter()
retweets = 0
likes = 0
retweeted_users = collections.Counter()
liked_users = collections.Counter()
mentioned_users = collections.Counter()
id_screen_names = {}

def process_tweet(tweet):
    """ Processing a single Tweet and updating our datasets """
    global start_date
    global end_date
    global retweets

    tw_date = tweet.created_at

    # Updating most recent tweet
    end_date = end_date or tw_date
    start_date = tw_date

    # Handling retweets
    try:
        # We use id to get unique accounts (screen_name can be changed)
        rt_id_user = tweet.retweeted_status.user.id_str
        retweeted_users[rt_id_user] += 1

        if tweet.retweeted_status.user.screen_name not in id_screen_names:
            id_screen_names[rt_id_user] = "@%s" % tweet.retweeted_status.user.screen_name

        retweets += 1
    except:
        pass

    # Updating hashtags list
    if tweet.entities['hashtags']:
        for ht in tweet.entities['hashtags']:
            ht['text'] = "#%s" % ht['text']
            detected_hashtags[ht['text']] += 1

    # Updating domains list
    if tweet.entities['urls']:
        for url in tweet.entities['urls']:
            domain = urlparse(url['expanded_url']).netloc
            if domain != "twitter.com":  # removing twitter.com from domains (not very relevant)
                detected_domains[domain] += 1

    # Updating mentioned users list
    if tweet.entities['user_mentions']:
        for ht in tweet.entities['user_mentions']:
            mentioned_users[ht['id_str']] += 1
            if not ht['screen_name'] in id_screen_names:
                id_screen_names[ht['id_str']] = "@%s" % ht['screen_name']

def process_like(like):
    """ Processing a single Tweet and updating our datasets """
    #global start_date
    #global end_date
    global likes

    #tw_date = tweet.created_at

    # Updating most recent tweet
    #end_date = end_date or tw_date
    #start_date = tw_date

    try:
        # We use id to get unique accounts (screen_name can be changed)
        like_id_user = like.user.id_str
        liked_users[like_id_user] += 1

        if like.user.screen_name not in id_screen_names:
            id_screen_names[like_id_user] = "@%s" % like.user.screen_name

        likes += 1
    except:
        pass

def get_tweets(api, username, limit):
    """ Download Tweets from username account """
    for status in tqdm(tweepy.Cursor(api.user_timeline, screen_name=username).items(limit),
                       unit="tw", total=limit):
        process_tweet(status)

def get_likes(api, username, limit):
    """ Download Likes from username account """
    for status in tqdm(tweepy.Cursor(api.favorites, screen_name=username).items(limit),
                       unit="lk", total=limit):
        process_like(status)

def print_stats(dataset, top=5):
    """ Displays top values by order """
    sum = numpy.sum(list(dataset.values()))
    i = 0
    if sum:
        sorted_keys = sorted(dataset, key=dataset.get, reverse=True)
        max_len_key = max([len(x) for x in sorted_keys][:top])  # use to adjust column width
        for k in sorted_keys:
            try:
                print(("- \033[1m{:<%d}\033[0m {:>6} {:<4}" % max_len_key)
                      .format(k, dataset[k], "(%d%%)" % ((float(dataset[k]) / sum) * 100)))
                logger.warning(("- {:<%d} {:>6} {:<4}" % max_len_key)
                      .format(k, dataset[k], "(%d%%)" % ((float(dataset[k]) / sum) * 100)))
            except:
                import ipdb
                ipdb.set_trace()
            i += 1
            if i >= top:
                break
    else:
        print("no data")
    print("")

def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    twitter_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

    # Getting general account's metadata
    print("___ getting @\033[1m%s\033[0m's data..." % args.name)
    logger.warning("___ getting %s's data..." % args.name)
    user_info = twitter_api.get_user(screen_name=args.name)
    print("[+] tweets         : \033[1m%s\033[0m" % user_info.statuses_count)
    logger.warning("[+] tweets         : %s" % user_info.statuses_count)
    print("[+] tws/likes ratio: \033[1m%.2f\033[0m"% (float(user_info.statuses_count)/user_info.favourites_count))
    logger.warning("[+] tws/likes ratio: %.2f"% (float(user_info.statuses_count)/user_info.favourites_count))
    print("[+] followers      : \033[1m%s\033[0m" % user_info.followers_count)
    logger.warning("[+] followers      : %s" % user_info.followers_count)
    print("[+] fwrs/fwng ratio: \033[1m%.2f\033[0m"% (float(user_info.followers_count)/user_info.friends_count))
    logger.warning("[+] fwrs/fwng ratio: %.2f"% (float(user_info.followers_count)/user_info.friends_count))

    # Will retreive all Tweets from account (or max limit)
    num_tweets = numpy.amin([args.tweets, user_info.statuses_count])
    print("___ retrieving last %d tweets..." % num_tweets)
    # Download tweets
    get_tweets(twitter_api, args.name, limit=num_tweets)
    # Will retreive all Likes from account (or max limit)
    num_likes = numpy.amin([args.likes, user_info.favourites_count])
    print("___ retrieving last %d likes..." % num_likes)
    # Download likes
    get_likes(twitter_api, args.name, limit=num_likes) # WARNING! rate limit easily exceeded

    print("[+] %d tweets in:   \033[1m%d\033[0m days (from %s to %s)" % (num_tweets, (end_date - start_date).days, start_date, end_date))
    logger.warning("[+] %d tweets in:   %d days (from %s to %s)" % (num_tweets, (end_date - start_date).days, start_date, end_date))
    print("                     \033[1m%.2f\033[0m %% RTs" % (float(retweets) * 100 / num_tweets))
    logger.warning("                     %.2f %% RTs" % (float(retweets) * 100 / num_tweets))
    #print("                     \033[1m%.2f\033[0m %% likes" % (float(likes) * 100 / (num_tweets+num_likes))) #this metric need to be redesigned..

    # Checking if we have enough data (considering it's good to have at least 30 days of data)
    if (end_date - start_date).days < 30 and (num_tweets < user_info.statuses_count):
         print("[\033[91m!\033[0m] not enough tweets from user, consider retrying (--limit)")
         logger.warning("[!] not enough tweets from user, consider retrying (--limit)")

    if (end_date - start_date).days != 0:
        print("[+] on average:      \033[1m%.2f\033[0m tweets/day" % (num_tweets / float((end_date - start_date).days)))
        logger.warning("[+] on average:      %.2f tweets/day" % (num_tweets / float((end_date - start_date).days)))
        print("                     \033[1m%.2f\033[0m likes/day" % (likes / float((end_date - start_date).days)))
        logger.warning("                     %.2f  likes/day" % (likes / float((end_date - start_date).days)))

    print("[+] Top 10 hashtags")
    logger.warning("[+] Top 10 hashtags")
    print_stats(detected_hashtags, top=10)

    # Converting users id to screen_names
    retweeted_users_names = {}
    for k in retweeted_users.keys():
        retweeted_users_names[id_screen_names[k]] = retweeted_users[k]

    liked_users_names = {}
    for k in liked_users.keys():
        liked_users_names[id_screen_names[k]] = liked_users[k]


    print("[+] top 5 most retweeted users")
    logger.warning("[+] top 5 most retweeted users")
    print_stats(retweeted_users_names, top=5)

    print("[+] top 5 most liked users")
    logger.warning("[+] top 5 most liked users")
    print_stats(liked_users_names, top=5)

    mentioned_users_names = {}
    for k in mentioned_users.keys():
        mentioned_users_names[id_screen_names[k]] = mentioned_users[k]
    print("[+] top 5 most mentioned users")
    logger.warning("[+] top 5 most mentioned users")
    print_stats(mentioned_users_names, top=5)

    print("[+] top 5 most linked domains (from URLs)")
    logger.warning("[+] top 5 most linked domains (from URLs)")
    print_stats(detected_domains, top=5)

if __name__ == '__main__':
    
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    file_dir = os.path.join(os.path.expanduser("~"), "analizados")
    if args.group:
        group_dir = os.path.join(file_dir, args.group)
        print("___ @%s added to group [\033[1m%s\033[0m]" % (args.name, args.group))
        logFile = logging.FileHandler(os.path.join(group_dir, args.name + ".txt"))
    else:
        logFile = logging.FileHandler(os.path.join(file_dir, args.name + ".txt"))
    logFile.setLevel(logging.WARNING)
    logger.addHandler(logFile)

    try:
        #TODO: pick users from list, analyze and send inform via dm
        main()
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
        logger.error("[!] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)
        logger.error("[!] twitter error: %s" % e)
