#!/usr/bin/env python3

"""Scrapes Steam reviews for a user."""

import argparse
import re
import urllib.request
import os.path
import time
import json
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dateutil import parser

CACHE_FILE = '/tmp/appnames.json'


def is_older_than(file, days=1):
    """Checks if a file was modified within the last x days."""
    file_time = os.path.getmtime(file)
    return (time.time() - file_time) / 3600 > 24 * days


def cache_app_names():
    """Stores the big appid<->appname JSON from Steam locally."""
    source_url = 'https://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json'

    if not os.path.isfile(CACHE_FILE) or is_older_than(CACHE_FILE, 7):
        print("Refreshing app name cache (" + CACHE_FILE + ").")
        urllib.request.urlretrieve(source_url, CACHE_FILE)


def fallback_name_by_id_lookup(app_id):
    """Scrapes a game name from the corresponding store page."""
    name = 'unknown'

    url = 'https://store.steampowered.com/app/' + str(app_id)
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    name_div = soup.find("div", id="appHubAppName_responsive")

    if name_div:
        name = name_div.decode_contents()

    return name


def find_name_by_id(app_id):
    """Returns the game name for a given app_id, either from local cache or new scrape."""
    name = 'unknown'
    with open(CACHE_FILE, encoding="utf-8") as f:
        apps = json.load(f)['applist']['apps']
        for app in apps:
            if app['appid'] == app_id:
                name = app['name']
                break

    if name == 'unknown':
        name = fallback_name_by_id_lookup(app_id)

    return name


def parse_review_dates(review):
    """Extracts the date a review was published and last updated."""
    review_date_text = review.find("div", class_="posted").text.strip()
    review_date_regex = r"Posted (?P<review_date>.*?)\.(\s*Last edited (?P<last_updated>.*?)\.)?"
    matches = re.finditer(review_date_regex, review_date_text)
    review_date = None
    last_updated = None
    for m in matches:
        review_date = m.group('review_date')
        last_updated = m.group('last_updated')

    return review_date, last_updated


def parse_review_playtime(review):
    """Extracts the current total and "total at time of review" playtime."""
    playtime_text = review.find("div", class_="hours").text.strip()
    playtime_regex = r"(?P<total_playtime>.*?) hrs on record(\s*\((?P<playtime_at_review>.*?) hrs at review time\))?"
    matches = re.finditer(playtime_regex, playtime_text)
    total_playtime = None
    playtime_at_review = None
    for m in matches:
        total_playtime = m.group('total_playtime')
        playtime_at_review = m.group('playtime_at_review')
    return total_playtime, playtime_at_review


def parse_review(review, username):
    """Extracts all relevant raw data for a review."""
    steam_link = review.find("a", class_="game_capsule_ctn")["href"]
    steam_id = int(steam_link.split('/')[-1])

    review_text = md(
        review.find(
            "div",
            class_="content").decode_contents())

    review_date, last_updated = parse_review_dates(review)
    total_playtime, playtime_at_review = parse_review_playtime(review)

    return {
        "steam_link": "https://store.steampowered.com/app/" + str(steam_id),
        "review_link": "https://steamcommunity.com/id/" +
        username + "/recommended/" + str(steam_id) + "/",
        "app_name": find_name_by_id(steam_id),
        "total_playtime": total_playtime,
        "playtime_at_review": playtime_at_review,
        "review_text": review_text,
        "review_date": parser.parse(review_date),
        "last_updated": None if not last_updated or (
            last_updated == review_date) else parser.parse(last_updated)}


def scrape_steam_reviews(username, download_all):
    """Scrapes Steam reviews for a given username."""
    base_url = f"https://steamcommunity.com/id/{username}/recommended/?p="
    page_number = 1
    parsed_reviews = []

    while True:
        url = base_url + str(page_number)
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        reviews = soup.find_all("div", class_="review_box")

        # TODO: Proper check based on " Showing 1-10 of 55 entries " text
        if not reviews:
            break

        for review in reviews:
            parsed_reviews.append(parse_review(review, username))

        if download_all:
            page_number += 1
        else:
            break

    return parsed_reviews


def print_review(review):
    """Prints a parsed review to stdout."""
    print(f"Game: {review['app_name']}")
    print(f"Steam Link: {review['steam_link']} / {review['review_link']}")
    print(
        f"Review Date: {review['review_date']} (last updated: {review['last_updated']})")
    print(
        f"Playtime: {review['total_playtime']} (at review: {review['playtime_at_review']})")
    print(f"Review: {review['review_text']}")
    print("-" * 50)


def save_review(review):
    """Saves a parsed review into a Hugo-compatible Markdown file."""
    steam_id = review['steam_link'].split('/')[-1]

    with open(steam_id + '.md', mode='w', encoding="utf-8") as f:
        f.write('---')
        f.write('\n')
        f.write('title: "' + review['app_name'] + '"')
        f.write('\n')
        f.write('steam_link: ' + review['steam_link'])
        f.write('\n')
        f.write('review_link: ' + review['review_link'])
        f.write('\n')
        f.write('date: ' + review['review_date'].strftime("%Y-%m-%d"))
        if review['last_updated']:
            f.write('\n')
            f.write(
                'last_updated: ' +
                review['last_updated'].strftime("%Y-%m-%d"))
        f.write('\n')
        f.write('total_playtime: ' + review['total_playtime'])
        if review['playtime_at_review']:
            f.write('\n')
            f.write('playtime_at_review: ' + review['playtime_at_review'])
        f.write('\n')
        f.write('---')
        f.write('\n')
        f.write(review['review_text'])
        f.write('\n')


def main():
    """The main method."""
    arg_parser = argparse.ArgumentParser(
        description="Archive Steam reviews from a specific user account.")
    arg_parser.add_argument(
        "--username",
        help="Steam username for which to download reviews")
    arg_parser.add_argument(
        '--all',
        default=False,
        action='store_true',
        help="download all reviews (or just the first page)")
    arg_parser.add_argument(
        '--save',
        default=False,
        action='store_true',
        help="save downloaded reviews to filesystem (or print to stdout)")
    args = arg_parser.parse_args()

    cache_app_names()

    reviews = scrape_steam_reviews(args.username, args.all)

    for review in reviews:
        if args.save:
            save_review(review)
        else:
            print_review(review)


if __name__ == "__main__":
    main()
