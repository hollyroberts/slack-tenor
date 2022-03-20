import json
import sqlite3
import os
import random
from sqlite3 import Connection

import requests

from database import Database
from image import Image


class Tenor:
    TENOR_API_KEY = os.environ.get("TENOR_API_KEY")
    TENOR_SEARCH_URL = "https://g.tenor.com/v1/random"
    TENOR_LOCALE = "en_GB"

    LIMIT = 5

    db = sqlite3.connect("database.db")

    def __init__(self, block_uid):
        self.block_uid = block_uid

    def next_image(self):
        with Database() as db:
            previous_image = self.__set_image_as_used_and_get(db)
            next_image = self.__next_image_from_db(db)
            if next_image is None:
                print(f"No more images stored for request {self.block_uid}")

                pos = None
                if previous_image is not None:
                    pos = previous_image['next_pos']
                    if pos is None:
                        raise f"Had a previous gif without next position for request {self.block_uid}. " \
                                f"Previous image id: {previous_image['id']}"
                self.__query_tenor(db, pos)
                next_image = self.__next_image_from_db(db)
                if next_image is None:
                    raise f"Tried fetching more images, but could not fetch more from the DB"

            return Tenor.__unpack_gif_object_from_db(next_image)

    def get_send_image_and_delete_others(self):
        with Database() as db:
            send_image = self.__set_image_as_used_and_get(db)
            if send_image is None:
                raise f"Could not get image to send for request {self.block_uid}"

            deleted_rows = db.execute("""
                DELETE FROM tenor_result
                WHERE id IN (
                    SELECT tr.id FROM tenor_result tr
                    INNER JOIN slack_request sr ON (sr.id = tr.slack_request_id)
                    WHERE block_uid = ?
                    AND tr.status = 'FETCHED'
                )
                """, (self.block_uid, )).rowcount
            print(f"Deleted {deleted_rows} unused requests for request {self.block_uid}")
            return Tenor.__unpack_gif_object_from_db(send_image)

    @staticmethod
    def __unpack_gif_object_from_db(db_result):
        return Image(json.loads(db_result['gif_object']))

    def __set_image_as_used_and_get(self, db: Connection):
        return self.__record_state_transition(db, 'SELECTING', 'USED')

    def __next_image_from_db(self, db: Connection):
        return self.__record_state_transition(db, 'FETCHED', 'SELECTING')

    def __record_state_transition(self, db: Connection, old_status: str, new_status: str):
        return db.execute("""
            UPDATE tenor_result
            SET status = ?
            WHERE id = (
                SELECT tr.id FROM tenor_result tr
                INNER JOIN slack_request sr ON (tr.slack_request_id = sr.id)
                WHERE sr.block_uid = ?
                AND tr.status = ?
                ORDER BY position ASC
                LIMIT 1
            )
            RETURNING *
            """, (new_status, self.block_uid, old_status)).fetchone()

    def __query_tenor(self, db: Connection, next_pos):
        search_string = db.execute("SELECT search_string FROM slack_request WHERE block_uid = ?", (self.block_uid, ))\
            .fetchone()['search_string']

        print(f"Fetching results from tenor for request {self.block_uid} with query string: {search_string}")
        resp = requests.get(Tenor.TENOR_SEARCH_URL, params={
            "key": Tenor.TENOR_API_KEY,
            "q": search_string,
            "locale": Tenor.TENOR_LOCALE,
            "limit": 5,
            "media_filter": "default",
            "ar_range": "all",
            "pos": next_pos
        })
        if not resp.ok:
            raise f"Got status code {resp.status_code} for tenor request"

        content = json.loads(resp.content)
        next_pos = content['next']
        results = content['results']

        print(f"Fetched {len(results)} from tenor for request {self.block_uid}")

        for i, obj in enumerate(results, start=0):
            if i + 1 == len(results):
                pos = next_pos
            else:
                pos = None

            cursor = db.execute("""
                INSERT INTO tenor_result (slack_request_id, position, gif_object, status, next_pos)
                SELECT
                    sr.id,
                    COALESCE(MAX(position), 0) + 1,
                    ?,
                    'FETCHED',
                    ?
                FROM slack_request sr
                LEFT JOIN tenor_result tr ON (sr.id = tr.slack_request_id)
                WHERE sr.block_uid = ?
                GROUP BY sr.id
                """, (json.dumps(results[i]), pos, self.block_uid))
            if cursor.rowcount != 1:
                raise f"Error inserting row for request {self.block_uid}"

        print(f"Inserted rows for request {self.block_uid}")