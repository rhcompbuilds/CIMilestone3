from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import OpenTime
from django.urls import reverse

# Create your views here.
def open_times_list(request):
    # Fetch all open times from the database
    open_times = OpenTime.objects.all().order_by('day')
    return render(request, 'open_times/open_times_list.html', {'open_times': open_times})

def add_open_time(request):
    if request.method == 'POST':
        day = request.POST.get('day')
        open_time = request.POST.get('open_time')
        close_time = request.POST.get('close_time')

        if day and open_time and close_time:
            OpenTime.objects.create(day=day, open_time=open_time, close_time=close_time)
            messages.success(request, 'Open time added successfully.')
            return redirect(reverse('open_times_list'))
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'open_times/add_open_time.html')

def edit_open_time(request, pk):
    open_time = get_object_or_404(OpenTime, pk=pk)

    if request.method == 'POST':
        day = request.POST.get('day')
        open_time_value = request.POST.get('open_time')
        close_time_value = request.POST.get('close_time')

        if day and open_time_value and close_time_value:
            open_time.day = day
            open_time.open_time = open_time_value
            open_time.close_time = close_time_value
            open_time.save()
            messages.success(request, 'Open time updated successfully.')
            return redirect(reverse('open_times_list'))
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'open_times/edit_open_time.html', {'open_time': open_time})

def delete_open_time(request, pk):
    open_time = get_object_or_404(OpenTime, pk=pk)

    if request.method == 'POST':
        open_time.delete()
        messages.success(request, 'Open time deleted successfully.')
        return redirect(reverse('open_times_list'))

    return render(request, 'open_times/delete_open_time.html', {'open_time': open_time})
