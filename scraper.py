import requests
import shutil
import pathlib
import json
import csv
import os
from pathlib import Path
import tkinter
from tkinter import filedialog
from progress.bar import ChargingBar


API_KEY = os.environ.get(API_KEY)
MOVIE_LIST_ID = "7054979"
TV_LIST_ID = "7054980"


class Media:
    def __init__(self, type):
        if type == "movie":
            self.title = "title"
            self.folder = "Movies"
        elif type == "tv":
            self.title = "name"
            self.folder = "TV Shows"


root = tkinter.Tk()
root.withdraw()
p = Path(tkinter.filedialog.askdirectory())
# p = Path.cwd()


def get_media_info(list_id):
    url = (
        "https://api.themoviedb.org/3/list/"
        + list_id
        + "?api_key="
        + API_KEY
        + "&language=en-US"
    )

    response = requests.get(url)
    list = response.json()

    media = []
    for item in list["items"]:
        name = item[Media(item["media_type"]).title]
        name = name.replace(":", " -")
        name = name.replace("/", "-")
        info = (
            str(item["id"]),
            item["media_type"],
            name,
        )

        if item["media_type"] == "movie":
            info = info + (item["poster_path"],)

        media.append(info)

    # media[0] = id
    # media[1] = movie or tv
    # media[2] = movie or tv show name
    # media[3] = if movie, poster link
    return media


def get_season_links(media_info):
    bar = ChargingBar("Getting season links", max=len(media_info))
    # media[4] = list with tv show seasons
    # media[4][0] = season number
    # media[4][1] = poster link
    for index, media in enumerate(media_info):
        seasons = []
        if media[1] == "tv":
            url = (
                "https://api.themoviedb.org/3/tv/"
                + media[0]
                + "?api_key="
                + API_KEY
                + "&language=en-US"
            )
            response = requests.get(url)
            list = response.json()
            for season in list["seasons"]:
                if (
                    not season["season_number"] == 0
                    and not season["poster_path"] == None
                ):
                    seasons.append(
                        (str(season["season_number"]), season["poster_path"])
                    )
            media = media + (seasons,)
            media_info[index] = media
            bar.next()

    bar.finish()
    return media_info


def download(filepath, link):
    url = "https://image.tmdb.org/t/p/original" + link
    if not filepath.is_file():
        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(url, stream=True)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Open a local file with wb ( write binary ) permission.
            with open(filepath, "wb") as f:
                # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


def download_posters():
    list_id = input("List ID: ")
    media_info = get_media_info(list_id)
    media_info = get_season_links(media_info)

    bar = ChargingBar("Downloading posters", max=len(media_info))
    for media in media_info:
        poster_folder = p / Media(media[1]).folder
        if not poster_folder.is_dir():
            poster_folder.mkdir()

        if media[1] == "movie":
            download((poster_folder / (media[2] + ".jpg")), media[3])
        elif media[1] == "tv":
            poster_folder = poster_folder / media[2]
            if not poster_folder.is_dir():
                poster_folder.mkdir()
            seasons = media[3]
            for season in seasons:
                download((poster_folder / (season[0] + ".jpg")), season[1])
        bar.next()

    bar.finish()


def add_to_list():
    r = requests.get(
        "https://api.themoviedb.org/3/authentication/token/new?api_key=" + API_KEY
    )
    if r.status_code == 200:
        response = r.json()
    TOKEN = response["request_token"]
    print("https://www.themoviedb.org/authenticate/" + TOKEN)
    input("Press enter!")
    p = requests.post(
        "https://api.themoviedb.org/3/authentication/session/new?api_key=" + API_KEY,
        json={"request_token": TOKEN},
    )
    if p.status_code == 200:
        response = p.json()
    SESSION_ID = response["session_id"]

    with open("movies.csv") as ids:
        reader = csv.reader(ids)
        data = list(reader)

    for id in data:
        p = requests.post(
            "https://api.themoviedb.org/3/list/"
            + MOVIE_LIST_ID
            + "/add_item?api_key="
            + API_KEY
            + "&session_id="
            + SESSION_ID,
            json={"media_id": id[0]},
        )


download_posters()
