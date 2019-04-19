#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# python3 tenedor.py <screen_name> [options]

__author__ = '@jartigag'
__version__ = '0.1' # working on v0.2

# WHAT'S NEW (v0.2):
#
# + secrets array of any size

#TODO: --human descriptive inform
#TODO: send inform via dm

from tqdm import tqdm
import tweepy
import argparse
import collections
from datetime import datetime
import os
import logging

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from secrets import secrets

s = 0 # counter of the actual secret: secrets[i]

try:

    auth = tweepy.OAuthHandler(secrets[s]['consumer_key'], secrets[s]['consumer_secret'])
    auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
    api = tweepy.API(auth, compression=True)

except tweepy.error.RateLimitError as e:
        print("[\033[91m!\033[0m] api limit reached! %s" % e)

        s+=1 if s < len(secrets)-1 else 0 # rotate secrets[s]
        auth = tweepy.OAuthHandler(secrets[s]['consumer_key'], secrets[s]['consumer_secret'])
        auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
        api = tweepy.API(auth, compression=True)

# Here are globals used to store data - I know it's dirty, whatever
start_date = 0
end_date = 0

detected_hashtags = collections.Counter()
detected_domains = collections.Counter()
retweets = 0
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
    """ Processing a single Like and updating our datasets """

    try:
        # We use id to get unique accounts (screen_name can be changed)
        like_id_user = like.user.id_str
        liked_users[like_id_user] += 1

        if like.user.screen_name not in id_screen_names:
            id_screen_names[like_id_user] = "@%s" % like.user.screen_name
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
    suma = sum(list(dataset.values()))
    i = 0
    if suma:
        sorted_keys = sorted(dataset, key=dataset.get, reverse=True)
        max_len_key = max([len(x) for x in sorted_keys][:top])  # use to adjust column width
        for k in sorted_keys:
            print(("- \033[1m{:<%d}\033[0m {:>6} {:<4}" % max_len_key)
                  .format(k, dataset[k], "(%d%%)" % ((float(dataset[k]) / suma) * 100)))
            logger.info(("- {:<%d} {:>6} {:<4}" % max_len_key)
                  .format(k, dataset[k], "(%d%%)" % ((float(dataset[k]) / suma) * 100)))
            i += 1
            if i >= top:
                break
    else:
        print("no data")
    print("")

def basics(api, username):
    """ Get basic info from username account
        returns: number of tweets, likes/tweet ratio, number of followers, followers/following ratio """
    user_info = api.get_user(screen_name=username)

    return (user_info.statuses_count, float(user_info.favourites_count/user_info.statuses_count),
        user_info.followers_count, float(user_info.followers_count/user_info.friends_count))

def over_time(api, username, tweets_limit=500, likes_limit=500):
    """ Get how username tweets over time
        returns: days beetween first and last tweet (considering limit of tweets), start date, end date,
        number of tweets, tweets/day on average, %RTs """
    # get_tweets without tqdm without progress bar
    for status in tweepy.Cursor(api.user_timeline, screen_name=username).items(tweets_limit):
        process_tweet(status)

    # get_likes without tqdm without progress bar
    for status in tweepy.Cursor(api.favorites, screen_name=username).items(likes_limit):
        process_like(status)

    if tweets_limit < api.get_user(screen_name=username).statuses_count:
        num_tweets = tweets_limit
    else:
        num_tweets = api.get_user(screen_name=username).statuses_count

    tweets_day_avg = 0.00
    retweets_percent = 0.00

    if (end_date - start_date).days != 0:
        tweets_day_avg = (num_tweets / float((end_date - start_date).days))
        retweets_percent = (float(retweets) * 100 / num_tweets)

    return ((end_date - start_date).days, start_date, end_date,
        num_tweets, tweets_day_avg, retweets_percent)

