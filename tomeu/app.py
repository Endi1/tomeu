import os
import hashlib
import urllib.parse
import sqlite3
from os.path import isfile
import feedparser
import argparse


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


def parse_feeds(feed_urls):
    conn = sqlite3.connect('.cache')
    c = conn.cursor()

    for url in feed_urls:
        d = feedparser.parse(url)

        if not d.feed or not d.entries:
            continue

        c.execute('SELECT id FROM cache where feed_url=?', (url,))
        id_ = c.fetchone()

        if not id_:
            etag = d.etag if 'etag' in d else ''
            hash_ = ''
            if not etag:
                hash_ = _get_hash(d.entries)

            c.execute(
                'INSERT INTO cache (feed_url, etag, hash) VALUES (?,?,?)',
                (url, etag, hash_)
            )
        else:
            c.execute(
                'SELECT etag FROM cache WHERE feed_url=?', (url,)
            )
            etag = c.fetchone()

            if etag and 'etag' in d:
                if etag[0] == d.etag:
                    print('Skipping, same etag... ', url)
                    # skip this feed
                    continue
                else:
                    c.execute(
                        'UPDATE cache SET etag=? WHERE feed_url=?',
                        (d.etag, url)
                    )
            else:
                c.execute(
                    'SELECT hash from cache where feed_url=?', (url,)
                )
                cached_hash = c.fetchone()
                hash_ = _get_hash(d.entries)

                if cached_hash[0] == hash_:
                    print('Skipping, same hash...', url)
                    # Skip this feed
                    continue
                else:
                    c.execute(
                        'UPDATE cache SET hash=? WHERE feed_url=?',
                        (hash_, url)
                    )

        feed_title = d.feed.title

        if not os.path.exists(feed_title):
            os.makedirs(feed_title)

        for entry in d.entries:
            entry_title = entry.title
            body = entry.description
            entry_title = entry_title.replace('/', '')

            f = open(os.path.join(feed_title, entry_title+'.html'), 'w+')
            f.write(body)
            f.close()

    conn.commit()
    generate_index()
    c.close()


def _get_hash(entries):
    titles = [e.title for e in entries]
    mergetitles = ""

    for title in titles:
        mergetitles += title

    hash_obj = hashlib.md5(mergetitles.encode('utf-8'))
    return hash_obj.hexdigest()


def setup_cache(folder_name):
    db_location = folder_name+'/.cache'
    f = open(db_location, 'w')
    f.close()
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute(
        'CREATE TABLE cache (id integer primary key, feed_url text, etag text, hash text)'
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

        parse_feeds(feed_urls)

        return


if __name__ == '__main__':
    main()
