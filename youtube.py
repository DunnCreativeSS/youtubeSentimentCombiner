import json
import sys
from urllib import *
import argparse
from urllib.parse import urlparse, urlencode, parse_qs
from urllib.request import  urlopen
import logging
import praw
from time import sleep 
from gensim import models
from gensim.models import Word2Vec as word2vec
from cltk.vector.word2vec import get_sims
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from scipy import spatial
from gensim.models import Word2Vec
from sklearn.ensemble import RandomForestClassifier
from difflib import SequenceMatcher

mykey = "AIzaSyCJHFzjEF_2gMG4n2_bSsoELD28VEVgkGA"

import time
YOUTUBE_COMMENT_URL = 'https://www.googleapis.com/youtube/v3/commentThreads'
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

parser = argparse.ArgumentParser()

import time
from pprint import pprint
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.sentiment.vader import SentiText
from nltk import tokenize
import ssl
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

r = praw.Reddit(client_id='isH6FnlKKpE4ZA',
                     client_secret="S8LW-ewauj5wGMMJTpUUoqzLAr8", password='w0rdp4ss',
                     user_agent='USERAGENT', username='h3xadecimal138')


scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('googlesheets.json', scope)

gc = gspread.authorize(credentials)

posSheet = gc.open("Reddit Randoms").worksheet('YouTube Positives')
negSheet = gc.open("Reddit Randoms").worksheet('YouTube Negatives')
ratio = SequenceMatcher(None, 'this is how we do you know', 'know you how we do this').ratio()
print(ratio)



def generatesentiment(k, text):
    sid = SentimentIntensityAnalyzer()
    score = sid.polarity_scores(text)
    sentiment = {
        k: text,
        "sentiment": score,
        "v_neg": [],
        "s_neg": [],
        "v_pos": [],
        "s_pos": []
    }

    sentitext = SentiText(text).words_and_emoticons

    for i, w in enumerate(sentitext):
        w_lower = w.lower()
        if w_lower in sid.lexicon:
            score = sid.lexicon[w_lower]
            word_obj = {"word": w, "score": score}
            if score <= -2.4:
                sentiment["v_neg"].append(word_obj)
            elif score <= -0.8:
                sentiment["s_neg"].append(word_obj)
            elif score >= 2.4:
                sentiment["v_pos"].append(word_obj)
            elif score >= 0.8:
                sentiment["s_pos"].append(word_obj)

    return sentiment 
positives = []
negatives = []

args = parser.parse_args()
noMoarLoad = False
def load_comments(mat):
    if len(positives)>110:
        doSheet()
    else:
        for item in mat["items"]:
            comment = item["snippet"]["topLevelComment"]
            author = comment["snippet"]["authorDisplayName"]
            text = comment["snippet"]["textDisplay"]
            if 'replies' in item.keys():
                for reply in item['replies']['comments']:
                    rauthor = reply['snippet']['authorDisplayName']
                    text = text + "\n" + reply["snippet"]["textDisplay"]
            splits = text.split('\n')
            splits = list(filter(None, splits))
            sentiments = [generatesentiment("split", split) for split in splits]
            for sentiment in sentiments:
                compound = (sentiment['sentiment']['compound'])
                if compound > 0.3:
                    lower = sentiment['split'].lower()#.replace('bitcoin', '[[our coin]]').replace('btc', '[[our ticker]]')
                    if not lower.startswith('>') and not lower.startswith('**') and not lower.startswith('##')and not lower.startswith('[http'):
                        positives.append(lower)
                        #print(len(positives))
                if compound < -0.3:
                    lower = sentiment['split'].lower()#.replace('bitcoin', '[[our coin]]').replace('btc', '[[our ticker]]')
                    if not lower.startswith('>') and not lower.startswith('**') and not lower.startswith('##')and not lower.startswith('[http'):
                        negatives.append(lower)
                        print(len(negatives))
                    
posChoices = []
negChoices = []
def posF(n: int, C: list) -> list:
    choice = random.choice (positives)
    if choice not in posChoices:
        posChoices.append(choice)
        C.append(choice)
        n = n - 1
    if n >= 0:
        return posF(n, C)
    else:
        return C
def negF(n: int, C: list) -> list:
    choice = random.choice (negatives)
    if choice not in negChoices:
        negChoices.append(choice)
        C.append(choice)
        n = n - 1
    if n >= 0:
        return posF(n, C)
    else:
        return C
