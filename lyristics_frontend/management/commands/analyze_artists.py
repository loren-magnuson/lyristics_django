from django.core.management.base import BaseCommand
from lyristics_frontend.models import Artist, Album, Song
from textblob import TextBlob
import re
from operator import itemgetter
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import cPickle, sys, os
from textstat.textstat import textstat
from sumy.parsers.html import HtmlParser
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from langdetect import detect
from lyristics_django.analysis_libs.Lyricator.lyricator import emotuslite

LANGUAGE = "english"
SENTENCES_COUNT = 1
CUSTOM_STOPWORDS = ["n't", "'m", "'s", "'ll"]


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.assign_languages_for_artists()
        self.assign_emotionality_for_artists()
        self.assign_sentiment_for_artists()
        self.assign_grade_score_for_artists()

    def assign_languages_for_artists(self):

        # all_artists = Artist.objects.all()
        all_artists = Artist.objects.filter(artist_name="Immortal Technique")

        for artist_object in all_artists:
            songs_by_artist = Song.objects.filter(artist_object=artist_object.id)
            languages_seen = {}

            for song_object in songs_by_artist:

                if 'primary_language' in song_object.lyric_stats:
                    the_language = song_object.lyric_stats['primary_language']

                    if the_language in languages_seen:
                        languages_seen[the_language] += 1

                    else:
                        languages_seen[the_language] = 1

            if languages_seen:
                ranked_languages = sorted(languages_seen.iteritems(), key=itemgetter(1), reverse=True)
                artist_object.lyric_stats['primary_language'] = []
                artist_object.lyric_stats['primary_language'] = ranked_languages[0][0]
                artist_object.lyric_stats['secondary_languages'] = []

                if len(languages_seen) > 1:
                    for language in ranked_languages[1:]:
                        print language
                        artist_object.lyric_stats['secondary_languages'].append(language[0])

                print languages_seen
                artist_object.save()

    def assign_emotionality_for_artists(self):

        # all_artists = Artist.objects.all()
        all_artists = Artist.objects.filter(artist_name="Immortal Technique")

        for artist_object in all_artists:
            songs_by_artist = Song.objects.filter(artist_object=artist.id)
            emotionalities_seen = {}

            for song_object in songs_by_artist:

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
                artist_object.lyric_stats['primary_emotionality'] = []
                artist_object.lyric_stats['primary_emotionality'] = ranked_emotionalities[0][0]
                artist_object.lyric_stats['secondary_emotionalities'] = []

                if len(emotionalities_seen) > 1:

                    for emotion in ranked_emotionalities[1:]:
                        print emotion
                        artist_object.lyric_stats['secondary_emotionalities'].append(emotion[0])

                artist_object.save()

    def assign_sentiment_for_artists(self):
        all_artists = Artist.objects.all()

        for artist_object in all_artists:
            sentiment_scores = []
            songs_by_artist = Song.objects.filter(artist_object=artist_object.id)

            for song_object in songs_by_artist:

                if 'sentiment' in song_object.lyric_stats:
                    sentiment_scores.append(song_object.lyric_stats['sentiment'])

            if sentiment_scores:
                artist_object.lyric_stats['sentiment'] = sum(sentiment_scores) / len(sentiment_scores)
                artist_object.save()

    def assign_grade_score_for_artists(self):
        all_artists = Artist.objects.all()

        for artist_object in all_artists:
            grade_scores = []
            songs_by_artist = Song.objects.filter(artist_object=artist_object.id)

            for song_object in songs_by_artist:

                if 'grade_level' in song_object.lyric_stats:
                    grade_scores.append(song_object.lyric_stats['grade_level'])

            if grade_scores:
                artist_object.lyric_stats['grade_level'] = sum(grade_scores) / len(grade_scores)
                artist_object.save()