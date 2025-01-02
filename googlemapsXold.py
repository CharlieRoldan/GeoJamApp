import requests
import csv
from geopy.distance import distance


# Print header
print("╔════════════════════════════════════════════════════╗")
print("║         Tulkas GeoJam Contextualization            ║")
print("╚════════════════════════════════════════════════════╝")

# Set up API endpoint and parameters
endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
query = input("Enter search query / keywords: ")
location_str = input("Enter location to search LAT & LONG Center (comma separated): ")
location = tuple(map(float, location_str.split(',')))
radius = int(input("Provide me a radius from location center (in meters): "))


params = {
    "query": query,
    "location": f"{location[0]},{location[1]}",
    "radius": radius,
    "key": "AIzaSyC0KLATkK9lTyDwyAZjA16NPzg320P_hIQ"
}


# Make API request
response = requests.get(endpoint, params=params)
data = response.json()

# Extract location information from API response
max_address_len = 50
max_name_len = 30
print("\nResults:")
print(f"{'Name':<{max_name_len}}{'Address':<{max_address_len}}{'Latitude':<15}{'Longitude':<15}{'Rating':<8}{'Distance (m)'}")
for result in data["results"]:
    name = result["name"][:max_name_len]
    address = result.get("formatted_address", "")[:max_address_len]
    latitude = f"{result['geometry']['location']['lat']:.7f}"
    longitude = f"{result['geometry']['location']['lng']:.7f}"
    rating = result.get("rating", "")
    place_loc = (result['geometry']['location']['lat'], result['geometry']['location']['lng'])
    dist_m = distance(location, place_loc).meters
    if dist_m <= radius:
        print(f"{name:<{max_name_len}}{address:<{max_address_len}}{latitude:<15}{longitude:<15}{rating:<8}{int(dist_m)}")


# Write results to CSV file
filename = input("\nEnter a filename to save the results: ")
with open(f"{filename}.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Address", "Latitude", "Longitude", "Rating", "Distance (m)"])
    for result in data["results"]:
        name = result["name"]
        address = result.get("formatted_address", "")
        latitude = f"{result['geometry']['location']['lat']:.7f}"
        longitude = f"{result['geometry']['location']['lng']:.7f}"
        rating = result.get("rating", "")
        place_loc = (result['geometry']['location']['lat'], result['geometry']['location']['lng'])
        dist_m = distance(location, place_loc).meters
        if dist_m <= radius:
            writer.writerow([name, address, latitude, longitude, rating, int(dist_m)])
        
print(f"\nResults saved to {filename}.csv")
