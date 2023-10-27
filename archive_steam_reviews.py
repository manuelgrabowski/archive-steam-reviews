#!/usr/bin/env python3

import argparse
import re
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dateutil import parser


def scrape_steam_reviews(username, download_all):
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
            steam_link = review.find("a", class_="game_capsule_ctn")["href"]
            steam_id = steam_link.split('/')[-1]
            review_link = "https://steamcommunity.com/id/" + \
                username + "/recommended/" + steam_id + "/"

            review_text = md(
                review.find(
                    "div",
                    class_="content").decode_contents())

            review_date_text = review.find("div", class_="posted").text.strip()
            review_date_regex = r"Posted (?P<review_date>.*?)\.(\s*Last edited (?P<last_updated>.*?)\.)?"
            matches = re.finditer(review_date_regex, review_date_text)
            review_date = None
            last_updated = None
            for m in matches:
                review_date = m.group('review_date')
                last_updated = m.group('last_updated')

            playtime_text = review.find("div", class_="hours").text.strip()
            playtime_regex = r"(?P<total_playtime>.*?) hrs on record(\s*\((?P<playtime_at_review>.*?) hrs at review time\))?"
            matches = re.finditer(playtime_regex, playtime_text)
            total_playtime = None
            playtime_at_review = None
            for m in matches:
                total_playtime = m.group('total_playtime')
                playtime_at_review = m.group('playtime_at_review')

            review_data = {
                "steam_link": steam_link,
                "review_link": review_link,
                "total_playtime": total_playtime,
                "playtime_at_review": playtime_at_review,
                "review_text": review_text,
                "review_date": parser.parse(review_date),
                "last_updated": None if not last_updated or (
                    last_updated == review_date) else parser.parse(last_updated)}

            parsed_reviews.append(review_data)

        if download_all:
            page_number += 1
        else:
            break

    return parsed_reviews


def print_review(review):
    print(f"Steam Link: {review['steam_link']} / {review['review_link']}")
    print(
        f"Review Date: {review['review_date']} (last updated: {review['last_updated']})")
    print(
        f"Playtime: {review['total_playtime']} (at review: {review['playtime_at_review']})")
    print(f"Review: {review['review_text']}")
    print("-" * 50)


def save_review(review):
    steam_id = review['steam_link'].split('/')[-1]

    with open(steam_id + '.md', mode='w', encoding="utf-8") as f:
        f.write('---')
        f.write('\n')
        f.write('steam_link: ' + review['steam_link'])
        f.write('\n')
        f.write('review_link: ' + review['review_link'])
        f.write('\n')
        f.write('review_date: ' + review['review_date'].strftime("%Y-%m-%d"))
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

    reviews = scrape_steam_reviews(args.username, args.all)

    for review in reviews:
        if args.save:
            save_review(review)
        else:
            print_review(review)


if __name__ == "__main__":
    main()
