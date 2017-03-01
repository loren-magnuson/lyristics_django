# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.core import serializers
import json
from urllib import urlencode
from copy import deepcopy
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render
from django.views.generic.base import TemplateView
from lyristics_frontend.models import Artist, Album
from django.core import serializers
client = settings.ES_CLIENT


def artist_search_view(request):
    query = request.GET.get('term', '')
    es_query = {
               'query': {
                   'match': {
                        'artist_name': query
                      }
                   }
               }

    resp = client.search(index='lyristics', doc_type='artist', body=es_query)
    print resp
    artist_ids = [ i['_id'] for i in resp['hits']['hits'] ]
    artists = []
    for i in artist_ids:
        artist = Artist.objects.get(id=i)
        artists.append(artist)
    
    data = json.dumps({'mongo_items': serializers.serialize("json", artists),
                       'count': len(artists),
                           'query': query})
  #                     'es_results': resp})    



 #   data = json.dumps(resp)
    
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)  


def autocomplete_view(request):
    query = request.GET.get('term', '')
    print query

    resp = client.suggest(
        index='lyristics',
        # body={
        #     'name_complete': {
        #         "text": query,
        #         "completion": {
        #             "field": 'name_complete',
        #         }
        #     }
        # }
        body={
            'name_complete': {
                "text": query,
                "completion": {
                    "field": 'name_complete',
                }
            }
        }
    )
    print resp
    options = resp['name_complete'][0]['options']
    data = json.dumps(
        [{'id': i['_id'], 'value': i['text']} for i in options]
    )
    print data
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def artist_details_view(request):
    artist_id = request.GET.get('artist_id')
    artist = Artist.objects.get(id=artist_id)
    context = {'artist': artist, 'albums': [ album for album in Album.objects.filter(artist_object=artist.id) ]}
    return render(request, 'lyristics_frontend/artist_details.html', context)


class FrontPageview(TemplateView):
    template_name = "lyristics_frontend/index.html"

    def get_context_data(self, **kwargs):
        body = {

        }
        es_query = self.gen_es_query(self.request)
        body.update({'query': es_query})
        search_result = client.search(index='lyristics', doc_type='artist', body=body)

        print search_result
        context = super(FrontPageview, self).get_context_data(**kwargs)
        context['hits'] = [
            self.convert_hit_to_template(c) for c in search_result['hits']['hits']
            ]

        return context

    def convert_hit_to_template(self, hit1):
        hit = deepcopy(hit1)
        almost_ready = hit['_source']
        almost_ready['artist_id'] = hit['_id']
        return almost_ready

    def facet_url_args(self, url_args, field_name, field_value):
        is_active = False
        if url_args.get(field_name):
            base_list = url_args[field_name].split(',')
            if field_value in base_list:
                del base_list[base_list.index(field_value)]
                is_active = True
            else:
                base_list.append(field_value)
            url_args[field_name] = ','.join(base_list)
        else:
            url_args[field_name] = field_value
        return url_args, is_active

    def prepare_facet_data(self, aggregations_dict, get_args):
        resp = {}
        for area in aggregations_dict.keys():
            resp[area] = []
            if area == 'age':
                resp[area] = aggregations_dict[area]['buckets']
                continue
            for item in aggregations_dict[area]['buckets']:
                url_args, is_active = self.facet_url_args(
                    url_args=deepcopy(get_args.dict()),
                    field_name=area,
                    field_value=item['key']
                )
                resp[area].append({
                    'url_args': urlencode(url_args),
                    'name': item['key'],
                    'count': item['doc_count'],
                    'is_active': is_active
                })
        return resp

    def gen_es_query(self, request):
        req_dict = deepcopy(request.GET.dict())
        if not req_dict:
            return {'match_all': {}}

        else:
            print req_dict
        filters = []

        # if 'term' in req_dict.keys() and len(req_dict) == 1:
        #     return {
        #
        #     }
        if 'term' in req_dict.keys():
            return { 'query': {
                    "term": {"artist_name": req_dict['term']}
                }
            }
        # for field_name in req_dict.keys():
        #     if '__' in field_name:
        #         filter_field_name = field_name.replace('__', '.')
        #     else:
        #         filter_field_name = field_name
        #     for field_value in req_dict[field_name].split(','):
        #         if not field_value:
        #             continue
        #         filters.append(
        #             {
        #                 'term': {filter_field_name: field_value},
        #             }
        #         )
        # return {
        #     'filtered': {
        #         'query': {'match_all': {}},
        #         'filter': {
        #             'bool': {
        #                 'must': filters
        #             }
        #         }
        #     }
        # }
