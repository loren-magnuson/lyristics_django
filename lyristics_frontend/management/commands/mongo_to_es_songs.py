from django.core.management.base import BaseCommand, CommandError
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
import sys
from lyristics_frontend.models import Artist, Album, Song


class Command(BaseCommand):
    def handle(self, *args, **options):
        def generate_es_song_data():
            for song in Song.objects.all():
                # Index for elasticsearch.
                idx = song.id
                parent_id = song.album_object
                es_fields_keys = ('song_title', 'song_lyrics')
                try:
                    es_fields_vals = (song.song_title, song.song_lyrics[0])
                except IndexError:
                    es_fields_vals = (song.song_title, '')

                # We return a dict holding values from each line
                es_song_data = dict(zip(es_fields_keys, es_fields_vals))

                # Return the row on each iteration
                yield idx, parent_id, es_song_data  # <- Note the usage of 'yield'

        def es_add_bulk():
            # The nginx file can be gzip or just text. Open it appropriately.

            es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200}])

            # NOTE the (...) round brackets. This is for a generator.
            k = ({
                     "_index": "lyristics",
                     "_type": "album",
                     "_parent": parent_id,
                     "_id": idx,

                     "_source": es_song_data,
                 } for idx, parent_id, es_song_data in generate_es_song_data())

            helpers.bulk(es, k)

        es_add_bulk()

        # es = Elasticsearch()
        # songs = Song.objects.all()
        # for song in songs:
        #
        #     doc = {
        #         'song_title': song.song_title,
        #         'parent': song.album_object,
        #         'song_lyrics': song.song_lyrics[0]
        #     }
        #     res = es.index(index="lyristics", doc_type='song', id=song.id, body=doc)
        #
        #
        #     print(res['created'])