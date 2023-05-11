import requests
import csv
from geopy.distance import distance
from google_maps_search.models import SearchResult
import csv
import io
from io import StringIO



def search_places(api_key, query, location, radius):
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    location_str = f"{location[0]},{location[1]}"

    params = {
        "query": query,
        "location": location_str,
        "radius": radius,
        "key": "AIzaSyC0KLATkK9lTyDwyAZjA16NPzg320P_hIQ"
    }
    

    response = requests.get(endpoint, params=params)
    data = response.json()

    results = []
    for result in data["results"]:
        name = result["name"]
        address = result.get("formatted_address", "")
        latitude = result['geometry']['location']['lat']
        longitude = result['geometry']['location']['lng']
        place_loc = (latitude, longitude)
        dist_m = distance(location, place_loc).meters

        if dist_m <= radius:
            search_result = SearchResult(name=name, address=address, latitude=latitude, longitude=longitude)
            results.append(search_result)

    return results


def generate_csv(results):
    """
    Given a list of SearchResult objects, generate a CSV file and return its contents as a string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Address', 'Latitude', 'Longitude', 'Rating'])
    for result in results:
        writer.writerow([result.name, result.address, result.latitude, result.longitude, result.rating])
    return output.getvalue()


