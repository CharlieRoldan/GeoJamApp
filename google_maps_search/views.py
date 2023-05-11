import csv
from io import StringIO
from django.http import HttpResponse
from django.shortcuts import render
from .forms import GoogleMapsSearchForm
from .models import SearchResult
from .googlemapsX import search_places, generate_csv

def search(request):
    results = []
    if request.method == 'POST':
        form = GoogleMapsSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            lat = form.cleaned_data['lat']
            lng = form.cleaned_data['lng']
            radius = form.cleaned_data['radius']
            location = (lat, lng)
            results = search_places(query, location, radius)
            SearchResult.objects.bulk_create(results)
    else:
        form = GoogleMapsSearchForm()
    return render(request, 'search.html', {'form': form, 'results': results})



def download_csv(request):
    print('download_csv() function called.')
    query = request.GET.get('query')
    location = (float(request.GET.get('latitude')), float(request.GET.get('longitude')))
    radius = int(request.GET.get('radius'))
    results = search_places(query=query, location=location, radius=radius)

    # Convert results to a CSV string using the generate_csv function
    csv_str = generate_csv(results)

    # Create a response object with the CSV string as the content
    response = HttpResponse(csv_str, content_type='text/csv')

    # Set the content-disposition header to trigger a download
    response['Content-Disposition'] = f'attachment; filename=search_results.csv'

    return response