def main():
    """ To run with python tenedor.py screen_name """

    print("___ getting @\033[1m%s\033[0m's data..." % args.name)
    logger.info("___ getting %s's data..." % args.name)

    n_tweets, l_ratio, n_followers, f_ratio = basics(api, args.name)

    print("[+] tweets         : \033[1m%s\033[0m" % n_tweets)
    logger.info("[+] tweets         : %s" % n_tweets)
    print("[+] likes/tw ratio : \033[1m%.2f\033[0m"% l_ratio)
    logger.info("[+] likes/tw ratio : %.2f"% l_ratio)
    print("[+] followers      : \033[1m%s\033[0m" % n_followers)
    logger.info("[+] followers      : %s" % n_followers)
    print("[+] fwrs/fwng ratio: \033[1m%.2f\033[0m"% f_ratio)
    logger.info("[+] fwrs/fwng ratio: %.2f"% f_ratio)

    # Will retreive all Tweets from account (or max limit)
    if n_tweets < args.tweets:
        num_tweets = n_tweets
    else:
        num_tweets = args.tweets
    print("___ retrieving last %d tweets..." % num_tweets)
    # Download tweets
    get_tweets(api, args.name, limit=num_tweets)
    # Will retreive all Likes from account (or max limit)
    if args.likes < int(l_ratio*n_tweets):
        num_likes = args.likes
    else:
        num_likes = int(l_ratio*n_tweets)   # l_ratio needed in other script, so
                                            # n_likes has to be calculated this way
    if num_likes != 0:
        print("___ retrieving last %d likes..." % num_likes)
        # Download likes
        get_likes(api, args.name, limit=num_likes)

    print("[+] %d tweets in  : \033[1m%d\033[0m days (from %s to %s)" %
        (num_tweets, (end_date - start_date).days, datetime.strftime(start_date, '%Y-%m-%d'), end_date))
    logger.info("[+] %d tweets in  : %d days (from %s to %s)" %
        (num_tweets, (end_date - start_date).days, datetime.strftime(start_date, '%Y-%m-%d'), end_date))

    print("                     = %d months" % ((end_date - start_date).days / 30))

    # Checking if we have enough data (considering it's good to have at least 30 days of data)
    if (end_date - start_date).days < 30 and (num_tweets < n_tweets):
         print("[*] %i tweets are not enough in this case, consider retrying (--limit)" % num_tweets)
         logger.info("[*] %i tweets are not enough in this case, consider retrying (--limit)" % num_tweets)

    if (end_date - start_date).days != 0:
        print("[+] on average     : \033[1m%.2f\033[0m tweets/day, \033[1m%.2f\033[0m %% RTs" %
         (num_tweets / float((end_date - start_date).days), float(retweets) * 100 / num_tweets))
        logger.info("[+] on average     : %.2f tweets/day, %.2f %% RTs" %
         (num_tweets / float((end_date - start_date).days), float(retweets) * 100 / num_tweets))

    print("[+] Top 10 hashtags")
    logger.info("[+] Top 10 hashtags")
    print_stats(detected_hashtags, top=10)

    # Converting users id to screen_names
    retweeted_users_names = {}
    for k in retweeted_users.keys():
        retweeted_users_names[id_screen_names[k]] = retweeted_users[k]

    liked_users_names = {}
    for k in liked_users.keys():
        liked_users_names[id_screen_names[k]] = liked_users[k]


    print("[+] top 5 most retweeted users")
    logger.info("[+] top 5 most retweeted users")
    print_stats(retweeted_users_names, top=5)

    print("[+] top 5 most liked users")
    logger.info("[+] top 5 most liked users")
    print_stats(liked_users_names, top=5)

    mentioned_users_names = {}
    for k in mentioned_users.keys():
        mentioned_users_names[id_screen_names[k]] = mentioned_users[k]
    print("[+] top 5 most mentioned users")
    logger.info("[+] top 5 most mentioned users")
    print_stats(mentioned_users_names, top=5)

    print("[+] top 5 most linked domains (from URLs)")
    logger.info("[+] top 5 most linked domains (from URLs)")
    print_stats(detected_domains, top=5)
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description= ">> \"eat one mouthful at a time\"\ntool for twitter, v%s by %s" % (__version__,__author__),
        formatter_class=argparse.RawTextHelpFormatter,
        usage='%(prog)s <screen_name> [options]')
    parser.add_argument('name', metavar="screen_name",
                        help='target screen_name')
    parser.add_argument('-g', '--group',
                        help='add the user to a group')
    parser.add_argument('-l', '--likes', type=int, default=500,
                        help='limit the number of likes to retreive (default=500)')
    parser.add_argument('-t', '--tweets', type=int, default=500,
                        help='limit the number of tweets to retreive (default=500)')

    args = parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if not os.path.exists(os.path.join(os.path.expanduser("~"), "twanalizados")):
        os.makedirs(os.path.join(os.path.expanduser("~"), "/twanalizados"))
    file_dir = os.path.join(os.path.expanduser("~"), "twanalizados")
    userFile = ""

    try:

        auth = tweepy.OAuthHandler(secrets[s]['consumer_key'], secrets[s]['consumer_secret'])
        auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
        api = tweepy.API(auth, compression=True)
        #TODO: analyze groups (from .txt, from fwing, from flwrs, from lists). print stats (avg, distrib, most freq)
        if args.name==".":
            following = []
            n = 0
            myUsername = api.me().screen_name
            print("[-] hi %s! getting your following.." % myUsername)
            for page in tweepy.Cursor(api.friends_ids, screen_name=myUsername).pages():
                following.extend(page)
                if n==1:            print("-- you follow +5k. retreiving them in pages..")
                if n>0:             print("-- [+] page " + str(n))
                if len(page)==5000: n += 1
            print("[_] " + str(len(following)) + " following")
            if args.group:
                if not os.path.exists("{}/{}".format(file_dir, args.group)):
                        os.makedirs("{}/{}".format(file_dir, args.group))
                file_dir = os.path.join(file_dir, args.group)
            i = 1
            for f in following:
                retweets = 0
                args.name = api.get_user(f).screen_name
                print("[\033[92m%i\033[0m]"%i)
                print("___ @%s added to group [\033[1m%s\033[0m]" % (args.name, args.group))
                if userFile: logger.removeHandler(userFile)  # to avoid including previous logs in each userFile
                userFile = logging.FileHandler(os.path.join(file_dir, datetime.now().strftime('%y%m%d') + "-" + args.name + ".txt"))
                logger.addHandler(userFile)
                try:
                    main()
                except Exception as e:
                    pass
                i += 1
            print("[_] " + str(len(following)) + " analyzed")

        else:

            if args.group:
                file_dir = os.path.join(file_dir, args.group)
                print("___ @%s added to group [\033[1m%s\033[0m]" % (args.name, args.group))
            userFile = logging.FileHandler(os.path.join(file_dir, datetime.now().strftime('%y%m%d') + "-" + args.name + ".txt"))
            logger.addHandler(userFile)
            main()

    except tweepy.error.RateLimitError as e:
        print("[\033[91m!\033[0m] api limit reached! %s" % e)

        s+=1 if s < len(secrets)-1 else 0 # rotate secrets[s]
        auth = tweepy.OAuthHandler(secrets[s]['consumer_key'], secrets[s]['consumer_secret'])
        auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
        api = tweepy.API(auth, compression=True)

    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
        logger.error("[!] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)
        logger.error("[!] error: %s" % e)
