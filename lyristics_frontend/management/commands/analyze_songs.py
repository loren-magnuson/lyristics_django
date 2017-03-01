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


def rank_words_by_frequency(word_count_dict):

    ranked_list = sorted(word_count_dict.iteritems(), key=itemgetter(1), reverse=True)
    return ranked_list


def clean_lyrics(song_lyrics):

    remove_bracketed_text_regex = re.compile("([^\(]*)\[[^\)]*\]*(.*)")
    remove_paranthetical_text_regex = re.compile("([^\(]*)\([^\)]*\)*(.*)")

    song_lyrics = remove_bracketed_text_regex.sub('', song_lyrics)
    song_lyrics = remove_paranthetical_text_regex.sub('', song_lyrics)

    return song_lyrics


def remove_stopwords(song_lyrics, language="english"):

    the_stopwords = stopwords.words(language)

    if str(type(song_lyrics)) == "<type 'collections.defaultdict'>":
        new_dict = {}
        for key, val in song_lyrics.iteritems():
            if key not in the_stopwords:
                new_dict[key] = val

        return new_dict


def get_all_songs_for_artist(artist_object):

    all_albums_by_artist = Album.objects.filter(artist_object=artist_object.id)
    all_songs = {}
    
    for album in all_albums_by_artist:

        songs_on_album = Song.objects.filter(album_object=album.id)
        all_songs[album.id] = []

        for song in songs_on_album:

            all_songs[album.id].append(song)

    return all_songs


def filter_pos_tags(song_lyrics, language="english"):

    the_blob = TextBlob(song_lyrics)
    pos_tags = the_blob.tags
    the_lemmatizer = WordNetLemmatizer()
    lemmatize_nouns = ['NN', 'NNS', 'PRP$']
    lemmatize_verbs = ['RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
    filter_tags = ['CC', 'DT', 'IN', 'TO', 'PRP', 'MD'	]
    filtered_tags = [x for x in pos_tags if x[1] not in filter_tags]
    the_stopwords = stopwords.words(language) + CUSTOM_STOPWORDS
    filtered_tags = [x for x in filtered_tags if x[0] not in the_stopwords and len(x[0]) > 1]
    lemmatized_tags = []

    for tag in filtered_tags:

        if tag[1] in lemmatize_nouns:

            lemmatized_noun = the_lemmatizer.lemmatize(tag[0], 'n')

            if lemmatized_noun != tag[0]:
                new_tag = (lemmatized_noun, tag[1])
                lemmatized_tags.append(new_tag)

        elif tag[1] in lemmatize_verbs:

            lemmatized_verb = the_lemmatizer.lemmatize(tag[0], 'v')

            if lemmatized_verb != tag[0]:
                new_tag = (lemmatized_verb, tag[1])
                lemmatized_tags.append(new_tag)

        else:
            lemmatized_tags.append(tag)

    return lemmatized_tags     


class Command(BaseCommand):

    def handle(self, *args, **options):

        self.assign_lifetime_word_frequencies()
        self.assign_language_for_songs()
        self.assign_emotionality_for_songs()
        self.assign_sentiment_for_songs()
        self.assign_grade_score_for_songs()

    def assign_lifetime_word_frequencies(self):

        artists = Artist.objects.filter(artist_name="Immortal Technique")

        for artist_object in artists:
            lifetime_lyrics = get_all_songs_for_artist(artist_object)
            lifetime_words = []

            for album_id, song_list in lifetime_lyrics.iteritems():
                album_lyrics = []

                for song_object in song_list:

                    if len(song_object.song_lyrics) > 0:
                        song_lyrics = clean_lyrics(song_object.song_lyrics[0])
                        filtered_song_lyrics = filter_pos_tags(song_lyrics)
                        lifetime_words += filtered_song_lyrics
                        album_lyrics += filtered_song_lyrics
                        song_blob = TextBlob(" ".join([x[0] for x in filtered_song_lyrics]))
                        song_word_rankings = rank_words_by_frequency(song_blob.word_counts)
                        song_object.lyric_stats['word_frequency'] = []
                        song_object.lyric_stats['word_frequency'] = [x for x in song_word_rankings[0:10]]
                        song_object.save()

                album_blob = TextBlob(" ".join([x[0] for x in album_lyrics]))
                album_word_rankings = rank_words_by_frequency(album_blob.word_counts)
                album_object = Album.objects.get(id=album_id)
                album_object.lyric_stats['word_frequency'] = []
                album_object.lyric_stats['word_frequency'] = [x for x in album_word_rankings[0:10]]
                album_object.save()

            the_blob = TextBlob(" ".join([x[0] for x in lifetime_words]))
            lifetime_word_rankings = rank_words_by_frequency(the_blob.word_counts)
            artist_object.lyric_stats['word_frequency'] = []
            artist_object.lyric_stats['word_frequency'] = [x for x in lifetime_word_rankings[0:10]]

    def assign_language_for_songs(self):

        all_songs = Song.objects.all()

        for song_object in all_songs:

            if len(song_object.song_lyrics) > 0:
                the_language = detect(song_object.song_lyrics[0])
                song_object.lyric_stats['primary_language'] = the_language
                song_object.save()

    def assign_emotionality_for_songs(self):

        e = emotuslite()
        all_songs = Song.objects.all()

        for song_object in all_songs:

            try:
                doc = song_object.song_lyrics[0]

            except IndexError:
                continue

            else:
                score = e.appraise_document(doc)
                # Threshold values (pleasure = 0.0843..., arousal = 0.0125...) come from analyzing
                # the PAD scores of several thousand songs and finding the midpoint of these values

                if (score[0] > 0.0843264048824253) and (score[1] > 0.0125793907208737):
                    emotionality = "engaging"

                elif (score[0] > 0.0843264048824253) and (score[1] < 0.0125793907208737):
                    emotionality = "soothing"

                elif (score[0] < 0.0843264048824253) and (score[1] < 0.0125793907208737):
                    emotionality = "boring"

                elif (score[0] < 0.0843264048824253) and (score[1] > 0.0125793907208737):
                    emotionality = "angry"

                else:
                    emotionality = "unknown"

                print "These lyrics are %s" % emotionality, " %s" % song_object.song_title
                song_object.lyric_stats['emotionality'] = emotionality
                song_object.save()

    def assign_sentiment_for_songs(self):

        all_songs = Song.objects.all()

        for song_object in all_songs:

            if len(song_object.song_lyrics) > 0:
                song_blob = TextBlob(song_object.song_lyrics[0])
                song_object.lyric_stats['sentiment'] = song_blob.sentiment.polarity
                song_object.save()

    def assign_grade_score_for_songs(self):

        all_songs = Song.objects.all()

        for song_object in all_songs:

            if len(song_object.song_lyrics) > 0:
                song_object.lyric_stats['grade_level'] = textstat.coleman_liau_index(song_object.song_lyrics[0])
                song_object.save()
