# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy import Field


class ArtistImageItem(scrapy.Item):
    image_urls = scrapy.Field()
    images = scrapy.Field()
    image_type = scrapy.Field()
    artist_object = scrapy.Field()
    image_paths = scrapy.Field()
    image_dicts = scrapy.Field()

class AlbumImageItem(scrapy.Item):
    album_object = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    image_type = scrapy.Field()
    image_paths = scrapy.Field()
