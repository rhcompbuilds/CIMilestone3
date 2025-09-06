from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def opening_hour(request):
    return HttpResponse("Welcome to the Swimming Pool Opening Hours page!")