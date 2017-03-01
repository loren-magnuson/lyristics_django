# -*- coding: utf-8 -*-
import sys
import scrapy
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from lyristics_frontend.models import Artist, artistLetters, Album, Song
from lyristics_scrapy.items import AlbumImageItem, ArtistImageItem
from scrapy import Request
from scrapy_splash import SplashRequest

IMAGE_TYPES = ['wikipedia', 'twitter', 'myspace']
url_root = "http://lyrics.wikia.com"


class LyricsWikiSpider(scrapy.Spider):

    name = "lyrics_wiki"
    allowed_domains = ["lyrics.wikia.com", 'nocookie.net', 'myspace.com', 'facebook.com',
                       'twitter.com', 'wikipedia.org']

    def __init__(self, scan_type=None, get_images=False, get_lyrics=False):
        self.start_urls = []
        self.get_lyrics = get_lyrics
        self.get_images = get_images

        if scan_type is None:
            sys.exit()

        else:
            self.scan_type = scan_type

    def start_requests(self):

        if self.scan_type == "create_artists_db":
            yield Request("http://lyrics.wikia.com/wiki/Lyrics_Wiki", self.get_all_artist_letters)

        elif self.scan_type == "create_albums_db":
            artists_list = Artist.objects.filter(artist_name="Immortal Technique")

            for a in artists_list:
                new_request = Request(a.artist_url, self.get_albums_by_artist)
                new_request.meta['artist_object'] = a
                yield new_request

        elif self.scan_type == "create_lyrics_db":
            songs_list = Song.objects.filter(song_title="Sierra Maestra")
            redlink = str("redlink=")

            for song in songs_list:
                song_url = song.song_url.encode('ascii', 'ignore')

                if redlink not in song_url:
                    new_request = SplashRequest("http://lyrics.wikia.com" + song_url, self.scrape_lyrics,
                                                endpoint='render.html',
                                                args={'wait': 4.0})
                    new_request.meta['retries'] = 0
                    new_request.meta['song_object'] = song
                    yield new_request

        elif self.scan_type == "update_lyrics_db":
            songs_list = Song.objects.filter(song_lyrics=[])
            redlink = str("redlink=")

            for song in songs_list:
                song_url = song.song_url.encode('ascii', 'ignore')

                if redlink not in song_url:
                    new_request = SplashRequest("http://lyrics.wikia.com" + song_url,
                                                self.scrape_lyrics,
                                                endpoint='render.html',
                                                args={'wait': 4.0})
                    new_request.meta['retries'] = 0
                    new_request.meta['song_object'] = song
                    yield new_request

    def get_all_artist_letters(self, response):

        artists_tab = response.css("#mpWelcome div.tabbertab")[0]
        for i in artists_tab.css("p > a"):
            artist_letter = i.css("::text").extract()[0]
            artist_letter_url = url_root + i.css("::attr(href)").extract()[0]
            artist_letter_object = artistLetters.objects.create(artist_letter=artist_letter,
                                                                artist_letter_url=artist_letter_url)
            
            if artistLetters.objects.filter(artist_letter=artist_letter):
                print "Found existing artist letter: %s" % artist_letter
            
            else:
                artist_letter_object.save()
            
            new_request = Request(artist_letter_url, self.get_all_artists)
            yield new_request

    def get_all_artists(self, response):
        artist_links = response.css("#mw-pages table ul li a")

        for i in artist_links:
            artist_name = i.css("::text").extract()[0]
            artist_url = url_root + i.css("::attr(href)").extract()[0]

            if Artist.objects.filter(artist_url=artist_url):
                print "Found existing artist: %s" % artist_name

            else:
                artist_object = Artist.objects.create(artist_name=artist_name,
                                                      artist_url=artist_url)
                artist_object.save()

            next_button_url = response.css(".paginator-next::attr(href)")
            if next_button_url:
                next_page_url = next_button_url.extract()[0]
                new_request = Request(next_page_url, self.get_all_artists)
                new_request.meta['is_next_page'] = True
                yield new_request

    def get_albums_by_artist(self, response):

        artist_object = response.request.meta['artist_object']

        external_links = response.css("#mw-content-text div.plainlinks")
        if external_links:
            links_list = []

            for row in external_links:
                link_label = row.xpath("./text()").extract()[0].replace(":", "")
                link_url = row.css("a::attr(href)").extract()[0]
                links_list.append({'label': link_label, 'url': link_url})
            
            artist_object.external_links = links_list
            artist_object.save()

        related_links = response.css("#mw-content-text table.plainlinks:nth-child(1) a.external")
        if related_links:
            links_list = []

            for row in related_links:
                link_label = row.xpath("./text()").extract()[0]
                link_url = row.css("::attr(href)").extract()[0]
                links_list.append({'label': link_label, 'url': link_url})

                normalize_link_label = link_label.split(" ")[0].lower()

                if normalize_link_label in IMAGE_TYPES and self.get_images:
                    the_image_callback = "self.parse_%s" % normalize_link_label
                    print "yielding image request to ", the_image_callback, link_url
                    image_request = Request(url=link_url, callback=eval(the_image_callback))
                    image_request.meta['artist_object'] = artist_object
                    yield image_request

            artist_object.related_links = links_list
            artist_object.save()

        wikipedia_link = response.css("#mw-content-text table.plainlinks tr a.extiw")
        if wikipedia_link:
            row = wikipedia_link[0]
            link_label = row.css("::text").extract()[0]
            link_url = row.css("::attr(href)").extract()[0]
            artist_object.related_links.append({'label': link_label, 'url': link_url})
            artist_object.save()

            if self.get_images:
                image_request = Request(url=link_url, callback=self.parse_wikipedia)
                image_request.meta['artist_object'] = artist_object
                image_request.meta['image_type'] = 'wikipedia'
                yield image_request

        artist_info_table = response.css(".artist-info-box tr")

        if artist_info_table:
            print "Scraping artist info"
            section_label_elements = artist_info_table.xpath(".//div/b")

            for section_label_element in section_label_elements:
                label = section_label_element.xpath(".//text()").extract()[0].replace(":", "")

                if not label:
                    continue
                
                data_element = section_label_element.xpath("../../following-sibling::div[1]")
                data = None
                if data_element.xpath(".//p/b"):
                    data = data_element.xpath(".//p/b/text()").extract()

                elif data_element.xpath(".//ul/li/b"):
                    data = data_element.xpath(".//ul/li/b/text()").extract()

                elif data_element.xpath(".//ul/li/b/a"):
                    data = data_element.xpath(".//ul/li/b/a/text()").extract()

                elif data_element.xpath(".//ul/li/a"):
                    data = data_element.xpath(".//ul/li/a/text()").extract()
            
                if data:
                    artist_object.artist_info[label.replace(".", "")] = data
                    artist_object.save()

        country = response.xpath("//table//a[contains(@href, 'Hometown')]/b/text()")
        if country:
            artist_object.artist_info['country'] = country.extract()[0]
            artist_object.save()

        locality_and_city = response.xpath("//table//a[contains(@href, 'Hometown')]/text()")

        if locality_and_city:
            artist_object.artist_info['locality'] = locality_and_city.extract()[0]

            if len(locality_and_city) == 2:
                artist_object.artist_info['city'] = locality_and_city.extract()[1]
   
            artist_object.save()

        the_headers = response.css("#mw-content-text > h2 span.mw-headline")
        the_images = response.css("#mw-content-text > .tright a.image-thumbnail")
        the_ols = response.css("#mw-content-text > ol")
        the_uls = response.css('#mw-content-text > ul')
        the_lists = the_ols + the_uls

        for idx, header in enumerate(the_headers):
            header_url = None
            
            if header.css("a"):
                header_text = header.css("a::text").extract()[0]
                header_url = header.css("a::attr(href)").extract()[0]

            else:
                header_text = header.css("::text").extract()[0]
                if header_text == "Additional information":
                    continue

            if header_text == "Genres":
                continue

            else:
                album_dict = {'artist_object': artist_object.id,
                              'album_title': header_text}

                if header_url:
                    album_dict['album_url'] = header_url
            
                try:
                    Album.objects.get(artist_object=album_dict['artist_object'],
                                      album_title=album_dict['album_title'])
            
                except ObjectDoesNotExist:
                    album_object = Album.objects.create(**album_dict)
                    album_object.save()
            
                else:
                    print "found existing album %s for artist %s ... updating" % (album_dict['album_title'], artist_object.artist_name)
                    album_object = Album.objects.get(artist_object=album_dict['artist_object'],
                                                     album_title=album_dict['album_title'])

                try:
                    album_image = the_images[idx]

                except IndexError:
                    pass

                else:
                    item = AlbumImageItem()
                    item['album_object'] = album_object
                    item['image_urls'] = album_image.css("::attr(href)").extract()
                    yield item

                song_list = the_lists[idx].css("li > b > a")
                track_list = []

                for song in song_list:
                    song_title = song.css("::text").extract()[0]
                    song_url = song.css("::attr(href)").extract()[0]
                    print song_title

                    try:
                        Song.objects.get(album_object=album_object.id, song_title=song_title)

                    except ObjectDoesNotExist:
                        song_object = Song.objects.create(song_title=song_title,
                                                          song_url=song_url,
                                                          album_object=album_object.id)                    
                        song_object.save()

                    else:
                        print "Found existing song ", song_title, "... updating"
                        song_object = Song.objects.get(album_object=album_object.id, song_title=song_title)
                    
                    finally:

                        track_list.append(song_object.id)

                        if "redlink" not in song_url and self.get_lyrics:
                            new_request = SplashRequest("http://lyrics.wikia.com" + song_url,
                                                        self.scrape_lyrics,
                                                        endpoint='render.html',
                                                        args={'wait': 4.0})
                            new_request.meta['retries'] = 0
                            new_request.meta['song_object'] = song_object
                            yield new_request

                print "saving track list for %s" % album_object.album_title
                album_object.track_list = track_list
                album_object.save()

        artist_object.last_scraped = timezone.now()
        artist_object.save()

    def scrape_lyrics(self, response):

        song_object = response.request.meta['song_object']
        retries = response.request.meta['retries']
        lyric_box = response.css("div.lyricbox")
        lyrics = lyric_box.xpath("./text()").extract()
    
        if lyrics:
            print "Lyrics downloaded for ", song_object.song_title, " @ ", response.url
            song_object.song_lyrics = []
            song_is_instrumental = response.css("div.lyricbox > b::text")

            if song_is_instrumental:

                if song_is_instrumental.extract()[0] == "Instrumental":
                    song_object.song_lyrics = ["Instrumental"]

                else:
                    print song_is_instrumental.extract()[0]

            else:
                song_object.song_lyrics = ["\n".join(lyrics)]

            song_object.save()

            external_links = response.css("#mw-content-text div.plainlinks")

            if external_links:
                links_list = []

                for row in external_links:
                    link_label = row.xpath("./text()").extract()[0].replace(":", "")
                    link_url = row.css("a::attr(href)").extract()[0]
                    links_list.append({'label': link_label, 'url': link_url})

                song_object.external_links = links_list
                song_object.save()

        elif response.request.meta['retries'] < 5:
            new_request = SplashRequest("http://lyrics.wikia.com" + song_object.song_url,
                                        self.scrape_lyrics,
                                        endpoint='render.html',
                                        args={'wait': 4.0})

            new_request.meta['retries'] = 1 + retries
            new_request.meta['song_object'] = song_object
            yield new_request

    def parse_twitter(self, response):

        item = ArtistImageItem()
        item['artist_object'] = response.request.meta['artist_object']
        item['image_type'] = "twitter"
        img_urls, img_dicts = [], []

        img_elements = response.css("div.ProfileAvatar img")

        if img_elements:

            for img_element in img_elements:
                img_url = img_element.css("::attr(src)").extract()[0]

                if img_url in img_urls:
                    continue

                else:
                    img_urls.append(img_url)
                    img_dicts.append({'url': img_url})

        if img_dicts and img_urls:
            item['image_dicts'] = img_dicts
            item['image_urls'] = img_urls
            return item

        else:
            print "No twitter image found for ", item['artist_object'].artist_name, response.url
            return None


    def parse_myspace(self, response):

        item = ArtistImageItem()
        item['artist_object'] = response.request.meta['artist_object']
        item['image_type'] = "myspace"
        img_elements = response.css("#profileImage img")
        img_urls, img_dicts = [], []

        if img_elements:

            for img_element in img_elements:
                img_url = img_element.css("::attr(src)").extract()[0]

                if img_url in img_urls:
                    continue

                else:
                    img_urls.append(img_url)
                    img_dicts.append({'url': img_url})

        if img_dicts and img_urls:
            item['image_dicts'] = img_dicts
            item['image_urls'] = img_urls
            return item

        else:
            print "No myspace image found for ", item['artist_object'].artist_name, response.url
            return None

    def parse_wikipedia(self, response):

        item = ArtistImageItem()
        item['artist_object'] = response.request.meta['artist_object']
        img_urls = []
        img_dicts = []
        item['image_type'] = "wikipedia"
        img_elements = response.css("table.infobox.vcard.plainlist a img")

        if img_elements:

            for img_element in img_elements:
                img_url = "https:%s" % img_element.css("::attr(src)").extract()[0]

                if img_url in img_urls:
                    continue

                img_dicts.append({'url': img_url})
                img_urls.append(img_url)

        img_elements = response.css("#mw-content-text div.thumbinner")

        if img_elements:

            for img_element in img_elements:
                img_dict = {}
                img_element = img_element.css("a:nth-child(1) > img::attr(src)")

                if not img_url:
                    continue

                if img_url in img_urls:
                    continue

                img_dict['url'] = img_url
                img_urls.append("https:%s" % img_element.extract()[0])
                img_caption = img_element.css(".thumbcaption")

                if img_caption:
                    img_dict['caption'] = img_caption.xpath("./text()").extract()[0]

                img_dicts.append(img_dict)

        if img_dicts and img_urls:
            item['image_dicts'] = img_dicts
            item['image_urls'] = img_urls
            return item

        else:
            print "No wikipedia images found for ", item['artist_object'].artist_name, response.url
            return None
