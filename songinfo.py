#!/usr/bin/env python3

# import music_tag
from tinytag import TinyTag
import readline
import tempfile
import yt_dlp
import os

extention = "opus"

out = ''

def exit():
    while True:
        i = input("Do you want to exit? [y/N]").strip().lower()
        if len(i) > 1 or i not in ['y', 'n', '']:
            print("Answer: `Y` or `N`")
            continue
        if i == 'y':
            return True
        elif i == 'n':
            return False
        elif i == '':
            return False
        else:
            assert False, "unreachable"
        return False
    return False

while True:
    try: url = input("|> ").strip().strip("\"").strip("\'").strip()
    except KeyboardInterrupt: print(); continue

    if len(url) < 2 and len(url) != 0:
        if exit():
            break
        else:
            continue
    if url == "": continue

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            ytdlp_opts = {
                "quiet": True,
                "noprogress": True,
                "no_warnings": True,
                "outtmpl": os.path.join(tmpdirname, "tmp"),
                "format": "bestaudio/best",
                'paths': { 'temp': tmpdirname },
                # 'writesubtitles': 'true',
                # 'subtitleslangs': 'en',
                "postprocessors": [
                    {"key": "FFmpegExtractAudio",
                        "preferredcodec": extention},
                    {"key": "FFmpegMetadata"},
                    # {"key": "FFmpegEmbedSubtitle"},
                ], "cachedir": "/tmp/"}

            with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
                error_code = ydl.download(url)

            # f = music_tag.load_file(os.path.join(tmpdirname, "tmp."+extention))
            f = TinyTag.get(os.path.join(tmpdirname, "tmp."+extention))

            title = str(f.title).replace(u'\u2014', "-")
            title = title.replace(u'/', "")

            feat = False
            if title.count("-") == 1:
                stitle = title.split('-', 1)
                a = str(f.artist).replace(',', ';').split(';')[0]

                if len(stitle) == 1:
                    pass
                    # title = str(f['title'])
                elif a in stitle[0]:
                    title = stitle[1].strip()
                elif a in stitle[1]:
                    title = stitle[0].strip()
                else:
                    pass
                    # title = str(f['title'])

                title = title.replace('\"', '\\\"')
                for t in ["(Instrumental)",
                          "【ENGLISH COVER】",
                          "【ORIGINAL MV】",
                          "【COVER】",
                          "【MV】",
                          "『MV』",
                          "「MV」"
                          "[SynthV Original]",
                          "[Original Song]",
                          "(Original Music Video)",
                          "(Official Music Video)",
                          "(Official Lyric Video)",
                          "(SynthV Original Song)",
                          "(Official 4K Video)",
                          "(indie rock cover)",
                          "(Official Video)",
                          "(OFFICIAL VIDEO)",
                          "(English Cover)",
                          "(Lyric Video)",
                          "(HQ Audio)",
                          "(Lyrics)",
                          "(Audio)",
                          "COVER",
                          ]:
                    title = title.replace(t, "")

                for t in ["ft.", "(feat.", "feat."]:
                    if t in title:
                        title, feat = title.split(t, 1)
                        feat = feat.strip().strip(")").strip()

            print(f"    # {f.title}")




            title = title.strip()
            ti = f"    - title: \"{title}\"\n"
            print(ti, end = '')

            url = f"      url: \"{url}\"\n"
            print(url, end = '')

            alb = str(f.album).strip()
            if alb != "" and alb != f.artist and alb != f.title:
                album = f"      album: \"{alb}\"\n"
                print(album, end = '')
            else: album = ''

            artist = str(f.artist).replace(',', ';').split(';')
            artist = '; '.join(a.strip() for a in artist)
            if feat:
                artist += "; " + feat
            ar = f"      artist: \"{artist}\"\n"
            print(ar, end="\n")


            out += f"    # {f.title}\n"
            out += ti
            out += url
            out += album
            out += ar
            out += '\n'
    except Exception as e:
        print(e)
        # raise e

print('\n')
print("Out: ")
columns, rows = os.get_terminal_size(0)
print("-"*columns)
print("-"*columns)
print('\n')

if out != "":
    print("- path: \"tmp\"")
    print("  songs:")
    print(out)

print('\n')
print("-"*columns)
print("-"*columns)



