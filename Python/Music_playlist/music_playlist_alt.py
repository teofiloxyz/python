#!/usr/bin/python3
# MusicPlaylist menu com diversas funções, versão alternativa

import os
import subprocess
import sqlite3
import pandas as pd
from datetime import datetime
from Tfuncs import gmenu
from configparser import ConfigParser


class MusicPlaylist:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.db_path = self.config['GENERAL']['db_path']
        self.music_path = self.config['GENERAL']['music_path']
        self.playlist_txt_path = self.config['GENERAL']['playlist_txt_path']
        self.search_utils_path = self.config['GENERAL']['search_utils_path']
        self.downloads_path = self.config['GENERAL']['downloads_path']

        if not os.path.isfile(self.db_path):
            self.setup_database()

    def setup_database(self):
        subprocess.run(['touch', self.db_path])

        self.db_con = sqlite3.connect(self.db_path)
        self.cursor = self.db_con.cursor()

        self.cursor.execute('CREATE TABLE active(music_id '
                            'INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL '
                            'UNIQUE, date_added TEXT NOT NULL, title TEXT '
                            'NOT NULL UNIQUE, ytb_code TEXT NOT NULL UNIQUE, '
                            'genre TEXT NOT NULL)')
        self.cursor.execute('CREATE TABLE archive(music_id '
                            'INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL '
                            'UNIQUE, date_added TEXT NOT NULL, title TEXT '
                            'NOT NULL UNIQUE, ytb_code TEXT NOT NULL UNIQUE, '
                            'genre TEXT NOT NULL)')
        self.cursor.execute('CREATE TABLE genres(genre TEXT NOT NULL UNIQUE)')
        self.db_con.commit()

        self.db_con.close()

    @staticmethod
    def generic_connection(func):
        def process(self, *args, **kwargs):
            self.db_con = sqlite3.connect(self.db_path)
            self.cursor = self.db_con.cursor()
            func(self, *args, **kwargs)
            self.db_con.close()
        return process

    def search(self, table):
        while True:
            query = input('Enter music title to search: ')
            if query == 'q':
                print('Aborted...')
                return 'q'

            self.cursor.execute(f'SELECT title FROM {table} '
                                f'WHERE title like "%{query}%"')
            result = tuple([title[0] for title in self.cursor.fetchall()])

            if len(result) == 0:
                print(f"Nothing was found with '{query}' "
                      "on the title")
                continue
            else:
                return result

    @generic_connection
    def play(self, playlist):
        while True:
            print(f'\nls: Show {playlist} titles\ng: Search by genre\n'
                  's: Search by title\n#: Play music with # ID')
            option = input('Pick one of the options above '
                           f'or leave empty to play the whole {playlist}: ')

            if option == 'q':
                print('Aborted...')
                return

            elif option == 'ls':
                self.show(playlist, 'titles')
                # need to connect db again, bc show func closes database
                self.db_con = sqlite3.connect(self.db_path)
                self.cursor = self.db_con.cursor()

            elif option == 'g':
                while True:
                    self.cursor.execute('SELECT genre FROM genres')
                    genres = tuple([genre[0]
                                    for genre in self.cursor.fetchall()])
                    [print(f'[{n}] {genre}')
                     for n, genre in enumerate(genres, 1)]
                    selected_genres = input('Enter the genre number or combo '
                                            '(e.g: 2; 4+2+3): ')
                    selected_genres_list = []
                    for genre in selected_genres.split('+'):
                        try:
                            selected_genres_list.append(genres[int(genre) - 1])
                        except (ValueError, IndexError):
                            print('Aborted...')
                            return

                    selection = \
                        'title' if playlist == 'playlist' else 'ytb_code'
                    table = 'active' if playlist == 'playlist' else 'archive'
                    condition = \
                        '%" or genre like "%'.join(selected_genres_list)

                    self.cursor.execute(f'SELECT {selection} FROM {table} '
                                        f'WHERE genre like "%{condition}%"')

                    if playlist == 'playlist':
                        custom_list = tuple([f'"{title[0]}"*' for title
                                             in self.cursor.fetchall()])
                    else:
                        custom_list = tuple([f'https://youtu.be/{code[0]}' for
                                            code in self.cursor.fetchall()])

                    if len(custom_list) == 0:
                        selected_genres = ' or '.join(selected_genres_list)
                        print(f'Found none with genre: {selected_genres}\n')
                        continue
                    break
                break

            elif option == 's':
                table = 'active' if playlist == 'playlist' else 'archive'
                custom_list = self.search(table)
                if custom_list == 'q':
                    return
                elif len(custom_list) != 1:
                    [print(f'[{n}] {title}')
                     for n, title in enumerate(custom_list, 1)]
                    selected_titles = input('Enter the title number or combo '
                                            '(e.g: 2; 4+2+3) or leave empty '
                                            'for all: ')
                    if selected_titles != '':
                        selected_titles_list = []
                        for title in selected_titles.split('+'):
                            try:
                                selected_titles_list.append(custom_list
                                                            [int(title) - 1])
                            except (ValueError, IndexError):
                                print('Aborted...')
                                return
                        custom_list = tuple(selected_titles_list)

                if playlist == 'playlist':
                    custom_list = tuple([f'"{title}"*' for title
                                         in custom_list])
                else:
                    code_list = list()
                    for title in custom_list:
                        self.cursor.execute('SELECT ytb_code FROM archive '
                                            f'WHERE title={title}')
                        code_list.append('https://youtu.be/'
                                         f'{self.cursor.fetchall()[0]}')
                    custom_list = tuple(code_list)

                break

            elif option == '':
                if playlist == 'playlist':
                    self.cursor.execute('SELECT title FROM active')
                    custom_list = tuple([f'"{title[0]}"*' for title
                                         in self.cursor.fetchall()])
                else:
                    self.cursor.execute('SELECT ytb_code FROM archive')
                    custom_list = tuple([f'https://youtu.be/{code[0]}' for
                                        code in self.cursor.fetchall()])
                break

            else:
                try:
                    music_id = int(option)
                except ValueError:
                    continue

                if playlist == 'playlist':
                    self.cursor.execute('SELECT title FROM active '
                                        f'WHERE music_id={music_id}')
                    custom_list = tuple([f'"{title[0]}"*' for title
                                         in self.cursor.fetchall()])
                else:
                    self.cursor.execute('SELECT ytb_code FROM archive '
                                        f'WHERE music_id={music_id}')
                    custom_list = tuple([f'https://youtu.be/{code[0]}' for
                                        code in self.cursor.fetchall()])
                break

        cmd = 'mpv '
        if playlist == 'playlist':
            os.chdir(self.music_path)
        else:
            cmd += '--no-video '
        if len(custom_list) == 0:
            print('Error: Selection has no music entries...')
            return
        elif len(custom_list) > 1:
            if input(':: Play it randomly or in order? [R/o] ').lower() \
                    in ('', 'o'):
                cmd += '--shuffle '
        cmd += ' '.join(custom_list)
        subprocess.run(cmd, shell=True)
        pass

    @generic_connection
    def add(self, playlist, entry=None):
        table = 'active' if playlist == 'playlist' else 'archive'
        if entry is None:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            ytb_code = input('Enter the youtube link or video code: ')
            if ytb_code == 'q':
                print('Aborted...')
                return
            elif '/' in ytb_code:
                ytb_code = ytb_code.split('/')[-1]
            self.cursor.execute(f'SELECT * FROM {table} '
                                f'WHERE ytb_code="{ytb_code}"')
            if self.cursor.fetchone() is not None:
                print(f'Already have that youtube code on the {playlist}')
                return
            ytb_link = 'https://youtu.be/' + ytb_code

            print("Getting title...")
            cmd = f'yt-dlp --get-title {ytb_link}'.split()
            title = subprocess.run(cmd, capture_output=True) \
                .stdout.decode('utf-8')[:-1]
            if title.startswith('ERROR:') or title == '':
                print("Problem getting title...\nAborting...")
                return
            custom_title = input('Enter custom title (artist - song) '
                                 f'or leave empty for "{title}": ')
            if custom_title == 'q':
                print('Aborted...')
                return
            elif custom_title != '':
                title = custom_title
            title = title.replace('"', "'")
            title = title.replace('/', "|")
            self.cursor.execute(f'SELECT title FROM {table}')
            titles = tuple([f'{title[0]}' for title
                            in self.cursor.fetchall()])
            while title in titles:
                print(f'Title: "{title}" already exists!')
                title = input('Enter custom title (artist - song): ')
                if title == 'q':
                    print('Aborted...')
                    return
                title = title.replace('"', "'")
                title = title.replace('/', "|")

            self.cursor.execute('SELECT genre FROM genres')
            genres = tuple([genre[0] for genre in self.cursor.fetchall()])
            if len(genres) == 0:
                qst = 'Enter the genre(s) (e.g.: Rock; Pop+Rock): '
            else:
                [print(f'[{n}] {genre}') for n, genre in enumerate(genres, 1)]
                qst = 'Enter the genre(s) number(s) (e.g.: 2; 4+2+3)\nOr ' \
                    'enter a custom genre(s) (e.g.: Rock; Pop+Rock; 3+Pop+1): '
            ans = input(qst)
            if ans == 'q':
                print('Aborted...')
                return
            ans_list = ans.split('+')
            genre = []
            for ans in ans_list:
                try:
                    genre.append(genres[int(ans) - 1])
                except (ValueError, IndexError):
                    # Custom genre
                    genre.append(ans.capitalize())
                    self.cursor.execute('INSERT INTO genres (genre) '
                                        f'VALUES ({genre})')
                    self.db_con.commit()

            genre = '|'.join(genre)

            entry = now, title, ytb_code, genre
        else:
            title, ytb_code = entry[1], entry[2]
            self.cursor.execute(f'SELECT * FROM {table} '
                                f'WHERE ytb_code="{ytb_code}"')
            if self.cursor.fetchone() is not None:
                print(f'Already have that youtube code on the {playlist}')
                return

        if playlist == 'playlist':
            ytb_link = 'https://youtu.be/' + ytb_code
            print("Downloading...")
            cmd = 'yt-dlp -f "bestaudio" --continue --no-overwrites ' \
                '--ignore-errors --extract-audio ' \
                f'-o "{self.music_path}/{title}.%(ext)s" {ytb_link}'
            err = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)
            if err != 0:
                print('Error downloading...\nAborting...')
                return

        self.cursor.execute(f'INSERT INTO {table} (date_added, title, '
                            f'ytb_code, genre) VALUES {entry}')
        self.db_con.commit()
        print(f'"{title}" added to the {playlist}!')

    def remove(self):
        pass

    def recover_arc(self):
        pass

    def edit(self):
        pass

    @generic_connection
    def show(self, playlist, mode):
        table = 'active' if playlist == 'playlist' else 'archive'
        selection = '*' if mode == 'all' else 'music_id, title'

        df = pd.read_sql(f'SELECT {selection} FROM {table} ORDER BY music_id',
                         self.db_con)
        if len(df) == 0:
            print(f'{playlist.capitalize()} is empty...')
            return

        print(df.to_string(index=False))

    def youtube_search(self):
        pass

    def download(self):
        pass

    def export_csv(self):
        pass

    def import_csv(self):
        pass


