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

# Sidebar: Inputs and Logo
st.sidebar.image("assets/geojamlogo.png", use_column_width=True)  # Left panel logo

st.sidebar.subheader("Enter Search Parameters")

# Helper function for "i" icons with hover text
def info_icon(text):
    st.sidebar.markdown(f"""
    <span style="font-size: 0.9em; color: grey; cursor: help;" title="{text}">ℹ️</span>
    """, unsafe_allow_html=True)

# API Key Selection
st.sidebar.markdown("**Choose your API key option:**")
api_choice = st.sidebar.radio(
    "",
    ("Use GeoJam API Key (US$ 1.00 per Query)", "Use my own API Key (Free)")
)
info_icon("Select whether to use GeoJam's API key (requires password) or your own API key.")

if api_choice == "Use GeoJam API Key (US$ 1.00 per Query)":
    # Password-protect GeoJam API Key
    password = st.sidebar.text_input("Enter GeoJam password:", type="password")
    info_icon("Enter the password provided to use GeoJam's API key.")
    try:
        valid_password = st.secrets["google"]["password"]
        if password == valid_password:
            api_key = st.secrets["google"]["api_key"]
            st.sidebar.success("Password accepted. Using GeoJam's API key.")
        else:
            st.sidebar.error("Invalid password. Please try again.")
            st.stop()
    except KeyError:
        st.sidebar.error("GeoJam API key or password is not configured. Contact the administrator.")
        st.stop()
elif api_choice == "Use my own API Key (Free)":
    # Prompt user for their own API key
    api_key = st.sidebar.text_input("Enter your Google API Key:")
    info_icon("Provide your own Google API key to proceed.")
    if not api_key.strip():
        st.sidebar.warning("Please enter a valid API key to proceed.")
        st.stop()
else:
    st.sidebar.warning("Please select an API key option to proceed.")
    st.stop()

# Query Input
query = st.sidebar.text_input("Enter search query (e.g., restaurants, cafes):")
info_icon("Type the keyword for the search, like 'restaurants' or 'cafes'.")

# Location Input
location_str = st.sidebar.text_input(
    "Enter location (latitude,longitude):", placeholder="40.7128,-74.0060"
)
info_icon("Provide the location as latitude,longitude (e.g., 40.7128,-74.0060).")

# Radius Slider
radius = st.sidebar.slider(
    "Select radius (in meters):", min_value=1, max_value=50000, value=1000, step=100
)
info_icon("Choose the radius for the search area, up to 50 kilometers.")

# Run Search Button
if st.sidebar.button("Run Search"):
    run_query = True
else:
    run_query = False

# Main Panel: Map and Results
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
                        "Place ID": result["place_id"],
                        "Name": name,
                        "Type": ", ".join(result.get("types", [])),
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