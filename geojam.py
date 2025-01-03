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

# Sidebar Inputs with Info Icons
st.sidebar.subheader("Enter Search Parameters")

# Add info icon with hover tooltip for each field
def input_with_tooltip(label, tooltip_text, key=None, **kwargs):
    st.sidebar.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="margin-right: 8px;">{label}</span>
            <span style="width: 16px; height: 16px; display: inline-block; border-radius: 50%; background-color: #e0e0e0; color: #666; font-size: 12px; font-weight: bold; text-align: center; line-height: 16px; cursor: pointer;" 
                title="{tooltip_text}">i</span>
        </div>
        """, unsafe_allow_html=True
    )
    return st.sidebar.text_input("", key=key, **kwargs)

# API Key Selection
st.sidebar.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 5px;">
    <span>Choose your API key option:</span>
    <span style="width: 16px; height: 16px; display: inline-block; border-radius: 50%; background-color: #e0e0e0; color: #666; font-size: 12px; font-weight: bold; text-align: center; line-height: 16px; cursor: pointer;" 
        title="Select whether to use the GeoJam API (with a password) or your own API key for queries.">i</span>
</div>
""", unsafe_allow_html=True)
api_choice = st.sidebar.radio(
    "",
    ("Use GeoJam's API Key", "Use my own API Key"),
)

if api_choice == "Use GeoJam's API Key":
    password = st.sidebar.text_input("Enter GeoJam password:", type="password")
    try:
        valid_password = st.secrets["google"]["password"]  # Retrieve password from secrets
        if password == valid_password:
            api_key = st.secrets["google"]["api_key"]  # Retrieve API key
            st.sidebar.success("Password accepted. Using GeoJam's API key.")
        else:
            st.sidebar.error("Invalid password. Please try again.")
            st.stop()
    except KeyError:
        st.sidebar.error("GeoJam API key or password is not configured. Contact the administrator.")
        st.stop()
elif api_choice == "Use my own API Key":
    api_key = st.sidebar.text_input("Enter your Google API Key:")
    if not api_key.strip():
        st.sidebar.warning("Please enter a valid API key to proceed.")
        st.stop()
else:
    st.sidebar.warning("Please select an API key option to proceed.")
    st.stop()

# Query Input with Tooltip
input_with_tooltip(
    label="Enter search query (e.g., restaurants, cafes):",
    tooltip_text="Specify the type of business or location you want to search for.",
    key="query",
)

# Location Input with Tooltip
input_with_tooltip(
    label="Enter location (latitude,longitude):",
    tooltip_text="Provide the coordinates for the center of your search area. Format: latitude,longitude.",
    key="location_str",
    placeholder="40.7128,-74.0060"
)

# Radius Slider with Tooltip
st.sidebar.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 5px;">
    <span>Select radius (in meters):</span>
    <span style="width: 16px; height: 16px; display: inline-block; border-radius: 50%; background-color: #e0e0e0; color: #666; font-size: 12px; font-weight: bold; text-align: center; line-height: 16px; cursor: pointer;" 
        title="Define the search area radius in meters (max 50 km).">i</span>
</div>
""", unsafe_allow_html=True)
radius = st.sidebar.slider(
    "",
    min_value=1,
    max_value=50000,
    value=1000,
    step=100
)

# Run Search Button
run_query = st.sidebar.button("Run Search")

# Main Panel: Map and Results
if st.session_state.get("location_str"):
    try:
        location = tuple(map(float, st.session_state["location_str"].split(",")))

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

if run_query and st.session_state.get("location_str") and st.session_state.get("query"):
    try:
        location = tuple(map(float, st.session_state["location_str"].split(",")))

        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": st.session_state["query"],
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

# Results Table
if st.session_state.results:
    st.subheader("Query Details")
    st.write("**Search Query**:", st.session_state["query"])
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