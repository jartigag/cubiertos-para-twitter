#!/usr/bin/env python3
#
# usage:
# python3 cuchillo.py [options]

__author__ = '@jartigag'
__version__ = '0.1' # working on v0.2

# WHAT'S NEW (v0.2):
#
# - before unfollowing someone, show his info, bio and date/fragment of last tweet
# - add to whitelist from "unfollow? (y/n/w[hitelist])"

#TODO: filter by params
#TODO: monthly clean-up: check whitelist, list who you don't interact with
#      maybe twenedor will print 'in whitelist' (especially if you run it with '.' arg)

import argparse
import tweepy
import json
from datetime import datetime, timedelta
from tenedor import basics, over_time
import os
import logging

from secrets import secrets

WHITELIST_FILE = os.path.join(os.path.expanduser("~"), ".config/cuchillo/whitelist.json")

def last_date_tweeted(api, id):
    global last_date
    tweet = api.user_timeline(id = id, count = 1)[0]
    if tweet:
        last_date = tweet.created_at
    return last_date

#TODO: last_date_liked
#
#def last_date_liked(api, id):
#    global last_date
#    status = api.favorites(id=id, count=1)[0]
#    # 2 options
#       - get last like date
#       - store number of likes, compare with actual number of likes
#    return last_date

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

def whitelist(auth, api, username):
    with open(WHITELIST_FILE, encoding="utf-8") as file:
        whitelist = json.load(file)
        id = api.get_user(screen_name=username).id
        whitelist.append(id)
        with open(WHITELIST_FILE, "w", encoding="utf-8") as outfile:
            json.dump(whitelist, outfile)
            outfile.write("\n")
            print("       %s (id=%s) added to whitelist" % (username,id))

def main(auth, api):

    myUsername = api.me().screen_name
    print("[-] hi %s! getting your following and followers.." % myUsername)

    logger.warning(myUsername+" - "+datetime.now().strftime('%Y %b %d - %H:%M'))

    following = []
    n = 0
    for page in tweepy.Cursor(api.friends_ids, screen_name=myUsername).pages():
        following.extend(page)
        if n==1:            print("-- you follow +5k. retreiving them in pages..")
        if n>0:             print("-- [+] page " + str(n))
        if len(page)==5000: n += 1
    print("[_] " + str(len(following)) + " following")
    logger.warning("[_] " + str(len(following)) + " following")

    followers = []
    m = 0
    for page in tweepy.Cursor(api.followers_ids, screen_name=myUsername).pages():
        followers.extend(page)
        if m==1:            print("-- you have +5k followers. retreiving them in pages..")
        if m>0:             print("-- [+] page " + str(m))
        if len(page)==5000: m += 1
    print("[_] " + str(len(followers)) + " followers")
    logger.warning("[_] " + str(len(followers)) + " followers")

    fratio = float(len(followers)/len(following))
    print(" >> ratio fwrs/fwng: \033[1m%.2f\033[0m" % fratio)
    logger.warning(" >> ratio fwrs/fwng: %.2f" % fratio)

    # WHITELIST filter:
    afterWL = []
    for f in following:
        with open(WHITELIST_FILE, encoding="utf-8") as file:
            whitelist = json.load(file)
            if f not in whitelist: afterWL.append(f)

    # FOLLOWBACK filter:
    nonreciprocals = list(set(afterWL) - set(followers))

    if len(nonreciprocals)==0:
        return
    else:
        activity(api, nonreciprocals, auth)

    fratio_new = float(api.get_user(screen_name=myUsername).followers_count/api.get_user(screen_name=myUsername).friends_count)
    if fratio_new-fratio!=0:
        print(" >> your ratio fwrs/fwng has changed to: %.2f ( +\033[1m%.2f\033[0m)" % (fratio_new, fratio_new-fratio))
        logger.warning(" >> your ratio fwrs/fwng has changed to: %.2f ( +%.2f)" % (fratio_new, fratio_new-fratio))
