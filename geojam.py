import streamlit as st
import requests
import pandas as pd
from geopy.distance import distance


# Initialize session state variables
if "step" not in st.session_state:
    st.session_state.step = 1  # Start at step 1
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "results" not in st.session_state:
    st.session_state.results = None
if "search_params" not in st.session_state:
    st.session_state.search_params = {}

# Step 1: API Key Selection
if st.session_state.step == 1:
    st.title("GeoJam Contextualization Tool")
    st.subheader("Step 1: API Key Selection")
    api_choice = st.radio(
        "Choose your API key option:",
        ("Use GeoJam's API Key", "Use my own API Key"),
    )

    if api_choice == "Use GeoJam's API Key":
        password = st.text_input("Enter GeoJam password:", type="password")
        if st.button("Validate API Key"):
            if password == "GEOJAM":
                st.session_state.api_key = "AIzaSyBZ1oNBc74mCBB3Mc161f4CVHWorxV5iaA"
                st.success("Using GeoJam's API key.")
                st.session_state.step = 2
            else:
                st.error("Incorrect password.")
    else:
        custom_key = st.text_input("Enter your Google API Key:")
        if st.button("Validate API Key"):
            if custom_key.strip():
                st.session_state.api_key = custom_key
                st.success("Using your custom API key.")
                st.session_state.step = 2
            else:
                st.error("API Key cannot be empty.")

# Step 2: Input Search Parameters
if st.session_state.step == 2:
    st.title("GeoJam Contextualization Tool")
    st.subheader("Step 2: Input Search Parameters")
    query = st.text_input("Enter search query (e.g., restaurants, cafes):")
    location_str = st.text_input(
        "Enter location (latitude,longitude):", placeholder="40.7128,-74.0060"
    )
    radius = st.number_input(
        "Enter radius (in meters):", min_value=1, max_value=50000, value=1000
    )

    if st.button("Search"):
        try:
            location = tuple(map(float, location_str.split(",")))
            st.session_state.search_params = {
                "query": query,
                "location": location,
                "radius": radius,
            }
            st.session_state.step = 3
        except ValueError:
            st.error("Invalid location format. Please enter as latitude,longitude.")

# Step 3: Show Results and Provide Actions
if st.session_state.step == 3:
    st.title("GeoJam Contextualization Tool")
    st.subheader("Step 3: Search Results")
    params = st.session_state.search_params
    query = params["query"]
    location = params["location"]
    radius = params["radius"]
    api_key = st.session_state.api_key

    # Call Google Maps API
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    api_params = {
        "query": query,
        "location": f"{location[0]},{location[1]}",
        "radius": radius,
        "key": api_key,
    }
    response = requests.get(endpoint, params=api_params)
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

    st.session_state.results = results

    # Display Results
    if results:
        st.write(f"Found {len(results)} results within {radius} meters:")
        st.table(results)
    else:
        st.warning("No results found within the specified radius.")

    # Actions
    st.subheader("What would you like to do next?")
    action = st.radio(
        "Choose an option:",
        ("New Search", "Save Results as CSV", "Quit"),
    )

    if action == "New Search":
        st.session_state.step = 1  # Restart at Step 1
        st.session_state.results = None
        st.session_state.search_params = {}

    elif action == "Save Results as CSV":
        filename = st.text_input("Enter a filename for the CSV (without extension):", "results")
        if st.button("Download CSV"):
            # Convert results to a DataFrame
            results_df = pd.DataFrame(st.session_state.results)

            # Convert DataFrame to CSV as bytes
            csv = results_df.to_csv(index=False).encode('utf-8')

            # Provide the file for download
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{filename}.csv",
                mime="text/csv",
            )

    elif action == "Quit":
        st.info("Thank you for using GeoJam! The app has stopped.")
        st.stop()