def get_video_comment(url):

    if len(positives)>110:
        doSheet()
    else:
        parser = argparse.ArgumentParser()
        mxRes = 20
        vid = str()
        parser.add_argument("--c", help="calls comment function by keyword function", action='store_true')
        parser.add_argument("--max", help="number of comments to return", default="50")
        parser.add_argument("--videourl", help="Required URL for which comments to return", default=url)
        parser.add_argument("--key", help="Required API key", default=mykey)

        args = parser.parse_args()

        if not args.max:
            args.max = mxRes

        if not args.videourl:
            exit("Please specify video URL using the --videourl=parameter.")

        if not args.key:
            exit("Please specify API key using the --key=parameter.")

        try:
            video_id = urlparse(str(args.videourl))
            q = parse_qs(video_id.query)
            vid = q["v"][0]

        except:
            print("Invalid YouTube URL")

        parms = {
                    'part': 'snippet,replies',
                    'maxResults': args.max,
                    'videoId': vid,
                    'textFormat': 'plainText',
                    'key': args.key
                }

        try:
            
            matches = openURL(YOUTUBE_COMMENT_URL, parms)
            i = 2
            mat = json.loads(matches)
            nextPageToken = mat.get("nextPageToken")
            if noMoarLoad is False:
                load_comments(mat)
            
            while nextPageToken:
                if len(positives)>110:
                    doSheet()
                else:
                    parms.update({'pageToken': nextPageToken})
                    matches = openURL(YOUTUBE_COMMENT_URL, parms)
                    mat = json.loads(matches)
                    nextPageToken = mat.get("nextPageToken")
                    if noMoarLoad is False:
                        load_comments(mat)
                    print('get_video_comment i: ' + str(i))
                    i += 1

        except KeyboardInterrupt:
            print("User Aborted the Operation")

        except Exception as e:
            print(e)
            print("Cannot Open URL or Fetch comments at a moment")
def load_search_res(search_response):
    if len(positives)>110:
        doSheet()
    else:
        videos, channels, playlists = [], [], []
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
              videos.append("{} ({})".format(search_result["snippet"]["title"],
                                         search_result["id"]["videoId"]))
              if noMoarLoad == False:
                get_video_comment('https://www.youtube.com/watch?v='+search_result["id"]["videoId"])
            elif search_result["id"]["kind"] == "youtube#channel":
              channels.append("{} ({})".format(search_result["snippet"]["title"],
                                           search_result["id"]["channelId"]))
            elif search_result["id"]["kind"] == "youtube#playlist":
              playlists.append("{} ({})".format(search_result["snippet"]["title"],
                                search_result["id"]["playlistId"]))
        
    #print("Videos:\n", "\n".join(videos), "\n")
    #print("Channels:\n", "\n".join(channels), "\n")
    #print("Playlists:\n", "\n".join(playlists), "\n")

doneSheet = False


def avg_feature_vector(sentence, model, num_features, index2word_set):
    words = sentence.split()
    feature_vec = np.zeros((num_features, ), dtype='float32')
    n_words = 0
    for word in words:
        if word in index2word_set:
            n_words += 1
            feature_vec = np.add(feature_vec, model[word])
    if (n_words > 0):
        feature_vec = np.divide(feature_vec, n_words)
    return feature_vec

def doSheet():
    global doneSheet
    if doneSheet is False:
        doneSheet = True;
        print('positive sentences last 100 posts in /r/bitcoin: ' + str(len(positives)))
        print('negative sentences last 100 posts in /r/bitcoin: ' + str(len(negatives)))
        for n in range(15):

            empty = []
            poses = int(len(positives) / 10)
            if poses > 3:
                poses = 3
            posC = posF(poses, empty)
            posPara = ""
            for choice in posC:
                posPara = posPara + choice + " "
            posArray = []
            subreddit = r.subreddit('bitoin')
            sims = []
            posParas = []
            submissions = []
            for submission in subreddit.hot(limit=1000):
                submissions.append(submission)
                text = (vars(submission)['selftext'])
                ratio = SequenceMatcher(None, text, posPara).ratio()
                sims.append(ratio)
                posParas.append(posPara)
        highest = 0
        count = 0
        finalPosPara = ""
        submmission = praw.models.Submission
        for sim in sims:
            count = count + 1
            if sim > highest:
                highest = sim
                submission = submissions[count]
                finalPosPara = posParas[count]
        print('highest:' + str(highest))
        submission.reply(finalPosPara)
        

def openURL(url, parms):
    f = urlopen(url + '?' + urlencode(parms))
    data = f.read()
    f.close()
    matches = data.decode("utf-8")
    return matches
try:
    parms = {'q': 'bitoin', 'part':'snippet', 'maxResults':"1", 'regionCode': 'US', 'key': mykey}
    if len(positives)>110:
        doSheet()
    else:
        matches = openURL(YOUTUBE_SEARCH_URL, parms)
        search_response = json.loads(matches)
        i = 2
        print(search_response)
        nextPageToken = search_response.get("nextPageToken")
        print(nextPageToken)
        load_search_res(search_response)

        while nextPageToken:
            if len(positives)>110:
                doSheet()
            else:    
                parms.update({'pageToken': nextPageToken})
                matches = openURL(YOUTUBE_SEARCH_URL, parms)

                search_response = json.loads(matches)
                nextPageToken = search_response.get("nextPageToken")

                load_search_res(search_response)
                print('load_search_res: ' + str(i))
                i += 1
             

except KeyboardInterrupt:
    print("User Aborted the Operation")

except Exception as e:
    print(e)
    print("Cannot Open URL or Fetch comments at a moment")
