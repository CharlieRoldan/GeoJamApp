import streamlit as st
import requests
import pandas as pd
from geopy.distance import distance


# Initialize session state variables
if "results" not in st.session_state:
    st.session_state.results = None


# Input Screen
st.title("GeoJam Contextualization Tool")
st.subheader("Enter Details Below")

# API Key
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
    if not api_key.strip():
        st.warning("Please enter your API key.")
        st.stop()

# Query and Location Inputs
query = st.text_input("Enter search query (e.g., restaurants, cafes):")
location_str = st.text_input(
    "Enter location (latitude,longitude):", placeholder="40.7128,-74.0060"
)
radius = st.number_input(
    "Enter radius (in meters):", min_value=1, max_value=50000, value=1000
)

# Execute Search
if st.button("Run Search"):
    try:
        # Validate location
        location = tuple(map(float, location_str.split(",")))

        # Call Google Maps API
        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "location": f"{location[0]},{location[1]}",
            "radius": radius,
            "key": api_key,
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        # Handle API Errors
        if "error_message" in data:
            st.error(f"API Error: {data['error_message']}")
            st.stop()

        # Process Results
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

        # Save results to session state
        st.session_state.results = results

        # Display Results
        if results:
            st.write(f"Found {len(results)} results:")
            st.table(results)

        else:
            st.warning("No results found within the specified radius.")

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

# Results Screen
if st.session_state.results:
    st.subheader("What would you like to do next?")
    if st.button("Go Back to Home Screen"):
        st.session_state.results = None  # Clear results to restart
    if st.button("Save as CSV"):
        results_df = pd.DataFrame(st.session_state.results)
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="results.csv",
            mime="text/csv",
        )