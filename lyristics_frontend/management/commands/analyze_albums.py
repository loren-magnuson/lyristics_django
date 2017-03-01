from django.core.management.base import BaseCommand
from lyristics_frontend.models import Artist, Album, Song
from operator import itemgetter
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

LANGUAGE = "english"
SENTENCES_COUNT = 1
CUSTOM_STOPWORDS = ["n't", "'m", "'s", "'ll"]

class Command(BaseCommand):

    def handle(self, *args, **options):
        self.assign_languages_for_albums()
        self.assign_emotionality_for_albums()
        self.assign_sentiment_for_albums()
        self.assign_grade_score_for_albums()

    def assign_languages_for_albums(self):

        # all_artists = Artist.objects.all()
        all_artists = Artist.objects.filter(artist_name="Immortal Technique")

        for album_object in all_artists:
            albums_by_artist = Album.objects.filter(artist_object=album_object.id)

            for album_object in albums_by_artist
                songs_on_album = Song.objects.filter(album_object=album_object.id)
                languages_seen = {}

                for song_object in songs_on_album:

                    if 'primary_language' in song_object.lyric_stats:
                        the_language = song_object.lyric_stats['primary_language']

                        if the_language in languages_seen:
                            languages_seen[the_language] += 1

                        else:
                            languages_seen[the_language] = 1

                if languages_seen:
                    ranked_languages = sorted(languages_seen.iteritems(), key=itemgetter(1), reverse=True)
                    album_object.lyric_stats['primary_language'] = []
                    album_object.lyric_stats['primary_language'] = ranked_languages[0][0]
                    album_object.lyric_stats['secondary_languages'] = []

                    if len(languages_seen) > 1:
                        for language in ranked_languages[1:]:
                            print language
                            album_object.lyric_stats['secondary_languages'].append(language[0])

                    print languages_seen
                    album_object.save()

    def assign_emotionality_for_albums(self):

        # all_artists = Artist.objects.all()
        all_artists = Artist.objects.filter(artist_name="Immortal Technique")

        for album_object in all_artists:
            albums_by_artist = Album.objects.filter(artist_object=album_object.id)

            for album_object in albums_by_artist:
                songs_on_album = Song.objects.filter(album_object=album_object.id)
                emotionalities_seen = {}

                for song_object in songs_on_album:

                    if 'emotionality' in song_object.lyric_stats:
                        the_emotionality = song_object.lyric_stats['emotionality']

                        if the_emotionality in emotionalities_seen:
                            emotionalities_seen[the_emotionality] += 1

                        else:
                            emotionalities_seen[the_emotionality] = 1

                if emotionalities_seen:
                    ranked_emotionalities = sorted(emotionalities_seen.iteritems(),
                                                   key=itemgetter(1),
                                                   reverse=True)
                    album_object.lyric_stats['primary_emotionality'] = []
                    album_object.lyric_stats['primary_emotionality'] = ranked_emotionalities[0][0]
                    album_object.lyric_stats['secondary_emotionalities'] = []

                    if len(emotionalities_seen) > 1:

                        for emotion in ranked_emotionalities[1:]:
                            print emotion
                            album_object.lyric_stats['secondary_emotionalities'].append(emotion[0])

                    album_object.save()

    def assign_sentiment_for_albums(self):
        all_artists = Artist.objects.all()

        for artist_object in all_artists:
            albums_by_artist = Album.objects.filter(artist_object=artist_object.id)

            for album_object in albums_by_artist:
                sentiment_scores = []
                songs_on_album = Song.objects.filter(album_object=album_object.id)

                for song_object in songs_on_album:

                    if 'sentiment' in song_object.lyric_stats:
                        sentiment_scores.append(song_object.lyric_stats['sentiment'])

                if sentiment_scores:
                    album_object.lyric_stats['sentiment'] = sum(sentiment_scores) / len(sentiment_scores)
                    album_object.save()

    def assign_grade_score_for_albums(self):
        all_artists = Artist.objects.all()

        for artist_object in all_artists:
            albums_by_artist = Album.objects.filter(artist_object=artist_object.id)

            for album_object in albums_by_artist:
                grade_scores = []
                songs_on_album = Song.objects.filter(album_object=album_object.id)

                for song_object in songs_on_album:

                    if 'grade_level' in song_object.lyric_stats:
                        grade_scores.append(song_object.lyric_stats['grade_level'])

                if grade_scores:
                    album_object.lyric_stats['grade_level'] = sum(grade_scores) / len(grade_scores)
                    album_object.save()

    def create_album_summaries(self):

        artists = Artist.objects.filter(artist_name="Immortal Technique")

        for artist_object in artists:
            all_albums_by_artist = Album.objects.filter(artist_object=artist_object.id)

            for album_object in all_albums_by_artist:
                songs_on_album = Song.objects.filter(album_object=album_object.id)

                for song_object in songs_on_album:
                    stemmer = Stemmer(LANGUAGE)
                    summarizer = Summarizer(stemmer)
                    summarizer.stop_words = get_stop_words(LANGUAGE)

                    if len(song_object.song_lyrics) > 0:

                        song_lyrics = song_object.song_lyrics[0]
                        parser = PlaintextParser.from_string(song_lyrics, Tokenizer(LANGUAGE))

                        for sentence in summarizer(parser.document, SENTENCES_COUNT):
                            print(sentence), song_object.song_title
                            # raw_input("Press Enter to continue...")