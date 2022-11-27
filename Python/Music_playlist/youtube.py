from Tfuncs import inpt
from youtube_search import YoutubeSearch

import os
import subprocess


class Youtube:
    @staticmethod
    def get_title(ytb_code: str) -> str:
        print("Getting title...")
        cmd = f"yt-dlp --get-title https://youtu.be/{ytb_code}".split()
        title = subprocess.run(cmd, capture_output=True).stdout.decode("utf-8")[
            :-1
        ]
        if title.startswith("ERROR:") or title == "":
            print("Problem getting title...\nAborting...")
            return "q"
        return title

    def download(
        self,
        ytb_code: str,
        output_dir: str,
        title: (str | None) = None,
        mp3_output: bool = False,
    ) -> (int | None):
        print("Downloading...")
        if title is None:
            output_path = f"{output_dir}/%(title)s.%(ext)s"
        else:
            output_path = f"{output_dir}/{title}.%(ext)s"
        cmd = (
            'yt-dlp -f "bestaudio" --continue --no-overwrites '
            "--ignore-errors --extract-audio -o "
            f'"{output_path}" https://youtu.be/{ytb_code}'
        )
        if mp3_output:
            cmd += " --audio-format mp3"
        err = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)
        if err != 0:
            print("Error downloading...\nAborting...")
            return err

    def download_from_txt(self) -> None:
        def get_ytb_code(entry: str) -> str:
            if "youtu" in entry and "/" in entry:
                ytb_code = entry.split("/")[-1]
            else:
                ytb_code = entry
            if len(ytb_code) != 11 or " " in ytb_code:
                search = YoutubeSearch(entry, max_results=1).to_dict()
                ytb_code = search[0]["id"]
            return ytb_code

        txt = inpt.files(
            question="Enter the txt file full path: ", extensions="txt"
        )
        output_dir = "path/to/output_dir"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        custom_title = None
        mp3_output = (
            True
            if input(":: Want output format to be mp3? [y/N] ").lower() == "y"
            else False
        )

        with open(str(txt), "r") as tx:
            entries = tx.readlines()
        for entry in entries:
            entry = entry.strip("\n")
            if entry.strip(" ") == "":
                continue
            ytb_code = get_ytb_code(entry)
            self.download(ytb_code, output_dir, custom_title, mp3_output)