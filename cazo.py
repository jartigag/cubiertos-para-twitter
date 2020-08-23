#!/usr/bin/env python3
#
# usage:
# python3 cazo.py

__author__ = '@jartigag'
__version__ = '0.1' # working on v0.2

# WHAT'S NEW (v0.2):
#
# + -d, --last_date_tweet: filter by last date tweet
# + secrets array of any size

#FIXME: last_date_tweet not working
#TODO: --no-twitter-list
#TODO: "x doesn't match (reason why it doesn't match)"

import tweepy
import argparse
from datetime import datetime
from time import time,sleep
from random import randrange
from tenedor import basics, over_time
import os
import logging
import sys

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
    auth = tweepy.OAuthHandler(secrets[s]['api_key'], secrets[s]['api_secret_key'])
    auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
    api = tweepy.API(auth, compression=True)
    myUsername = api.me().screen_name
    myCount = api.me().followers_count
    logger.critical("[-] hi %s! you have %i followers. let's start!" % (myUsername, myCount))

    if args.keyword:
        keywordList = args.keyword+'-'+datetime.now().strftime('%d%b%Hh')
        targetList = api.create_list(keywordList,'private')
    elif args.user:
        userFlwrsList = args.user+'-'+datetime.now().strftime('%d%b%Hh')
        targetList = api.create_list(userFlwrsList,'private')
    else:
        todayslist = 'cazo-'+datetime.now().strftime('%d%b%H:%M')
        targetList = api.create_list(todayslist,'private')

    t = 15 # secs between reqs
    n = 0

    logger.critical("[_] targeting users who match this params: ")
    for arg in vars(args):
        if vars(args)[arg] is not None:
            if type(vars(args)[arg])==int or type(vars(args)[arg])==float:
                if vars(args)[arg]>=0:
                    logger.critical(arg+': > '+str(vars(args)[arg]))
                else:
                    logger.critical(arg+': < '+str((-vars(args)[arg])))
            elif arg=='last_tweet_date':
                if arg.split()[0]=='-':
                    logger.critical(arg+': < '+str(vars(args)[arg]))
                else:
                    logger.critical(arg+': > '+str(vars(args)[arg]))
            else:
                logger.critical(arg+': "%s"' % vars(args)[arg])

    if args.keyword:
        logger.critical('[_] capturing "%s" on the fly..' % args.keyword)

    init_time = time()

    while True:
        try:
            n+=1
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

            if targetUser==myUsername: continue

            logger.warning("[%i] %s" % (n, targetUser))

            n_tweets, l_ratio, n_followers, f_ratio = basics(api, targetUser)
            logger.warning("    > checking basics params..")
            if not checkBasics(n_tweets, l_ratio, n_followers, f_ratio):
                logger.critical("    >> %s doesn't match. let's pick another target" % (targetUser))
                continue

            n_days, start_date, end_date, num_tweets, tweets_day_avg, retweets_percent = over_time(api, targetUser)
            logger.warning("    > checking params over time..")
            if not checkOverTime(tweets_day_avg, end_date, retweets_percent):
                logger.critical("    >> %s doesn't match. let's pick another target" % (targetUser))
                continue

            logger.critical("    >> %s (%.2f fwrs/fwng, %.2f tweets/day) matches required params!" % (targetUser,f_ratio,tweets_day_avg))
            #TODO: in () print required params
            api.add_list_member(list_id=targetList.id,owner_screen_name='@'+myUsername,id=targetUser)

            sleep(t)

        except tweepy.error.RateLimitError as e:

            current_time = time()
            running_time = int(current_time - init_time)

            logger.error("[#] api limit reached! %i users analysed (running time: %i secs, pauses: %i secs, secrets%i)." % (n,running_time,t,s))

            # rotate secrets[s]
            if s < len(secrets)-1:
                s+=1
            else:
                s=0

            auth = tweepy.OAuthHandler(secrets[s]['api_key'], secrets[s]['api_secret_key'])
            auth.set_access_token(secrets[s]['access_token'], secrets[s]['access_token_secret'])
            api = tweepy.API(auth, compression=True)

            n=0
            init_time = time()

        except Exception as e:
            running_time = int(time() - init_time)

            if e.args[0]=='Twitter error response: status code = 429':
                logger.error("[\033[91m!\033[0m] error: tenedor.py made too many requests.. give it a break ;).")
                logger.error("[!] error: 429. %i users analysed (running time: %i secs, pauses: %i secs)." % (n,running_time,t))
                sleep(10) # sleep(900)
            else:
                logger.error("[!] error: "+str(e))
            pass

        sleep(t)

    #TODO: guardar los ids ya analizados (primero en array, más adelante en db)
    #              y comparar antes de analizar, para evitar
    #              malgastar peticiones a la api
    #TODO: rotar entre keys para acelerar el proceso

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=
        ">> \"serve from pot to dish\"\ntool for twitter, v%s by %s" % (__version__,__author__),
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
    file_dir = "/var/log/cazo" #FIXME: i think it's more suitable, but permission error.. i'll give it a thought
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

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
        logFile.setLevel(logging.CRITICAL)
        logger.addHandler(logFile)
        formatLogFile = logging.Formatter('%(asctime)s %(message)s', datefmt='%y%m%d-%H:%M:%S')
        logFile.setFormatter(formatLogFile)
        logStderr = logging.StreamHandler(sys.stderr)
        logger.addHandler(logStderr)
        main()
