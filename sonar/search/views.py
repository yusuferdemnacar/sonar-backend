import math
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from .models import *
from .s2agmodels import *
import requests
import json
from django.template import loader

class HomePageView(TemplateView):
    template_name = 'index.html'

def SearchResultsView(request):
    template_name = 'index.html'
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
        article = S2AGSearchDisplayArticle(title=element['title'], s2ag_paperID=element['paperId'], abstract = element['abstract'])
        queryset.append(article)
    page_number = math.ceil(int(response.json()['total'])/25)
    context = {
        'object_list': queryset,
        'page_number' : page_number,
        'query':query,
        'offset':offset,
    }
    return HttpResponse(template.render(context, request))

def add_catalog(request):
    print(f'{request.POST["paperId"]} Added to Catalog')
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def createCatalogBase(request):

    user = User.objects.get(id=1)
    
    catalog_name = request.POST['catalog_name']

    catalog_base = CatalogBase(catalog_name=catalog_name, owner=user)
    
    try:
        catalog_base.save()
        return JsonResponse({"info": "Catalog created successfully", "id": catalog_base.id}, status=200)
    except:
        return JsonResponse({"info": "Catalog creation failed"}, status=400)