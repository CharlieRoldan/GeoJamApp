import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import distance
from st_aggrid import AgGrid, GridOptionsBuilder
import simplekml  # For KML creation

# Set Streamlit page layout to wide
st.set_page_config(layout="wide")

# Initialize session state variables
if "results" not in st.session_state:
    st.session_state.results = None

# Sidebar Inputs
st.sidebar.image("assets/geojamlogo.png", use_container_width=True)
st.sidebar.subheader("Enter Search Parameters")

# API Key Selection
api_choice = st.sidebar.radio(
    "Choose your API key option:",
    ("Use GeoJam's API Key", "Use my own API Key"),
)

if api_choice == "Use GeoJam's API Key":
    # Password-protect GeoJam API Key
    password = st.sidebar.text_input("Enter GeoJam password:", type="password")
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
elif api_choice == "Use my own API Key":
    api_key = st.sidebar.text_input("Enter your Google API Key:")
    if not api_key.strip():
        st.sidebar.warning("Please enter a valid API key to proceed.")
        st.stop()

# Query Input
query = st.sidebar.text_input("Enter search query (e.g., restaurants, cafes):")
location_str = st.sidebar.text_input("Enter location (latitude,longitude):", placeholder="40.7128,-74.0060")
radius = st.sidebar.slider("Select radius (in meters):", min_value=1, max_value=50000, value=1000, step=100)
run_query = st.sidebar.button("Run Search")

# Display Map
if location_str.strip():
    try:
        location = tuple(map(float, location_str.split(",")))
        m = folium.Map(location=location, zoom_start=12)
        folium.Circle(location=location, radius=radius, color="blue", fill=True, fill_opacity=0.2).add_to(m)
        folium.Marker(location=location, popup="Center Point").add_to(m)
        st_folium(m, width=1660, height=500)
    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

# Fetch Data
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

        # Process Results
        results = []
        for result in data.get("results", []):
            place_id = result["place_id"]
            details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "key": api_key,
            }
            details_response = requests.get(details_endpoint, params=details_params)
            details_data = details_response.json()

            if details_data.get("result"):
                details = details_data["result"]
                results.append({
                    "Name": result["name"],
                    "Latitude": result["geometry"]["location"]["lat"],
                    "Longitude": result["geometry"]["location"]["lng"],
                    "Distance (m)": int(distance(location, (result["geometry"]["location"]["lat"], result["geometry"]["location"]["lng"])).meters),
                    "Vicinity": result.get("vicinity", "N/A"),
                    "Formatted Address": details.get("formatted_address", "N/A"),
                    "Status NOW": details.get("business_status", "N/A"),
                    "Rating": result.get("rating", "N/A"),
                    "User Ratings Total": result.get("user_ratings_total", "N/A"),
                    "Price Level": details.get("price_level", "N/A"),
                    "Website": details.get("website", "N/A"),
                    "Google URL": details.get("url", "N/A"),
                    "Phone": details.get("international_phone_number", "N/A"),
                    "Hours": ", ".join(details.get("opening_hours", {}).get("weekday_text", [])),
                    "Wheelchair Accessible": details.get("wheelchair_accessible_entrance", "N/A"),
                    "Plus Code": details.get("plus_code", {}).get("compound_code", "N/A"),
                    "Place ID": place_id,
                    "Types": ", ".join(details.get("types", [])),
                })

        st.session_state.results = results

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")

# Save as KML Function
def save_as_kml(data, filename):
    kml = simplekml.Kml()
    for index, row in data.iterrows():
        kml.newpoint(
            name=row["Name"],
            coords=[(row["Longitude"], row["Latitude"])],
            description=f"""
                <b>Address:</b> {row["Formatted Address"]}<br>
                <b>Vicinity:</b> {row["Vicinity"]}<br>
                <b>Rating:</b> {row["Rating"]} ({row["User Ratings Total"]} reviews)<br>
                <b>Status:</b> {row["Status NOW"]}<br>
                <b>Website:</b> {row["Website"]}<br>
                <b>Phone:</b> {row["Phone"]}<br>
            """
        )
    kml.save(f"{filename}.kml")

# Display Results
if st.session_state.results:
    st.subheader("Search Results")
    results_df = pd.DataFrame(st.session_state.results)

    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(results_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(resizable=True, filterable=True, sortable=True)
    grid_options = gb.build()

    AgGrid(
        results_df,
        gridOptions=grid_options,
        height=300,
        theme="streamlit",
        enable_enterprise_modules=False,
    )

    # Save Results
    filename = st.text_input("Enter a filename for the export (without extension):", "results")
    if st.button("Save as CSV"):
        if filename.strip():
            csv = results_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{filename.strip()}.csv",
                mime="text/csv",
            )
        else:
            st.warning("Please enter a valid filename.")

    if st.button("Save as KML"):
        if filename.strip():
            save_as_kml(results_df, filename.strip())
            with open(f"{filename.strip()}.kml", "rb") as file:
                st.download_button(
                    label="Download KML",
                    data=file,
                    file_name=f"{filename.strip()}.kml",
                    mime="application/vnd.google-earth.kml+xml",
                )
        else:
            st.warning("Please enter a valid filename.")