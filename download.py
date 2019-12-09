import sys
import os
import pprint
import time
import argparse
import random
from datetime import datetime
from typing import Dict, List
from io import BytesIO


import requests
import click
from selenium import webdriver
from youtube_dl import YoutubeDL
from imgur_downloader import ImgurDownloader
from PIL import Image

driver = None
this_dir = os.path.abspath(os.path.dirname(__file__))
subreddits_file = os.path.join(this_dir, "subreddits.txt")

def wait_for_internet():
    click.secho("Ensuring that theres still an internet connection...", fg='red')
    while True:
        try:
            req = requests.get("http://www.google.com", timeout=10)
            req.raise_for_status()
            return
        except:
            pass


def random_wait() -> None:
    """
    Waits some time between requests/clicks, display a message to the user describing wait time
    """
    seconds = random.randint(2, 4)
    while seconds > 0:
        click.secho("\rWaiting {} second(s)...".format(seconds), nl=False, fg="yellow")
        sys.stdout.flush()
        seconds -= 1
        time.sleep(1)
    print("\r", end="")


def get_subreddits():
    """Read and parse the ./subreddits.txt file"""
    if not os.path.exists(subreddits_file):
        print(f"{subreddits_file} does not exist!", file=sys.stderr)
        sys.exit(1)

    subreddits = {}
    with open(subreddits_file, "r") as subreddits_f:
        for line in filter(str.strip, subreddits_f.read().splitlines()):
            subreddit_name, _, pages = line.partition(" ")
            try:
                subreddits[subreddit_name] = int(pages)
            except ValueError:
                print(
                    f"Could not interpret {pages} as an integer, parsed from {line}. Fix that line in {subreddits_file}",
                    file=sys.stderr,
                )
                sys.exit(1)

    pprint.pprint(subreddits)
    return subreddits


def create_webdriver():
    global driver
    if "WALLPAPER_DRIVER" in os.environ:
        driver = webdriver.Chrome(os.environ["WALLPAPER_DRIVER"])
    else:
        driver = webdriver.Chrome()


def configure() -> Dict[str, int]:
    """Read config file and set up chromedriver"""
    subreddits = get_subreddits()
    create_webdriver()
    return subreddits


def get_links(subreddit_list: Dict[str, int]) -> List[str]:
    """
    Use selenium to get the links for each image from each subreddit

    Saves a list of links to ./links.txt
    """
    global driver

    driver.get("https://old.reddit.com")

    # prompt the user to log in
    print("Logged in accounts see 100 posts instead of 25")
    input("Log into your reddit account in the chromedriver. Press enter when you're done...")


    for subreddit_name in subreddit_list:
        subreddit_base = f"https://old.reddit.com/r/{subreddit_name}/"
        print(f"Making sure {subreddit_base} exists...")
        driver.get(subreddit_base)
        random_wait()
        assert driver.current_url.casefold() == subreddit_base.casefold()

    # may be some links that arent images, those can be dealt with later/handled manually
    image_links = []
    for subreddit_name, number_of_pages in subreddit_list.items():
        # first top page, sorted by all
        driver.get(f"https://old.reddit.com/r/{subreddit_name}/top/?sort=top&t=all")
        pages_left = int(number_of_pages)
        while pages_left > 0:
            images_found = 0
            for post in driver.find_elements_by_css_selector("#siteTable > div.link"):
                # if this is a promoted post/advertisement
                if len(post.find_elements_by_css_selector(".promoted-tag")) == 0:
                    image_links.append(
                        post.find_element_by_css_selector("a.title").get_attribute("href")
                    )
                    images_found += 1
            print(f"Added {images_found} possible images from {driver.current_url}")
            random_wait()
            # dont need to go to the next page when we're on the last one (1 page left)
            if pages_left != 1:
                # go to the next page
                driver.find_element_by_css_selector("span.next-button").click()
            pages_left -= 1

    driver.quit()

    with open(os.path.join(this_dir, "links.txt"), "w") as link_cache:
        link_cache.write("\n".join(image_links))

    return image_links


def download_images(image_links: List[str]):
    os.makedirs(os.path.join(this_dir, "wallpapers"), exist_ok=True)

    couldnt_download = open(os.path.join(this_dir, "failed.txt"), "a")
    ydl = YoutubeDL({"outtmpl": "./wallpapers/%(title)s.%(ext)s"})
    def_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    for i, url in enumerate(image_links, 1):
        click.secho(
            f"({i}/{len(image_links)}) Trying to download: '{url}'...", fg="blue"
        )
        if "old.reddit.com" in url:
            try:
                # youtube-dl can download reddit videos
                # it will fallback to parsing the page/downloading the content anyways
                # so this works for any images which are not direct links to the image
                ydl.download([url])
                click.secho("Download succeeded!", fg="green")
                random_wait()
            except:
                click.secho(f"Couldn't download '{url}'.", fg="red", err=True)
                couldnt_download.write(f"{url}\n")
                couldnt_download.flush()
                wait_for_internet()
        elif "imgur" in url:
            try:
                # this may fail if a URL not on imgur has imgur in the url, but I'm fine ignoring that
                # case and going through the URL manually after its written to failed.txt
                ImgurDownloader(
                    url,
                    dir_download=os.path.join(this_dir, "wallpapers"),
                    debug=True,
                    delete_dne=False,
                ).save_images()
                click.secho("Download succeeded!", fg="green")
                random_wait()
            except Exception as e:
                print(str(e))
                click.secho(f"Couldn't download '{url}'.", fg="red", err=True)
                couldnt_download.write(f"{url}\n")
                couldnt_download.flush()
                wait_for_internet()
        else:
            try:
                r = requests.get(url, stream=True, headers=def_headers)
                try:
                    Image.open(BytesIO(r.content)).save(
                        "./wallpapers/{}.png".format(datetime.now())
                    )
                    click.secho("Download succeeded!", fg="green")
                except OSError as oe:  # image failed to be parsed
                    click.echo(str(oe))
                    raise oe  # re-raise so that the failed image decode gets written to failed.txt
                random_wait()
            except:
                click.secho(f"Couldn't download '{url}'.", fg="red", err=True)
                couldnt_download.write(f"{url}\n")
                couldnt_download.flush()
                wait_for_internet()
    couldnt_download.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-links", help="use the links.txt instead of using selenium to generate new links", action="store_true", default=False, required=False)
    args = parser.parse_args()
    try:
        if args.use_links:
            with open('links.txt', 'r') as f:
                links = list(map(str.strip, f.read().splitlines()))
        else:
            links = get_links(configure())

        download_images(links)
    finally:
        if driver:
            driver.quit()
