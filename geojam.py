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
if "password_attempted" not in st.session_state:
    st.session_state.password_attempted = False

# Sidebar Inputs
st.sidebar.image("assets/geojamlogo.png", use_container_width=True)
st.sidebar.subheader("Enter Search Parameters")

# 🔹 Always Visible: Contact Us Message
st.sidebar.markdown(
    '<p style="font-size: 15px; color: #007BFF; font-weight: bold; margin-bottom: 5px;">Contact us for a code: mermedata@gmail.com</p>',
    unsafe_allow_html=True
)

# API Key Selection
api_choice = st.sidebar.radio(
    "Choose your API key option:",
    ("Use a purchased code from GeoJam", "Use my own API Key"),
)

api_key = None  # Default to None

# Handle GeoJam API Key Input with Multiple Passcodes
if api_choice == "Use a purchased code from GeoJam":
    password = st.sidebar.text_input(
        "Enter GeoJam passcode:", 
        type="password", 
        placeholder="Input the code you have received from us"
    )

    if password:
        st.session_state.password_attempted = True

    try:
        stored_passcodes = st.secrets.get("passcodes", {})

        valid_user = None
        for user, stored_code in stored_passcodes.items():
            if password == stored_code:
                valid_user = user
                break

        if valid_user:
            api_key = st.secrets["google"]["api_key"]
            st.sidebar.success(f"✅ Welcome, {valid_user}. Access granted.")
            st.session_state.password_attempted = False
        else:
            st.sidebar.error("❌ Invalid passcode. Please try again.")
    except KeyError as e:
        st.sidebar.error("GeoJam API key or passcode is not configured. Contact the administrator.")

# Handle Custom API Key Input
elif api_choice == "Use my own API Key":
    api_key = st.sidebar.text_input("Enter your Google API Key:")
    if not api_key.strip():
        st.sidebar.warning("Please enter a valid API key to proceed.")

# **🔍 Ensure API Key is Set**
if not api_key:
    st.error("⚠️ No API Key found. Please enter a valid passcode or API Key.")
    st.stop()

# Query Input
query = st.sidebar.text_input("Enter search query (e.g., restaurants, cafes):")
location_str = st.sidebar.text_input("Enter location (latitude,longitude):", placeholder="40.7128,-74.0060")

# Adjusted Radius Slider UI
radius = st.sidebar.slider(
    "Select radius (in meters):", 
    min_value=1, 
    max_value=10000, 
    value=1000, 
    step=100
)
st.sidebar.markdown(f"<p style='text-align: center; font-weight: bold;'>{radius} meters</p>", unsafe_allow_html=True)

run_query = st.sidebar.button("Run Search", help="Click to start searching")

# **🔍 Ensure Query & Location are Set**
if run_query:
    if not query.strip():
        st.error("⚠️ Please enter a search query.")
        st.stop()
    if not location_str.strip():
        st.error("⚠️ Please enter a valid location.")
        st.stop()

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
if run_query:
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
            st.error(f"⚠️ API Error: {data['error_message']}")
            st.stop()

        # Process Results (FULL RESTORE)
        results = []
        for result in data.get("results", []):
            place_id = result["place_id"]
            details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {"place_id": place_id, "key": api_key}
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

# Display Results
if st.session_state.results:
    results_df = pd.DataFrame(st.session_state.results)
    st.write("### Search Results")
    st.dataframe(results_df)

    # **🔍 Ensure `filename` is defined before using it**
    filename = st.text_input("Enter a filename for export:", "results")

    if st.button("Save as CSV"):
        if filename.strip():
            st.download_button("Download CSV", data=results_df.to_csv(index=False).encode("utf-8"), file_name=f"{filename}.csv", mime="text/csv")
        else:
            st.warning("⚠️ Please enter a valid filename.")

    if st.button("Save as KML"):
        def save_as_kml(data, filename):
            kml = simplekml.Kml()
            for index, row in data.iterrows():
                kml.newpoint(
                    name=row["Name"],
                    coords=[(row["Longitude"], row["Latitude"])],
                    description=f"""
                        <b>Address:</b> {row["Formatted Address"]}<br>
                        <b>Google URL:</b> {row["Google URL"]}<br>
                    """
                )
            kml.save(f"{filename}.kml")

        if filename.strip():
            save_as_kml(results_df, filename)
            with open(f"{filename}.kml", "rb") as file:
                st.download_button("Download KML", data=file, file_name=f"{filename}.kml", mime="application/vnd.google-earth.kml+xml")
        else:
            st.warning("⚠️ Please enter a valid filename.")