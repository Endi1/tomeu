import os
import shutil
import hashlib
import urllib.parse
import sqlite3
from os.path import isfile
import feedparser
import argparse

from datetime import datetime


def generate_index():
    content = ""
    for folder in os.walk('.'):
        feed_title = folder[0]

        if feed_title == '.' or feed_title == '':
            continue

        items = folder[2]

        for item in items:
            location = feed_title + '/' + item
            location = urllib.parse.quote(location[2:])
            content += f"<a href={location}>{item}</a><br />"

    f = open('index.html', 'w+')
    f.write(content)
    f.close()
    return


class Feed():
    def __init__(self, url):
        self.url = url

    def sync(self):
        conn = sqlite3.connect('.cache', detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        self.d = feedparser.parse(self.url)

        if not self.d.feed or not self.d.entries:
            return

        c.execute('SELECT id FROM cache where feed_url=?', (self.url,))
        id_ = c.fetchone()

        if not id_:
            self._insert_to_db(c)

        if not self._needs_update(c):
            return

        self._delete_old_entries(c)

        self._parse_feed(c)

        conn.commit()
        c.close()
        generate_index()

    def _get_etag(self, c):
        c.execute(
            'SELECT etag FROM cache WHERE feed_url=?', (self.url,)
        )
        etag = c.fetchone()
        return etag

    def _get_hash(self, c):
        c.execute(
            'SELECT hash from cache where feed_url=?', (self.url,)
        )
        _hash = c.fetchone()

        return _hash

    def _generate_hash(self, entries):
        titles = [e.title for e in entries]
        mergetitles = ""

        for title in titles:
            mergetitles += title

            hash_obj = hashlib.md5(mergetitles.encode('utf-8'))

        return hash_obj.hexdigest()

    def _insert_to_db(self, c):
        etag = self.d.etag if 'etag' in self.d else ''
        hash_ = ''
        if not etag:
            hash_ = self._generate_hash(self.d.entries)

        c.execute(
            'INSERT INTO cache (feed_url, etag, hash, last_delete) VALUES (?,?,?, ?)',
            (self.url, etag, hash_, datetime.now())
        )

    def _needs_update(self, c):
        etag = self._get_etag(c)
        cached_hash = self._get_hash(c)

        if etag and 'etag' in self.d:
            if etag[0] == self.d.etag:
                print('Skipping, same etag... ', self.url)
                return False

            c.execute(
                'UPDATE cache SET etag=? WHERE feed_url=?',
                (self.d.etag, self.url)
            )
            return True
        else:
            hash_ = self._generate_hash(self.d.entries)

            if cached_hash[0] == hash_:
                print('Skipping, same hash...', self.url)
                # Skip this feed
                return False

            c.execute(
                'UPDATE cache SET hash=? WHERE feed_url=?',
                (hash_, self.url)
            )
            return True

    def _delete_old_entries(self, c):
        c.execute(
            'SELECT last_delete FROM cache WHERE feed_url=?',
            (self.url)
        )

        last_delete = c.fetchone()[0]
        week_last_delete = last_delete.isocalendar()[1]
        current_week_time = datetime.now().isocalendar()[1]

        if current_week_time - week_last_delete >= 1:
            shutil.rmtree(self.d.feed.feed_title)

    def _parse_feed(self, c):
        feed_title = self.d.feed.title

        # Reset folders every week

        if not os.path.exists(feed_title):
            os.makedirs(feed_title)

        for entry in self.d.entries:
            entry_title = entry.title
            body = entry.description
            entry_title = entry_title.replace('/', '')

            f = open(os.path.join(feed_title, entry_title+'.html'), 'w+')
            f.write(body)
            f.close()

        return


def setup_cache(folder_name):
    db_location = folder_name+'/.cache'
    f = open(db_location, 'w')
    f.close()
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute(
        'CREATE TABLE cache (id integer primary key, feed_url text, etag text, hash text, last_delete timestamp)'
    )
    conn.commit()
    conn.close()
    return


def setup(folder_name):

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        setup_cache(folder_name)
        print('Folder created')
    else:
        print(f'Folder with name {folder_name} already exists, aborting')
    return


def create_parser():
    parser = argparse.ArgumentParser(description='Aggregate RSS.')
    parser.add_argument('-i', '--input', type=str,
                        help='The file with the feed URLs', default='feeds')
    parser.add_argument('-s', '--setup', help='Setup a folder for RSS feeds')

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    input_file_path = args.input
    setup_folder_name = args.setup

    if setup_folder_name:
        setup(setup_folder_name)

        return
    else:

        if not isfile(input_file_path):
            raise TypeError('Missing input file')

        input_file = open(input_file_path, 'r')
        feed_urls = input_file.readlines()
        input_file.close()

        for url in feed_urls:
            feed = Feed(url)
            feed.sync()

        return


if __name__ == '__main__':
    main()
