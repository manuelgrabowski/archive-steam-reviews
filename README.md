### Archive Steam reviews

This script uses BeautifulSoup to do some very basic web-scraping and retrieve the reviews for a given user account. The profile must be set to public visibility.

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

By default it will only retrieve the first page of reviews, and print to stdout. As the review page is sorted by most recently changed, usually the `--all` switch is only be needed for an initial dump of all existing reviews. If more than ten reviews are published and/or edited between running the script, the parameter is needed to get all changes.

When using `--save`, each review will be stored in a text file named with the [Steam App ID](https://steamdb.info/apps/) the review is for (unfortunately the game name itself is not available for scraping without an additional request). The file will have a [YAML frontmatter](https://gohugo.io/content-management/front-matter/) with some metadata (Steam URL, playtime, date of review, …) and the review (converted to Markdown) as the post body. As such, it is ready for use in [Hugo](https://gohugo.io/), similar static site generators or other purposes.