if __name__ == "__main__":
    pl = MusicPlaylist()
    title = 'Music-Playlist-Menu'
    keys = {'p': (lambda: pl.play('playlist'),
                  "Play music from playlist"),
            'pa': (lambda: pl.play('archive'),
                   "Play music from archive"),
            'ad': (lambda: pl.add('playlist'),
                   "Add music to playlist"),
            'rm': (lambda: pl.remove('playlist'),
                   "Remove music from playlist that goes to archive"),
            'ada': (lambda: pl.add('archive'),
                    "Add music to archive"),
            'rma': (lambda: pl.remove('archive'),
                    "Remove music from archive"),
            'rc': (pl.recover_arc,
                   "Recover music from archive"),
            'ed': (lambda: pl.edit('playlist'),
                   "Edit title or genre of a music from playlist"),
            'eda': (lambda: pl.edit('archive'),
                    "Edit title or genre of a music from archive"),
            'ls': (lambda: pl.show('playlist', 'titles'),
                   "Show playlist titles"),
            'la': (lambda: pl.show('playlist', 'all'),
                   "Show all columns from playlist"),
            'lsa': (lambda: pl.show('archive', 'titles'),
                    "Show archive titles"),
            'laa': (lambda: pl.show('archive', 'all'),
                    "Show all columns from archive"),
            'y': (pl.youtube_search,
                  "Search music from youtube"),
            'd': (pl.download,
                  "Download from txt file with titles and/or links"),
            'xc': (pl.export_csv,
                   "Export playlist (or archive) to CSV"),
            'ic': (pl.import_csv,
                   "Import playlist (or archive) from CSV")}
    gmenu(title, keys)