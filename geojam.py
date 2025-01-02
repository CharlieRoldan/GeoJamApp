import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import distance


# Initialize session state variables
if "results" not in st.session_state:
    st.session_state.results = None


# Sidebar: Inputs and Logo
st.sidebar.title("GeoJam App")
st.sidebar.write("Your Location-Based Search Tool")

# Add a placeholder for the logo (use your own logo file here)
st.sidebar.image("https://via.placeholder.com/150", use_container_width=True)  # Updated here

# Sidebar Inputs
st.sidebar.subheader("Enter Search Parameters")

# API Key Selection
api_choice = st.sidebar.radio(
    "Choose your API key option:",
    ("Use GeoJam's API Key", "Use my own API Key"),
)

if api_choice == "Use GeoJam's API Key":
    password = st.sidebar.text_input("Enter GeoJam password:", type="password")
    if password == "GEOJAM":
        api_key = "AIzaSyBZ1oNBc74mCBB3Mc161f4CVHWorxV5iaA"
        st.sidebar.success("Using GeoJam's API key.")
    else:
        st.sidebar.error("Incorrect password.")
        st.stop()
else:
    api_key = st.sidebar.text_input("Enter your Google API Key:")
    if not api_key.strip():
        st.sidebar.warning("Please enter your API key.")
        st.stop()

# Query Input
query = st.sidebar.text_input("Enter search query (e.g., restaurants, cafes):")

# Location Input
location_str = st.sidebar.text_input(
    "Enter location (latitude,longitude):", placeholder="40.7128,-74.0060"
)

# Radius Slider
radius = st.sidebar.slider(
    "Select radius (in meters):", min_value=1, max_value=50000, value=1000, step=100
)

# Run Search Button
run_query = st.sidebar.button("Run Search")

# Map Display
if location_str.strip():
    try:
        # Parse the Lat/Long
        location = tuple(map(float, location_str.split(",")))

        # Create Map with Folium
        m = folium.Map(location=location, zoom_start=12)

        # Add Circle to Map
        folium.Circle(
            location=location,
            radius=radius,
            color="blue",
            fill=True,
            fill_opacity=0.2,
        ).add_to(m)

        # Add Marker to Map
        folium.Marker(location=location, popup="Center Point").add_to(m)

        # Display Map
        st.subheader("Location Map")
        st_folium(m, width=700, height=500)

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

# Results Processing
if run_query and location_str.strip() and query:
    try:
        # Parse Lat/Long
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

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

# Results Display
if st.session_state.results:
    # Display Query Details
    st.subheader("Query Details")
    st.write("**Search Query**:", query)
    st.write("**Location**:", location)
    st.write("**Radius**:", f"{radius} meters")

    # Display Results Table
    st.subheader("Search Results")
    results = st.session_state.results
    if results:
        st.write(f"Found {len(results)} results:")
        st.table(results)

        # Save Results
        filename = st.text_input("Enter a filename for the CSV (without extension):", "results")
        if st.button("Save as CSV"):
            if filename.strip():
                results_df = pd.DataFrame(results)
                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{filename.strip()}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Please enter a valid filename.")
    else:
        st.warning("No results found within the specified radius.")