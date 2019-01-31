import json
import sys
from urllib import *
import argparse
from urllib.parse import urlparse, urlencode, parse_qs
from urllib.request import  urlopen
import logging
mykey = "AIzaSyDr6Uf5m9A5BuVYLZ6-DKxkis4rZX528OM"
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.debug("This is a debug log")
logger.info("This is an info log")
logger.critical("This is critical")
logger.error("An error occurred")
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

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('googlesheets.json', scope)

gc = gspread.authorize(credentials)

posSheet = gc.open("Reddit Randoms").worksheet('YouTube Positives')
negSheet = gc.open("Reddit Randoms").worksheet('YouTube Negatives')



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
    if len(negatives)>60:
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
                if compound > 0.6:
                    lower = sentiment['split'].lower().replace('bitcoin', '[[our coin]]').replace('btc', '[[our ticker]]')
                    if not lower.startswith('>') and not lower.startswith('**') and not lower.startswith('##')and not lower.startswith('[http'):
                        positives.append(lower)
                        print(len(positives))
                if compound < -0.6:
                    lower = sentiment['split'].lower().replace('bitcoin', '[[our coin]]').replace('btc', '[[our ticker]]')
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

    if len(negatives)>60:
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
                if len(negatives)>60:
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
    if len(negatives)>60:
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
def doSheet():
    global doneSheet
    if doneSheet is False:
        doneSheet = True;
        print('positive sentences last 100 posts in /r/bitcoin: ' + str(len(positives)))
        print('negative sentences last 100 posts in /r/bitcoin: ' + str(len(negatives)))
        for n in range(10):

            empty = []
            poses = int(len(positives) / 10)
            if poses > 6:
                poses = 6
            posC = posF(poses, empty)
            posPara = ""
            for choice in posC:
                posPara = posPara + choice + " "
            posArray = []
            posArray.append(posPara)
            posSheet.append_row(posArray)
            
            neges = int(len(negatives) / 10)
            if neges > 6:
                 neges = 6
            empty = []
            negC = negF(neges, empty)

            negPara = ""
            for choice in negC:
                negPara = negPara + choice + " "
            negArray = []
            negArray.append(negPara)
            negSheet.append_row(negArray)
def openURL(url, parms):
    f = urlopen(url + '?' + urlencode(parms))
    data = f.read()
    f.close()
    matches = data.decode("utf-8")
    return matches
try:
    parms = {'q': 'bitcoin exchange', 'part':'snippet', 'maxResults':"1", 'regionCode': 'US', 'key': mykey}
    if len(negatives)>60:
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
            if len(negatives)>60:
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
    logger.error(e)
    logger.error("Cannot Open URL or Fetch comments at a moment")
