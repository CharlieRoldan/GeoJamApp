import streamlit as st
import pandas as pd
import requests
from geopy.distance import distance
import streamlit.components.v1 as components


# Initialize session state variables
if "results" not in st.session_state:
    st.session_state.results = None


# Function to Embed Google Maps
def google_maps_embed(lat, lon, zoom=12, radius=None, api_key="YOUR_GOOGLE_API_KEY"):
    # Base URL for Google Maps Embed API
    map_url = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center={lat},{lon}&zoom={zoom}&maptype=roadmap"
    
    # Add radius circle if provided
    if radius:
        circle_script = f"""
        <script>
            function initMap() {{
                var center = {{ lat: {lat}, lng: {lon} }};
                var map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: {zoom},
                    center: center
                }});
                var circle = new google.maps.Circle({{
                    center: center,
                    radius: {radius},
                    map: map,
                    fillColor: '#blue',
                    fillOpacity: 0.2,
                    strokeColor: '#0000FF',
                    strokeOpacity: 0.7
                }});
                new google.maps.Marker({{
                    position: center,
                    map: map
                }});
            }}
        </script>
        """
        map_url += f"&script={circle_script}"

    # Embed the map
    iframe_html = f"""
    <iframe
        width="100%"
        height="500"
        frameborder="0"
        style="border:0"
        src="{map_url}"
        allowfullscreen>
    </iframe>
    """
    components.html(iframe_html, height=500)


# Sidebar: Inputs and Logo
st.sidebar.title("GeoJam App")
st.sidebar.write("Your Location-Based Search Tool")

# Add a placeholder for the logo (use your own logo file here)
st.sidebar.image("https://via.placeholder.com/150", use_container_width=True)  # Replace with your logo URL or file path

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

        # Display Google Maps
        st.subheader("Map Visualization")
        google_maps_embed(location[0], location[1], zoom=12, radius=radius, api_key=api_key)

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

# Results Processing
if run_query and location_str.strip() and query:
    try:
        # Parse Lat/Long
        location = tuple(map(float, location_str.split(",")))

        # Call Google Maps Places API
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