def activity(api, nonreciprocals, auth):
    # ACTIVITY filter:
    results = []
    asktounfollow = []
    unfollowed = []

    if args.active:
        active_or_inactive = "active"
        ndays=args.active
    if args.inactive:
        active_or_inactive = "inactive"
        ndays=args.inactive
    if len(nonreciprocals)==1: howmany_nonreciprocals = "1 non-reciprocal user has"
    if len(nonreciprocals)>1:  howmany_nonreciprocals = str(len(nonreciprocals)) + " non-reciprocal users have"
    print( "[_] checking if %s been %s for %s days.." % (howmany_nonreciprocals, active_or_inactive, ndays) )

    for f in nonreciprocals:
        if args.active:
            if last_date_tweeted(api, f) + timedelta(days=ndays) > datetime.today():
                screen_name = api.get_user(f).screen_name
                print("\n    >> @\033[1m%s\033[0m has been %s." % (screen_name, active_or_inactive) )
                results.append(f)
            #elif has_liked(api, f) < datetime.today() - timedelta(days=ndays): actives.append(f)
                if args.confirmation:
                    nofbuser = api.get_user(f)
                    print("       %s (%s fwrs, %s tws). bio:\n\033[1m«\033[0m%s\033[1m»\033[0m" % (nofbuser.name,nofbuser.followers_count,nofbuser.statuses_count,nofbuser.description))
                    creation_moment = nofbuser.status.created_at.strftime("%Y-%m-%d %H:%M:%S").split(' ')
                    creation_date = creation_moment[0].split('-')
                    creation_day = '-'.join([creation_date[1],creation_date[2]])
                    creation_time = creation_moment[1].split(':')
                    creation_hour = ':'.join([creation_time[0],creation_time[1]])
                    print("       last tweet (on %s-\033[1m%s\033[0m \033[1m%s\033[0m:%s):\n\033[1m«\033[0m%s\033[1m»\033[0m\n" % (creation_date[0],creation_day,creation_hour,creation_time[2],nofbuser.status.text))
                    ans = input( "    unfollow? (y/N/w[hitelist]) ")
                    if ans == "y":
                        api.destroy_friendship(f)
                        unfollowed.append(f)
                        print("       @%s has been unfollowed" % (screen_name))
                    elif ans == "w":
                        whitelist(auth, api, nofbuser.screen_name)
                    else:
                        print("       @%s hasn't been unfollowed" % (screen_name))
                else:
                    asktounfollow.append(nofbuser)

        if args.inactive:
            if last_date_tweeted(api, f) + timedelta(days=ndays) < datetime.today():
                print("    >> @\033[1m%s\033[0m has been %s." % (api.get_user(f).screen_name, active_or_inactive) )
                results.append(f)
                if args.confirmation:
                    nofbuser = api.get_user(f)
                    print("       %s (%s fwrs, %s tws). bio:\n\033[1m«\033[0m%s\033[1m»\033[0m" % (nofbuser.name,nofbuser.followers_count,nofbuser.statuses_count,nofbuser.description))
                    creation_moment = nofbuser.status.created_at.strftime("%Y-%m-%d %H:%M:%S").split(' ')
                    creation_date = creation_moment[0].split('-')
                    creation_day = '-'.join([creation_date[1],creation_date[2]])
                    creation_time = creation_moment[1].split(':')
                    creation_hour = ':'.join([creation_time[0],creation_time[1]])
                    print("       last tweet (on %s-\033[1m%s\033[0m \033[1m%s\033[0m:%s):\n\033[1m«\033[0m%s\033[1m»\033[0m\n" % (creation_date[0],creation_day,creation_hour,creation_time[2],nofbuser.status.text))
                    ans = input( "    unfollow? (y/n/w[hitelist]) ")
                    if ans == "y":
                        api.destroy_friendship(f)
                        unfollowed.append(f)
                    elif ans == "w":
                        whitelist(auth, api, nofbuser.screen_name)
                else:
                    asktounfollow.append(f)

    if len(results)==0: howmany_results = "no one has"
    if len(results)==1: howmany_results = "1 user has"
    if len(results)>1: howmany_results = str(len(results)) + " users have"
    print( " >> %s been %s for %s days.." % (howmany_results, active_or_inactive, ndays) )
    logger.warning( " >> %s been %s for %s days.." % (howmany_results, active_or_inactive, ndays) )

    if asktounfollow:
        if input( "    unfollow %i? (y/n) " % len(asktounfollow) ) == "y":
            for f in asktounfollow:
                api.destroy_friendship(f)
                unfollowed.append(f)

    if len(unfollowed)==0: howmany_unfollowed = "no one has"
    if len(unfollowed)==1: howmany_unfollowed = "1 user has"
    if len(unfollowed)>1: howmany_unfollowed = str(len(unfollowed)) + " users have"
    print( " >> %s been unfollowed" % howmany_unfollowed )
    logger.warning( " >> %s been unfollowed" % howmany_unfollowed )

    # info collected in logger: datetime - followers, following, f_ratio, unfollows
    logger.warning("")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=
        ">> \"separate meat from bone\"\ntool for twitter, v%s by %s" % (__version__,__author__),
        formatter_class=argparse.RawTextHelpFormatter,
        usage='%(prog)s [options]')
    parser.add_argument('-c', '--confirmation', action='store_true',
                        help='ask for confirmation before each unfollow (otherwise, asked before massive unfollow after listing users)')

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

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--active', type=int, metavar='N_DAYS',
                        help='unfollow users who have been active for < N_DAYS')
    group.add_argument('-i', '--inactive', type=int, metavar='N_DAYS',
                        help='unfollow users who have been inactive for > N_DAYS')
    group.add_argument('-w', '--add_to_whitelist', metavar='USERNAME',
                        help='add USERNAME to whitelist')

    args = parser.parse_args()

    logger = logging.getLogger()
    if not os.path.exists(os.path.join(os.path.expanduser("~"), ".config/cuchillo")):
        os.makedirs(os.path.join(os.path.expanduser("~"), ".config/cuchillo"))
    file_dir = os.path.join(os.path.join(os.path.expanduser("~"), ".config/cuchillo"))
    logFile = os.path.join(file_dir,"cuchillo.log")
    logging.basicConfig(filename=logFile,
                            filemode='a',
                            level=logging.WARNING,
                            format='%(asctime)s %(message)s', datefmt='%y%m%d-%H:%M:%S')
    if not os.path.isfile(WHITELIST_FILE):
        with open(WHITELIST_FILE, "w", encoding="utf-8") as file:
            json.dump([], file)
            file.write("\n")

    try:
        auth = tweepy.OAuthHandler(secrets[0]['api_key'], secrets[0]['api_secret_key'])
        auth.set_access_token(secrets[0]['access_token'], secrets[0]['access_token_secret'])
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
        if args.add_to_whitelist:
            whitelist(auth, api, args.add_to_whitelist)
            n_args = sum([1 for arg in vars(args).values() if arg])
            if n_args > 1:
                print("[only -w USERNAME arg is considered, other %i args are nosense here]" % (n_args-1))
        else:
            main(auth, api)
    except tweepy.error.TweepError as e:
        print("[\033[91m!\033[0m] twitter error: %s" % e)
    except Exception as e:
        print("[\033[91m!\033[0m] error: %s" % e)
