import os
import shutil
import hashlib
import sqlite3
import feedparser

from datetime import datetime
from .entry import Entry


class Feed():
    def __init__(self, url: str):
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
            self._parse_feed(c)
        elif not self._needs_update(c):
            return

        self._delete_old_entries(c)

        self._parse_feed(c)

        conn.commit()
        c.close()

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
            (self.url,)
        )

        last_delete = c.fetchone()[0]
        week_last_delete = last_delete.isocalendar()[1]
        current_week_time = datetime.now().isocalendar()[1]

        if current_week_time - week_last_delete >= 1:
            shutil.rmtree(self.d.feed.title)

    def _parse_feed(self, c):
        feed_title = self.d.feed.title

        # Reset folders every week

        if not os.path.exists(feed_title):
            os.makedirs(feed_title)

        for entry in self.d.entries:
            e = Entry(entry, feed_title)
            e.save()

        return
