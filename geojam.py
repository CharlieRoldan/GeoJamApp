import streamlit as st
import requests
import csv
from geopy.distance import distance

# Streamlit Title
st.title("GeoJam Contextualization Tool")
st.write("Search for places using the Google Places API and visualize results!")

# API Key Selection
st.subheader("API Key Selection")
api_choice = st.radio(
    "Choose your API key option:",
    ("Use GeoJam's API Key", "Use my own API Key"),
)

if api_choice == "Use GeoJam's API Key":
    password = st.text_input("Enter GeoJam password:", type="password")
    if password == "GEOJAM":
        api_key = "AIzaSyBZ1oNBc74mCBB3Mc161f4CVHWorxV5iaA"
        st.success("Using GeoJam's API key.")
    else:
        st.error("Incorrect password.")
        st.stop()
else:
    api_key = st.text_input("Enter your Google API Key:")
    if not api_key:
        st.warning("Please enter your API key.")
        st.stop()

# Input Fields for Query and Location
st.subheader("Search Parameters")
query = st.text_input("Enter search query (e.g., restaurants, cafes):")
location_str = st.text_input(
    "Enter location (latitude,longitude):", placeholder="40.7128,-74.0060"
)
radius = st.number_input(
    "Enter radius (in meters):", min_value=1, max_value=50000, value=1000
)

# Validate Location Input
try:
    location = tuple(map(float, location_str.split(",")))
except ValueError:
    st.error("Invalid location format. Please enter as latitude,longitude.")
    st.stop()

# Search Button
if st.button("Search"):
    # Set up API endpoint and parameters
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": f"{location[0]},{location[1]}",
        "radius": radius,
        "key": api_key,
    }

    # Make API request
    response = requests.get(endpoint, params=params)
    data = response.json()

    # Handle API Errors
    if "error_message" in data:
        st.error(f"API Error: {data['error_message']}")
        st.stop()

    # Process Results
    st.subheader("Results")
    results = []
    for result in data.get("results", []):
        name = result["name"]
        address = result.get("formatted_address", "N/A")
        latitude = result["geometry"]["location"]["lat"]
        longitude = result["geometry"]["location"]["lng"]
        rating = result.get("rating", "N/A")
        place_loc = (latitude, longitude)
        dist_m = distance(location, place_loc).meters

        # Filter results within the specified radius
        if dist_m <= radius:
            results.append(
                {
                    "Name": name,
                    "Address": address,
                    "Latitude": latitude,
                    "Longitude": longitude,
                    "Rating": rating,
                    "Distance (m)": int(dist_m),
                }
            )

    # Display results in a table
    if results:
        st.write(f"Found {len(results)} results within {radius} meters:")
        st.table(results)

        # Options: New Search, Save, or Quit
        action = st.radio("What would you like to do next?", ("New Search", "Save to CSV", "Quit"))

        if action == "New Search":
            st.experimental_rerun()  # Restarts the app

        elif action == "Save to CSV":
            filename = st.text_input("Enter a filename for the CSV (without extension):", "results")
            if st.button("Save"):
                with open(f"{filename}.csv", "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
                st.success(f"Results saved to {filename}.csv!")

        elif action == "Quit":
            st.stop()
    else:
        st.warning("No results found within the specified radius.")