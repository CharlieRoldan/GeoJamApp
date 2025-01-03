import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import distance
from st_aggrid import AgGrid, GridOptionsBuilder

# Set Streamlit page layout to wide
st.set_page_config(layout="wide")

# Initialize session state variables
if "results" not in st.session_state:
    st.session_state.results = None

# Sidebar: Inputs and Main Logo
st.sidebar.image("assets/GeoJamLogo.png", use_container_width=True)  # Main logo
st.sidebar.subheader("Enter Search Parameters")

# API Key Selection
api_choice = st.sidebar.radio(
    "Choose your API key option:",
    ("Use GeoJam's API Key", "Use my own API Key"),
)

if api_choice == "Use GeoJam's API Key":
    api_key = st.secrets["google"]["api_key"]
    st.sidebar.success("Using GeoJam's API key.")
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

# Main Panel Layout

# Display small logo
st.markdown(
    """
    <div style="text-align: right;">
        <img src="assets/geojamloguito.png" alt="Small Logo" style="max-width: 100%; height: auto; margin-bottom: 10px;">
    </div>
    """,
    unsafe_allow_html=True,
)
if location_str.strip():
    try:
        location = tuple(map(float, location_str.split(",")))

        # Display map
        m = folium.Map(location=location, zoom_start=12)

        folium.Circle(
            location=location,
            radius=radius,
            color="blue",
            fill=True,
            fill_opacity=0.2,
        ).add_to(m)

        folium.Marker(location=location, popup="Center Point").add_to(m)

        st_folium(m, width=1660, height=500)

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

if run_query and location_str.strip() and query:
    try:
        location = tuple(map(float, location_str.split(",")))

        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "location": f"{location[0]},{location[1]}",
            "radius": radius,
            "key": api_key,
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        if "error_message" in data:
            st.error(f"API Error: {data['error_message']}")
            st.stop()

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

        st.session_state.results = results

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

if st.session_state.results:
    st.subheader("Query Details")
    st.write("**Search Query**:", query)
    st.write("**Location**:", location)
    st.write("**Radius**:", f"{radius} meters")

    st.subheader("Search Results")
    results = st.session_state.results
    if results:
        st.write(f"Found {len(results)} results:")

        # Use AgGrid for interactive table
        results_df = pd.DataFrame(results)
        gb = GridOptionsBuilder.from_dataframe(results_df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_default_column(resizable=True, filterable=True, sortable=True)
        grid_options = gb.build()

        AgGrid(
            results_df,
            gridOptions=grid_options,
            height=300,
            theme="streamlit",  # Other options: "light", "dark", "blue", etc.
            enable_enterprise_modules=False,
        )

        # Save Results
        filename = st.text_input("Enter a filename for the CSV (without extension):", "results")
        if st.button("Save as CSV"):
            if filename.strip():
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