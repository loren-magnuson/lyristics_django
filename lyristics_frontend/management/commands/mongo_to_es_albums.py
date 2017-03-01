from django.core.management.base import BaseCommand, CommandError
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
import sys
from lyristics_frontend.models import Artist, Album, Song


class Command(BaseCommand):
    def handle(self, *args, **options):
        def generate_es_album_data():
            for album in Album.objects.all():
                # Index for elasticsearch.
                idx = album.id
                parent_id = album.artist_object
                es_fields_keys = ('album_title')
                es_fields_vals = (album.album_title)

                # We return a dict holding values from each line
                es_album_data = dict(zip(es_fields_keys, es_fields_vals))

                # Return the row on each iteration
                yield idx, parent_id, es_album_data  # <- Note the usage of 'yield'

        def es_add_bulk():
            # The nginx file can be gzip or just text. Open it appropriately.

            es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200}])

            # NOTE the (...) round brackets. This is for a generator.
            k = ({
                     "_index": "lyristics",
                     "_type": "album",
                     "_id": idx,
                     "_parent": parent_id,
                     "_source": es_album_data,
                 } for idx, parent_id, es_album_data in generate_es_album_data())

            helpers.bulk(es, k)
        es_add_bulk()

        # es = Elasticsearch()
        # albums = Album.objects.all()
        # for album in albums:
        #
        #     doc = {
        #         'parent': album.artist_object,
        #         'album_title': album.album_title,
        #     }
        #     res = es.index(index="lyristics", doc_type='album', id=album.id, body=doc)
        #
        #
        #     print(res['created'])