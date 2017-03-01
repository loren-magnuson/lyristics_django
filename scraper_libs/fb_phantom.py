import sys, os, django
import scrapy_fake_useragent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
sys.path.append('/home/magno/PycharmProjects/lyristics_django')
os.environ['DJANGO_SETTINGS_MODULE'] = 'lyristics_django.settings'
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from lyristics_frontend.models import Artist
from selenium.webdriver.support import expected_conditions as EC
import hashlib
from urllib import urlretrieve
image_store = os.getcwd() + "/static/images/artists/facebook"
usr = "itsmebusychild@mail.com"
pwd = "itsmemagno"
driver = webdriver.PhantomJS(executable_path=os.getcwd() + "/scraper_libs/phantomjs")
driver.get("https://www.facebook.com")
assert "Facebook" in driver.title

elem = driver.find_element_by_id("email")
elem.send_keys(usr)
elem = driver.find_element_by_id("pass")
elem.send_keys(pwd)
elem.send_keys(Keys.RETURN)

artists = Artist.objects.all()
for artist in artists:

    if 'Facebook' in artist.artist_images:
        pass

    else:
        artist_url = None

        if 'Facebook Profile' in artist.related_links:

            artist_url = artist.related_links['Facebook Profile']
            page = driver.get(artist_url)
            profile_image_url = None

            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img._4jhq")))

            except:
                print "couldnt find profile pic"

            else:
                img_src = element.get_attribute('src')
                print(img_src)
                hash_object = hashlib.sha1(driver.current_url)
                hex_dig = hash_object.hexdigest()
                artist.artist_images['Facebook'] = hex_dig + ".png"
                artist.save()
                print hex_dig
                urlretrieve(img_src, image_store + hex_dig + ".png")

            time.sleep(2)
