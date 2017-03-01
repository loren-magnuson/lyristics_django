from django.db import models
from djangotoolbox.fields import ListField, DictField, EmbeddedModelField

import django.db.models.options as options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    'es_index_name', 'es_type_name', 'es_mapping'
)

class artistLetters(models.Model):
    artist_letter = models.CharField(max_length=10, null=False)
    artist_letter_url = models.CharField(max_length=255, null=False)


class Artist(models.Model):
    artist_name = models.CharField(max_length=255, null=False)
    artist_url = models.CharField(max_length=255, null=False)
    genres = ListField()
    external_links = ListField()
    related_links = ListField()
    artist_images = ListField()
    artist_info = DictField()
    lyric_stats = DictField()

    def es_repr(self):
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.pk
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data

    def field_es_repr(self, field_name):

        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()

        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)

        return field_es_value

    def get_es_name_complete(self):
        return {
                "input": [self.artist_name]
        }

    def get_es_genres(self):
        return [genre for genre in self.genres]
               
             
    class Meta:
        es_index_name = 'lyristics'
        es_type_name = 'artist'
        es_mapping = {
            'properties': {
                'artist_name': {
                    'type': 'string'
                },
                'genres': {
                     'type': 'string',
                     'index': 'not_analyzed'
                },

                'name_complete': {
                     'type': 'completion',
                     'analyzer': 'simple',
                #     'payloads': True,
                     'preserve_separators': True,
                     'preserve_position_increments': True,
                     'max_input_length': 50,
                },

            }
        }

        # es_mapping = {
        #     'properties': {
        #         'artist_name': {
        #             'type': 'string'
        #         },
        #         'name_complete': {
        #             'type': 'completion',
        #             'analyzer': 'simple',
        #             'search_analyzer': 'simple',
        #             'payloads': True,
        #             'preserve_separators': True,
        #             'preserve_position_increments': True,
        #             'max_input_length': 50,
        #         },
        #
        #     }
        # }


class Album(models.Model):
    album_title = models.CharField(max_length=255, null=False)
    album_url = models.CharField(max_length=255, null=False)
    artist_object = models.CharField(max_length=255, null=False)
    track_list = ListField()
    lyric_stats = DictField()
    album_image = models.CharField(max_length=255, null=False)


class Song(models.Model):
    song_title = models.CharField(max_length=255, null=False)
    song_url = models.CharField(max_length=255, null=False)
    album_object = models.CharField(max_length=255, null=False)
    artist_object = models.CharField(max_length=255, null=False)
    external_links = ListField()
    song_lyrics = ListField()
    lyric_stats = DictField()

