import requests
import csv
from geopy.distance import distance

# Print header
print("╔════════════════════════════════════════════════════╗")
print("║                GeoJam Contextualization            ║")
print("╚════════════════════════════════════════════════════╝")

# API Key Selection
print("\nDo you want to use GeoJam's API key or your own?")
print("1. Use GeoJam's API key (Password required)")
print("2. Use my own API key")

while True:
    api_choice = input("Enter your choice (1/2): ").strip()
    if api_choice == "1":
        password = input("Enter the GeoJam password: ").strip()
        if password == "GEOJAM":
            api_key = "AIzaSyBZ1oNBc74mCBB3Mc161f4CVHWorxV5iaA"
            print("\nPassword correct. Using GeoJam's API key.")
            break
        else:
            print("Incorrect password. Please try again.")
    elif api_choice == "2":
        api_key = input("Enter your Google Maps API key: ").strip()
        if api_key:  # Validate non-empty input
            print("\nUsing your custom API key.")
            break
        else:
            print("API key cannot be empty. Please try again.")
    else:
        print("Invalid choice. Please enter 1 or 2.")

# Single input for query, location, and radius
query = input("\nEnter search query / keywords: ")
location_str = input("Enter location to search LAT & LONG Center (comma separated): ")
location = tuple(map(float, location_str.split(',')))
radius = int(input("Provide me a radius from location center (in meters): "))

# Set up API endpoint and parameters
endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
params = {
    "query": query,
    "location": f"{location[0]},{location[1]}",
    "radius": radius,
    "key": api_key
}

# Make API request
response = requests.get(endpoint, params=params)
data = response.json()

# Debugging: Print raw API response if needed
if "error_message" in data:
    print("\nError with API request:", data["error_message"])
    exit()

# Extract location information from API response
max_address_len = 50
max_name_len = 30
print("\nResults:")
if "results" in data and len(data["results"]) > 0:
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
else:
    print("\nNo results found for your query.")

# Menu for user actions
while True:
    print("\nWhat would you like to do next?")
    print("1. Run another search")
    print("2. Save results to CSV")
    print("3. Quit")

    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == "1":
        print("\nRestarting the search...")
        # Relaunch script logic: You could wrap everything in a function for reuse.
        exec(open(__file__).read())  # Rerun the script (only works if the script is saved)
        break
    elif choice == "2":
        if "results" in data and len(data["results"]) > 0:
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
        else:
            print("\nNo results to save. Run a search first.")
    elif choice == "3":
        print("\nGoodbye!")
        exit()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")