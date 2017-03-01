# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
import hashlib


class ImagesScrapyPipeline(ImagesPipeline):

    def file_path(self, request, response=None, info=None,):
        image_guid = hashlib.sha1(request.url).hexdigest()

        item = request.meta['item']
        if 'artist_object' in item and 'image_type' in item:
            the_file_path = "artists/%s/%s.jpg" % (item['image_type'], image_guid)

        elif 'album_object' in item:
            the_file_path = 'albums/%s.jpg' % image_guid

        else:
            the_file_path = 'full/%s.jpg' % image_guid

        return the_file_path

    def get_media_requests(self, item, info):
        if 'image_urls' in item:

            for image_url in item['image_urls']:
                the_request = scrapy.Request(image_url)
                if 'artist_object' in item:
                    the_request.meta['item'] = item

                elif 'album_object' in item:
                    the_request.meta['item'] = item

                yield the_request

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            print item['image_urls']
            raise DropItem("Item contains no images")

        else:
            if 'album_object' in item:
                album_object = item['album_object']
                album_object.album_image = image_paths[0]
                album_object.save()

            elif 'artist_object' in item:
                artist_object = item['artist_object']
                image_type = item['image_type']
                downloaded_images = []
                print image_paths
                print artist_object.id

                for image_dict in item['image_dicts']:
                    the_image_path = "artists/" + item['image_type'] + \
                                     "/" + hashlib.sha1(image_dict['url']).hexdigest() + \
                                     ".jpg"
                    print the_image_path

                    if the_image_path in image_paths:
                        image_dict['path'] = the_image_path
                        image_dict['image_type'] = item['image_type']
                        downloaded_images.append(image_dict)

                artist_object.artist_images = downloaded_images
                artist_object.save()



            item['image_paths'] = image_paths

        return item

