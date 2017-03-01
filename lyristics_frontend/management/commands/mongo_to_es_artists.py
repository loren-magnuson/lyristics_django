from django.core.management.base import BaseCommand, CommandError
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
import sys
from lyristics_frontend.models import Artist, Album, Song


class Command(BaseCommand):

    def handle(self, *args, **options):

        def generate_es_artists_data():
            for artist in Artist.objects.all():

                # Index for elasticsearch.
                idx = artist.id

                es_fields_keys = ['artist_name']
                es_fields_vals = [artist.artist_name]

                # We return a dict holding values from each line
                es_artist_data = dict(zip(es_fields_keys, es_fields_vals))
                print es_artist_data
                # Return the row on each iteration
                yield idx, es_artist_data  # <- Note the usage of 'yield'

        def es_add_bulk():

            es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200}])

            # NOTE the (...) round brackets. This is for a generator.
            k = ({
                     "_index": "lyristics",
                     "_type": "artist",
                     "_id": idx,
                     "_source": es_artist_data,
                 } for idx, es_artist_data in generate_es_artists_data())

            helpers.bulk(es, k)

        es_add_bulk()
        # es = Elasticsearch()
        # artists = Artist.objects.all()
        # for artist in artists:
        #
        #     doc = {
        #         'artist_name': artist.artist_name,
        #     }
        #     res = es.index(index="lyristics", doc_type='artist', id=artist.id, body=doc)
        #
        #
        #     print(res['created'])
        #
