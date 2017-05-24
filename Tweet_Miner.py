#Created by Nicholas Leer

#!/usr/bin/env python
# encoding: utf-8

import tweepy #https://github.com/tweepy/tweepy
import csv
import urllib2
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#Twitter API credentials
consumer_key = "***"
consumer_secret = "***"
access_key = "***"
access_secret = "***"

#User Input Varriables 
title = "Google Sheet Title"
handle = "Twitter Handle"

#Function to show whether the tweet pulled is a retweet or not
def get_retweet(twit):
    try:
        if twit.retweeted_status:
            return twit.retweeted_status.text
        else:
            return ''
    except:
        return ''

def combine_retweet(orig, retwit):
    if len(retwit)>0:
        return orig[:orig.find(retwit[:10])]+retwit
    else:
        return orig
def get_all_tweets(screen_name):
    #Twitter only allows access to a users most recent 3240 tweets with this method
    
    #authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('Location of json file', scope)
    client = gspread.authorize(creds)

    #initialize a list to hold all the tweepy Tweets
    alltweets = []

    #Opens Google sheet and sets since_id to most recent tweet ID on sheet
    sheet = client.open(title).sheet1
    first_cell = sheet.cell(2,1)
    
    #print new_id
    #return
    new_id = 1
    gvalues = sheet.get_all_values()
    gvalues.pop(0)
    for row in gvalues:
        row[0] = "'"+row[0]
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,since_id=new_id,count=3240,include_rts=True)

    #save most recent tweets
    alltweets.extend(new_tweets)

    #appends tweets when saved
    #[alltweets.append(i) for i in new_tweets]

    #save the id of the oldest tweet less one
    try:
        oldest = alltweets[-1].id - 1
    except:
        print("No new tweets to grab")
        return

    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:

        print("getting tweets after %s" % (new_id))
        
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=3240,since_id=new_id,max_id=oldest,include_rts=True)
        
        #save most recent tweets
        alltweets.extend(new_tweets)
        
        #update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        
        print("...%s tweets downloaded so far" % (len(alltweets)))

    #transform the tweepy tweets into a 2D array that will populate the tab file	
    #NO PROGRESS BAR

    #Updates tweets
    existing = sheet.col_values(1)
    for tweet in reversed(alltweets):
        if str(tweet.id) in existing:
            print("Tweet already in Sheet %s" % str(tweet.id))
        else:
            cell_list = ["'"+str(tweet.id),tweet.created_at.strftime("%a, %d %b %Y %H:%M:%S"),combine_retweet(tweet.text,get_retweet(tweet)),tweet.favorite_count,str(tweet.retweet_count),""]
            gvalues.insert(0,cell_list)
            print("adding tweet %s" % (tweet.id))
    sheet.resize(len(gvalues)+1,6)
    updatedcells = sheet.range(2,1,len(gvalues)+1,5)
    x=0
    y=0
    for cell in updatedcells:
        cell.value = gvalues[x][y]
        y+=1
        if y>=5:
            y=0
            x+=1
    sheet.update_cells(updatedcells)
    print("successful")
pass
if __name__ == '__main__':
	#pass in the username of the account you want to download
	get_all_tweets(handle)
