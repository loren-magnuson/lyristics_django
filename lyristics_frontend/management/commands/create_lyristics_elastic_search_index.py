from django.core.management.base import BaseCommand
from elasticsearch.helpers import bulk
from elasticsearch.client import IndicesClient
from lyristics_django import settings
from lyristics_frontend.models import Artist


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.recreate_index()
        self.push_db_to_index()

    def recreate_index(self):

        indices_client = IndicesClient(client=settings.ES_CLIENT)
        index_name = Artist._meta.es_index_name
        if indices_client.exists(index_name):
            indices_client.delete(index=index_name)
        indices_client.create(index=index_name)
        indices_client.put_mapping(doc_type=Artist._meta.es_type_name,
                                   body=Artist._meta.es_mapping,
                                   index=index_name
                                  )
    # def recreate_index(self):
    #     es = Elasticsearch()
    #     if es.indices.exists("lyristics"):
    #         print "Lyristics elastic search index already exists... deleting"
    #         es.indices.delete(index="lyristics")
    #     mapping = {
    #         "mappings": {
    #             "artist": {
    #                 "properties": {
    #                     'artist_name': {
    #                         "type": "string",
    #                         "index": "analyzed"
    #
    #                     },
    #                     'name_complete': {
    #                         'type': 'completion',
    #                         'analyzer': 'simple',
    #                         'payloads': True,
    #                         'preserve_separators': True,
    #                         'preserve_position_increments': True,
    #                         'max_input_length': 50,
    #                     },
    #                 }
    #             },
    #             "album": {
    #                 "_parent": {
    #                     "type": "artist"
    #                 },
    #
    #                 "properties": {
    #                     "album_title": {
    #                         "type": "string",
    #                         "index": "analyzed"
    #                     }
    #                 }
    #             },
    #             "song": {
    #                 "_parent": {
    #                     "type": "album"
    #                 },
    #                 "properties": {
    #                     "song_title": {
    #                         "type": "string",
    #                         "index": "analyzed"
    #                     },
    #                     "song_lyrics": {
    #                         "type": "string",
    #                         "index": "analyzed"
    #                     }
    #                 }
    #             },
    #         }
    #         }

    #    res = es.indices.create(index="lyristics", ignore=400, body=mapping)
    #
    #     if 'acknowledged' in res:
    #         print "Lyristics Index Created"
    #     else:
    #         print res
    #         print "Failed to Create Lyristics Index"

    def push_db_to_index(self):

        data = [
            self.convert_for_bulk(s, 'create') for s in Artist.objects.all()
            ]

        bulk(client=settings.ES_CLIENT,
             actions=data,
             stats_only=True,
             chunk_size=1000,
             request_timeout=30)

    def convert_for_bulk(self, django_object, action=None):
        data = django_object.es_repr()
        metadata = {
            '_op_type': action,
            "_index": django_object._meta.es_index_name,
            "_type": django_object._meta.es_type_name,
        }
        data.update(**metadata)
        return data