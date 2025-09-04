from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def opening_times(request):
    return HttpResponse("This is the opening times and days view")
    