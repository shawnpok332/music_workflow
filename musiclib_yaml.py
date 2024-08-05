#!/usr/bin/env python3


from urllib.parse import urlparse
import multiprocessing
import subprocess
import readline
import pathlib
import time
import yaml
import json
import sys
import os


'''
TODO:
General cleanup
warn when downloading song > 7 min


'''



def music_tag(song: dict):
    import music_tag
    f = music_tag.load_file(song["absolutePath"])
    f["title"]  = song["title"]
    f["artist"] = list([a.strip() for a in str(song["artist"]).split(";")])
    if song.get("album"):
        f["album"]  = song["album"]

    for o in ["album", "albumartist", "artwork", "comment", "compilation", "composer", "discnumber", "genre", "lyrics", "totaldiscs", "totaltracks", "tracknumber", "tracktitle", "year", "isrc"]:
        if song.get(o):
            f[o]  = song[o]
    f.save()


def music_tag(song: dict):
    from mutagen.oggopus import OggOpus
    from mutagen.id3 import COMM
    path = song["absolutePath"]
    print(path)

    # Define the mapping of tag names to ID3 frames
    tag_map = {
        "title": "TITLE",
        "artist": "ARTIST",
        "album": "ALBUM",
        "albumartist": "ALBUMARTIST",
        "comment": "COMMENT",
        "composer": "COMPOSER",
        "lyrics": "LYRICS",
        "discnumber": "DISCNUMBER",
        "totaldiscs": "TOTALDISCS",
        "totaltracks": "TOTALTRACKS",
        "tracknumber": "TRACKNUMBER",
        "tracktitle": "TRACKTITLE",
        "year": "YEAR",
    }

    try:
        tags = OggOpus(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file at `{path}` does not exist or cannot be accessed.")

    for tag_name, tag_key in tag_map.items():
        if tag_name in song:
            value = song[tag_name]
            if tag_key == "COMMENT":
                tags[tag_key] = COMM(encoding=3, text=value)
            else:
                tags[tag_key] = value

    tags.save(path)

# def music_tag(song: dict):
#     from mutagen.oggopus import OggOpus
#     f = OggOpus(song["absolutePath"])
#     f["title"]  = song["title"]
#     print(list([a.strip() for a in str(song["artist"]).split(";")]))
#     f["artist"] = list([a.strip() for a in str(song["artist"]).split(";")])
#     if song.get("album"):
#         f["album"]  = song["album"]
#
#     for o in ["album", "albumartist", "artwork", "comment", "compilation", "composer", "discnumber", "genre", "lyrics", "totaldiscs", "totaltracks", "tracknumber", "tracktitle", "year", "isrc"]:
#         if song.get(o):
#             f[o]  = song[o]
#     f.save()


# def loudgain(song: dict):
#     subprocess.call([]) # , stdout=FNULL, stderr=FNULL, shell=False



def ytdlp(song, extention):
    import yt_dlp
    urls = [song["url"]]
    urls.extend(song["fallback"])

    for url in urls:
        try:
            ytdlp_opts = {
                "quiet": True,
                "noprogress": True,
                "no_warnings": True,
                "outtmpl": song["absolutePath"].removesuffix("." + extention),
                "format": "bestaudio/best",
                'noplaylist': True,
                'writethumbnail': True,
                'writesubtitles': True,
                'subtitleslangs': 'en',

                "postprocessors": [
                    {"key": "FFmpegExtractAudio",
                     "preferredcodec": extention},
                    # {'key': 'FFmpegMetadata', 'add_metadata': True},
                    {"key": "FFmpegMetadata"},
                    {"key": "FFmpegEmbedSubtitle"},
                    {'key': 'EmbedThumbnail', 'already_have_thumbnail': False, }
                ], "cachedir": "/tmp/"}

            with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
                error_code = ydl.download(url)

            music_tag(song)
            # if song.get("loudgain"):
            #     loudgain(song)
        except yt_dlp.utils.DownloadError:
            continue

        return True
    return False


class Playlist:
    songs:   dict[str, str | list[str]]
    validate = False
    formated = False

    FAIL = '\033[91m'
    ENDC = '\033[0m'

    handlers = {
        "ytdlp": ytdlp
    }

    options = {
        "fileExtention": "opus",
        "download_handler": "ytdlp",
        "baseDirectory": "~/Music/",
        "downloadParrellel": True,
        "forcetagspass": False,
        "printSongs": False,
        "print": False,
        "cleanDirectory": True,
        "download": True,
    }

    defaults = {
        "filename": "{title} - {singleartist}",
        "album": "{singleartist}",
        "subDirectory": "{singleartist}",
        "absolutePath": "{baseDirectory}/{subDirectory}/{filename}.{fileExtention}",
        "fallback": [],
        # "loudgain": True
    }


    def propagate(self, song, d={}):
        a = self.defaults.copy()
        a.update(d)
        a.update(song)
        return a


    def addsong(self, song):
        self.songs.append(self.propagate(song))


    def addfolder(self, folder):
        folder = folder.copy()
        songs = folder["songs"]
        folder.pop("songs")
        if "path" in folder.keys():
            folder["subDirectory"] = folder.pop("path")
        for s in songs:
            self.songs.append(self.propagate(s, folder))


    def __init__(self, data: list):
        self.songs = []

        assert isinstance(data, list)

        for obj in data:
            assert isinstance(obj, dict)
            k = obj.keys()
            # print(k)

            if "ignore" in k:
                pass

            elif "songs" in k:
                # assert "name" or "artist" or "album" in k, "Folders must have a `name` or `artist` or `album`"
                self.addfolder(obj)

            elif "options" in k:
                if obj["options"] is not None:
                    self.options = self.options.copy()
                    self.options.update(obj["options"])

            elif "title" and "url" in k:
                self.addsong(obj)

            else:
                assert False, f"Malformed data `{obj}`"


    def validate(self):
        self.validate = True
        # validate types
        for key, value in self.options.items():
            assert isinstance(key, str)
            assert isinstance(value, str) or isinstance(value, bool)

        for s in self.songs:
            for key, value in s.items():
                assert isinstance(key, str)
                if isinstance(value, list):
                    for a in value:
                        assert isinstance(a, str)
                else:
                    assert isinstance(
                        value, str), f"{key}, {value}, {type(value)}, {s}"

        # validate songs
        for s in self.songs:
            k = s.keys()
            if not (("title" in k) and ("url" in k) and ("artist" in k)):
                assert False, "all songs must have a `title` and `url` and a `artist`"


    def playlistComp(self):
        path = os.path.expanduser(os.path.normpath(self.options["baseDirectory"]))

        songdict = {str(pathlib.Path(a["absolutePath"])): a for a in self.songs} # .encode("utf-8")
        songlist = set(songdict.keys())
        _pathlist = [str(path) for path in pathlib.Path(path).rglob("*")
                     if not os.path.basename(path).endswith('.lrc')]
        pathlist = []
        for path in _pathlist:
            if not os.path.isdir(path):
                pathlist.append(path)
        pathlist = set(pathlist)
        del _pathlist

        # same = songlist.intersection(pathlist)
        newlist = songlist-pathlist
        moved = pathlist-songlist

        new = []
        for n in newlist:
            new.append(songdict[n])

        return new, moved


    def cleanDirectory(self):
        assert len(self.songs) > 0
        _, moved = self.playlistComp()

        if len(moved) == 0:
            print("\nNo unknown files!\n")
            return

        q = self.ask("Do you want to review unknown files?")
        if q == "n":
            return
        assert q == "y"

        for f in moved:
            if os.path.basename(f).endswith('.lrc'): continue
            print(f"\nPath: `{os.path.dirname(f)}`")
            q = self.ask(f"Do you want to move `{os.path.basename(f)}` to trash?", options=[
                    'y', 'n', 'c'])
            if q == "c":
                break
            elif q == "n":
                pass
            elif q == "y":
                from send2trash import send2trash
                send2trash(f)  # move to trash
                print("Moved to trash.")
            else:
                assert False, "{FAIL}UNREACHABLE{ENDC} "
        print()


    def downloadSong(self, song):

        assert song["absolutePath"]
        assert not os.path.exists(song["absolutePath"]), f"{self.FAIL}ERROR:{self.ENDC} File already exists: `{song['absolutePath']}`"

        print(f"downloading `{song['filename']}.{self.options['fileExtention']}` from `{song['url']}`...")

        td = urlparse(song["url"]).netloc
        assert td == "www.youtube.com", f"{self.FAIL}ERROR:{self.ENDC} Unknown domain: `{td}` in `{song['url']}`, for song `{song['filename']}`"

        handler = self.handlers[self.options["download_handler"]]
        out = handler(song, self.options['fileExtention'])

        if not out:
            print(f"{self.FAIL}ERROR:{self.ENDC} Song download failed: `{song['filename']}`, consider adding more fallback urls. ")
        elif not os.path.exists(song["absolutePath"]):
            print(f"{self.FAIL}ERROR:{self.ENDC} Song download failed, and no error was reported (bad thing): `{song['filename']}`")

        return out


    def ask(self, question: str, options: list = ['y', 'n'], default='y'):
        assert question
        assert isinstance(question, str)
        assert options
        assert isinstance(options, list)
        assert len(options) > 0
        assert isinstance(options[0], str)
        assert default
        assert default in options

        options = [o.lower() for o in options]
        o2 = options.copy()
        d = o2.index(default)
        o2[d] = o2[d].upper()
        string = f"{question.strip()} [{'/'.join(o2)}]: "
        trys = 0
        while trys < 3:
            q = input(string).strip().lower()
            if q == '':
                q = default
            if q in options:
                return q
            print(options)
            print(f"Invalid result: \"{q}\"")
            trys += 1
        print("Too many tries, canceling!")
        exit(1)


    # https://stackoverflow.com/a/38993222
    def flush_input(self):
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except ImportError:
            # import sys
            # sys.stdin.flush()
            import sys
            import termios  # for linux/unix
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)


    def download(self):
        assert self.validate
        assert self.formated
        newSongs, _ = self.playlistComp()

        if newSongs == []:
            print("No unsynced music!\n")
            time.sleep(0.5)
            return

        print("Files to be downloaded: ")
        for s in newSongs:
            print(f" -> {s['filename']}.{self.options['fileExtention']}")
        print(f"Path: {self.options['baseDirectory']}")

        time.sleep(1)

        self.flush_input()
        q = self.ask("Continue?")
        if q == 'n':
            return False

        if self.options["downloadParrellel"]:
            with multiprocessing.Pool(15) as p:
                try:
                    m = p.map_async(self.downloadSong, newSongs)
                    m.wait()
                    failedDownloads = m.get().count(False)
                except KeyboardInterrupt:
                    print("Caught KeyboardInterrupt, shutting down. ")
                    p.close()
                    p.join()
            del m
            del p
        else:
            r = []
            for a in newSongs:
                r.append(self.downloadSong(a))
            failedDownloads = r.count(False)
            del r

        if failedDownloads == 0:
            print(f"\nAll songs have successfully been downloaded. ")
        elif failedDownloads == 1:
            print(f"{self.FAIL}ERROR:{self.ENDC} one song failed to download. ")
        elif failedDownloads > 0:
            print(f"{self.FAIL}ERROR:{self.ENDC} `{failedDownloads}` songs failed to download. ")

        assert failedDownloads <= len(newSongs)


    def format(self):
        self.formated = True
        for s in self.songs:
            for key, value in s.items():
                if isinstance(value, str):
                    a = {"baseDirectory": os.path.expanduser(os.path.normpath(self.options["baseDirectory"])),
                         "fileExtention": self.options["fileExtention"]}
                    a.update(s)
                    # a["subDirectory"] = s["artist"].split(";", 1)[0].strip()
                    a["singleartist"] = s["artist"].split(";", 1)[0].strip()
                    s[key] = value.format(**a)
            s["absolutePath"] = os.path.expanduser(
                os.path.normpath(s["absolutePath"]))
            if s.get("fallback") and isinstance(s.get("fallback"), str):
                s["fallback"] = list(s["fallback"])


    def printSongs(self):
        print(json.dumps(self.songs, indent=2, ensure_ascii=False))

    def print(self):
        print(json.dumps({
            "songs": self.songs,
            "options": self.options,
        }, indent=2, ensure_ascii=False))

    def forcetag(self, song):
        assert song["absolutePath"]
        assert os.path.exists(song["absolutePath"]), f"{self.FAIL}ERROR:{self.ENDC} File doesn't exists: `{song['absolutePath']}`"

        print(f"Editing tags: `{song['filename']}.{self.options['fileExtention']}`...")

        try:
            music_tag(song)
        except:
            print(f"{self.FAIL}ERROR:{self.ENDC} Error while editing tags: `{song['filename']}.{self.options['fileExtention']}`...")


    def forcetagspass(self):
        if self.options["downloadParrellel"]:
            with multiprocessing.Pool(15) as p:
                try:
                    m = p.map_async(self.forcetag, self.songs)
                    m.wait()
                except KeyboardInterrupt:
                    print("Caught KeyboardInterrupt, shutting down. ")
                    p.close()
                    p.join()
            del m
            del p
        else:
            r = []
            for a in self.songs:
                self.forcetag(a)
            del r

    def execute(self):
        if not self.formated: self.format()
        if not self.validate: self.validate()

        if self.options["cleanDirectory"]: self.cleanDirectory()
        if self.options["download"]: self.download()
        if self.options["print"]: self.print()
        if self.options["printSongs"]: self.printSongs()
        if self.options["forcetagspass"]: self.forcetagspass()


if __name__ == "__main__":
    playlist = yaml.safe_load(open(sys.argv[1]).read())
    playlist = Playlist(playlist)
    playlist.execute()

    if len(playlist.songs) == 0:
        print(f"No songs. ):")
    else:
        print(f"`{len(playlist.songs)}` Total songs.")


