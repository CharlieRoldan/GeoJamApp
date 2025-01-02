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

    # Display Results
    st.subheader("Results")
    if "results" in data and len(data["results"]) > 0:
        results = []
        for result in data["results"]:
            name = result["name"]
            address = result.get("formatted_address", "N/A")
            latitude = result["geometry"]["location"]["lat"]
            longitude = result["geometry"]["location"]["lng"]
            rating = result.get("rating", "N/A")
            place_loc = (latitude, longitude)
            dist_m = distance(location, place_loc).meters

            # Add result to list
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
        st.table(results)

        # Save to CSV Button
        if st.button("Save Results to CSV"):
            with open("results.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            st.success("Results saved to results.csv!")
    else:
        st.warning("No results found for your query.")