i.e. I didn't like any of the other tools out there so here's some python that does what I want.

A lot of the other tools to scrape wallpapers from Reddit do so on a periodic basis, and some automatically set your wallpaper each day/on startup, but I really just wanted a way to collect wallpapers from subreddits, without having to go to each subreddit and manually click each link, wait for the picture to load, and then deciding whether or not to download it. This frontloads the downloading so that I can filter through them faster.

I don't constantly look for better wallpapers from subreddits, I just want a few hundred of them to cycle through.

This repo includes a few scripts to download/classify images. The main script, `download.py`, uses selenium to download the first 'n' top pages of images from each wallpaper subreddit, described in `subreddits.txt`, and puts them in a folder; that's all.

##### Summary

A general summary on how this was used by me:

`python3 download.py` took about 15 hours to download ~7500 images, which had 106 failed downloads, a majority of which were dead URLs, verified by `python3 open_failed_links.py`. Any image I liked was manually downloaded using [`wget`](https://www.gnu.org/software/wget/).

`python3 classify.py`, to classify images into mobile/square/landscape, verify with [`sxiv`](https://github.com/muennich/sxiv) (e.g. `sxiv -t - < mobile.txt`), and then `python3 classify.py --link-files` to create hardlinks of each of those files into their corresponding directories.

A [custom keybinding](https://github.com/seanbreckenridge/dotfiles/blob/4934eb9a4aa76ad870d159b26b5235dea1a62c4a/.config/sxiv/exec/key-handler) with `sxiv` allows me to "delete" files, by moving any files I don't want to `/tmp` (which would be removed on system restart):

```
sxiv ./mobile
sxiv ./square
sxiv ./landscape
```

Square photos may be used as mobile/landscape, though that depends on how they might be able to be cropped, so that has to be done manually, if I liked any of them enough.

Move any images I do like from `./square` into `./mobile`/`./landscape`. Copy any mobile wallpapers that I may want to use in the future to somewhere else.

Copy all the images from `./landscape` to `~/Documents/wallpapers`.

`rm -rf wallpapers/ mobile/ square/ landscape/` (OS differences may cause links to not work properly, so make sure that the removing these doesn't remove the ones you saved. I copied the files instead of moving them, just to be sure)

#### Requirements

- selenium/python setup with chromedriver, see [here](https://selenium-python.readthedocs.io/installation.html#introduction)
- [pipenv](https://github.com/pypa/pipenv)
- python3.6+

### Run

Clone the repo.

Modify `subreddits.txt` to whichever subreddits you want to use, subreddit name, then number of pages

```
pipenv sync
pipenv run python3 download.py
```

If your webdriver is somewhere else and selenium fails to find it, you can set the `WALLPAPER_DRIVER` environment variable:

```
pipenv sync
pipenv shell
export WALLPAPER_DRIVER="${HOME}/Downloads/chromedriver"
python3 download.py
```

If this fails while the images are downloading, it can be restarted. A file called `links.txt` contains the links for each post. Deleting the `wallpapers` folder and running `python3 download.py --use-links` will restart the download process, without having to have to go to each reddit page again.

If this fails to download an image, it writes it to a file 'failed.txt'. Those can be gone through manually afterwards, by opening five links at a time in your browser: `python3 open_failed_links.py`

`python3 classify.py` will check the `wallpapers` folder, and put filenames of images into:

```
width / height <= 0.7 into ./mobile.txt
0.7 > width / height <= 1.3 into ./square.txt
width / height > 1.3 into ./landscape.txt
```

Those can be verified by using sxiv:

```
sxiv -t - < mobile.txt
sxiv -t - < square.txt
sxiv -t - < landscape.txt
```

And then moved into corresponding folders: `python3 classify.py --link-files`

##### Disclaimer

This waits what I feel is a randomized sufficient time between changing pages, but I don't claim that this won't get you banned. You're free to use this code and replace the selenium parts with [PRAW](https://praw.readthedocs.io/en/latest/), and use Reddits OAuth-API. I had no issues using this myself, and its only really meant to be used once, so the quick and dirty solution was to use selenium instead of the API.

