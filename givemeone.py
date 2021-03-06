# GiveMeOne by Robin Universe
# Licensed under the WTFPL

import sys
sys.dont_write_bytecode = True

from flask import Flask, render_template, redirect, request
from engines import google, ddg, ytdl, wiki
import configinit
import datetime
import textwrap
import requests
import pymongo
import json
import re
import os

app = Flask(__name__)

discord_user_agents = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0", "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)"]
telegram_user_agents = ["TelegramBot (like TwitterBot)"]
engines = [ "google", "ddg", "yt", "wiki", "arch", "mc", "scp", "urban", "dict" ]
linktypes = {
    "google" : "image",
    "ddg"    : "image",
    "yt"     : "youtube",
    "wiki"   : "wiki",
    "arch"   : "arch",
    "mc"     : "minecraft",
    "scp"    : "scp",
    "urban"  : "urban",
    "dict"   : "dict"
}

# Load the config file
config = configinit.getConfig()

# Check to see what link caching system the user wants, and do the setup appropriate for that
link_cache_system = config['config']['link_cache']
if link_cache_system == "json":
    link_cache = {}
    if not os.path.exists("links.json"):
        with open("links.json", "w") as outfile:
            default_link_cache = {"test":"test"}
            json.dump(default_link_cache, outfile, indent=4, sort_keys=True)

    f = open('links.json',)
    link_cache = json.load(f)
    f.close()
elif link_cache_system == "db":
    client = pymongo.MongoClient(config['config']['database'], connect=False)
    db = client.GiveMeOne

# Site without any arguments
@app.route('/') 
def default():
    user_agent = request.headers.get('user-agent')
    if user_agent in discord_user_agents:
        return message("GiveMeOne is a shortcut to help make googling images a bit easier")
    else:
        return redirect(config['config']['repo'], 301)

# Main function
@app.route('/<term>') 
def givemeone(term):
    return search(term)

# Specify Engine
@app.route('/<engine>/<term>') 
def engine(term, engine):
    if engine in engines:
        return search(term, engine=engine, linktype=linktypes[engine])
    else:
        return message(engine + " is not a valid search engine... yet!")

# Sends a simple embed with a message
def message(text): 
    return render_template('default.html', message=text, color=config['config']['color'], appname=config['config']['appname'], repo=config['config']['repo'], url=config['config']['url'])

# Attempts to return a render template from a search term by searching the link cache, or adding a new entry if one is not found
def search(term, engine=config['config']['engine'], linktype="image"): 
    cached_gso = get_gso_from_link_cache(term, linktype)

    if cached_gso == None:
        if engine == 'hybrid':
            try:
                gso = google.searchimages(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                gso = ddg.searchimages(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
        elif engine == 'google':
            try:
                gso = google.searchimages(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message('Google API quota has been reached for the day!')
        elif engine == 'ddg':
            try:
                gso = ddg.searchimages(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message('DuckDuckGo search failed!')
        elif engine == 'yt':
            try:
                gso = google.searchyoutube(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                try:
                    gso = ytdl.searchyoutube(term, config)
                    add_gso_to_link_cache(gso)
                    return redirect(gso['url'], 301)
                except Exception as e:
                    print(e)
                    return message("Could not retrieve youtube link!")
        elif engine == 'wiki':
            try:
                gso = wiki.searchwikipedia(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message("Could not retrieve Wikipedia link")
        elif engine == 'arch':
            try:
                gso = wiki.searcharchwiki(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message("Could not retrieve Archwiki link")
        elif engine == 'urban':
            try:
                gso = wiki.searchurban(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message("Could not retrieve UrbanDictionary link")
        elif engine == 'dict':
            try:
                gso = wiki.searchdict(term, config)
                add_gso_to_link_cache(gso)
                return message(gso['url'])
            except Exception as e:
                print(e)
                return message("Could not retrieve Dictionary link")
        elif engine == 'mc':
            try:
                return message("Minecraft Wiki searching not yet ready")
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message("Could not retrieve Minecraft Wiki link")
        elif engine == 'scp':
            try:
                gso = wiki.scpwiki(term, config)
                add_gso_to_link_cache(gso)
                return redirect(gso['url'], 301)
            except Exception as e:
                print(e)
                return message("Could not retrieve SCP link")

    else:
            return redirect(cached_gso['url'], 301)

# Try to get a GSO from the link cache
def get_gso_from_link_cache(term, linktype=""):
    if link_cache_system == "db":
        collection = db.linkCache
        gso = collection.find_one({'term': term, "type" : linktype})
        if gso != None: 
            print(linktype + " link located in DB cache for term: " + term.replace("-"," "))
            return gso
        else:
            print(linktype + " link was not found in DB cache for term: " + term.replace("-"," "))
            return None
    elif link_cache_system == "json":
        if term in link_cache:
            print("Link located in json cache")
            gso = link_cache[term]
            return gso
        else:
            print("Link not in json cache")
            return None

# Add a GSO to the Link Cache
def add_gso_to_link_cache(gso):
    if link_cache_system == "db":
        try:
            out = db.linkCache.insert_one(gso)
            print("Link added to DB cache")
            return True
        except Exception:
            print("Failed to add link to DB cache")
            return None
    elif link_cache_system == "json":
        link_cache[gso['term']] = gso
        with open("links.json", "w") as outfile: 
            json.dump(link_cache, outfile, indent=4, sort_keys=True)
            print("Link added to JSON cache")
            return None
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
