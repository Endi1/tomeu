import os
import sqlite3
from os.path import isfile
import argparse

from .index import Index
from .feed import Feed


def create_index():
    index = Index()
    content = index.generate_index()
    f = open('index.html', 'w+')
    f.write(content)
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

    create_index()


if __name__ == '__main__':
    main()
