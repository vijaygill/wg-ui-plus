from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
#from .models import Member

def index(request):
    template = loader.get_template('index.html')
    context = {}
    return HttpResponse(template.render(context, request))