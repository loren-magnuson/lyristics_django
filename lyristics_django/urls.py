"""lyristics_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from lyristics_frontend import views
from django.conf.urls.static import static
from lyristics_django import settings
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.FrontPageview.as_view(), name='front_page_view'),
    url(r'^autocomplete/', views.autocomplete_view, name='autocomplete_view'),
    url(r'^search/', views.artist_search_view, name='artist_search_view'),
    url(r'^artist', views.artist_details_view, name='artist_details_view'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
