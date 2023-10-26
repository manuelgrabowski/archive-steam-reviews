### Archive Steam reviews

While Steam does have [an API](https://steamcommunity.com/dev) and even [some endpoints](https://developer.valvesoftware.com/wiki/Steam_Web_API#GetOwnedGames_.28v0001.29) that allow accessing your own data, there is no official way of retrieving all of your game reviews. You can use the API to download reviews _per game_, but not _per user_ – which is what I'm much more interested in.

While I like publishing the reviews there, I don't want them to solely live on that platform. Being able to automatically download them into simple text files allows me to make sure they don't vanish in case the platform goes away – however unlikely that may be in the case of Steam – and also to integrate the reviews into my blog in a somewhat automated fashion.

This script uses BeautifulSoup to do some very basic web-scraping and retrieve the reviews for a given user account – the profile must be set to public visibility for this to work.

### Usage

```
usage: archive_steam_reviews.py [-h] [--username USERNAME] [--all] [--save]

Archive Steam reviews from a specific user account.

options:
  -h, --help           show this help message and exit
  --username USERNAME  Steam username for which to download reviews
  --all                download all reviews (or just the first page)
  --save               save downloaded reviews to filesystem (or print to stdout)
```

By default it will only retrieve the first page of reviews, and output to stdout. As the review page is sorted by most recently changed review, usually the `--all` switch should only be needed for the initial dump of all existing reviews. Unless more than ten reviews are published and/or edited between running the script, the parameter should not be needed to get all changes.


When using `--save`, each review will be stored in a text file named with the [Steam App ID](https://steamdb.info/apps/) the review is for (unfortunately the game name itself is not available for scraping without an additional request). The file will have a [YAML frontmatter](https://gohugo.io/content-management/front-matter/) with some metadata (Steam URL, playtime, date of review) and the review (converted to Markdown) as the post body – ready for use in the [Hugo](https://gohugo.io/) static site generator.
