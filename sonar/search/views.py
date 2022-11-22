
import math
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.http import HttpResponse
from .models import Article
import requests
import json
from django.template import loader

class HomePageView(TemplateView):
    template_name = 'index.html'

def SearchResultsView(request):
    model = Article
    template_name = 'index.html'
    # make an http get request to https://api.semanticscholar.org/graph/v1/paper/search?query=mobile%20edge%20computing&limit=20&fields=title,year,fieldsOfStudy,s2FieldsOfStudy,authors
    template = loader.get_template(template_name=template_name)
    
    query = request.GET.get("q")
    offset = request.GET.get('offset')
    
    
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=25&offset={(int(offset)-1)*25}&fields=title,year,fieldsOfStudy,abstract'
    response = requests.get(url, )
    # take the data field from the response and print every element in the in it in a new line
    data = response.json()['data']
    # assign the element's fieldOfStudy to its 0th element
    for element in data:
        element['fieldsOfStudy'] = element['fieldsOfStudy'][0] if element['fieldsOfStudy'] else None
    queryset = []
    for element in data:
        article = Article(title=element['title'], DOI='', paperId=element['paperId'], abstract = element['abstract'])
        queryset.append(article)
    page_number = math.ceil(int(response.json()['total'])/25)
    context = {
        'object_list': queryset,
        'page_number' : page_number,
        'query':query,
        'offset':offset,
    }
    return HttpResponse(template.render(context, request))
        