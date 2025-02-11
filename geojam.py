import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import time
import simplekml
import os
import toml
from geopy.distance import geodesic

# Main page
st.image("assets/instructions.png", width=900)  # Adjust width as needed


# Ensure session state variables
if "results" not in st.session_state:
    st.session_state.results = []
if "password_attempted" not in st.session_state:
    st.session_state.password_attempted = False

# Load secrets from .streamlit/secrets.toml
SECRETS_PATH = ".streamlit/secrets.toml"

if os.path.exists(SECRETS_PATH):
    secrets = toml.load(SECRETS_PATH)
else:
    st.error("⚠️ secrets.toml NOT FOUND! Make sure it exists in the .streamlit directory.")
    st.stop()

stored_passcodes = secrets.get("passcodes", {})
api_key = secrets["google"].get("api_key", None)

# SIDEBAR UI
st.sidebar.image("assets/geojamlogo.png", use_column_width=True)
st.sidebar.subheader("Enter Search Parameters")

st.sidebar.markdown(
    '<p style="font-size: 15px; color: #007BFF; font-weight: bold; margin-bottom: 5px;">Contact us for a code: mermedata@gmail.com</p>',
    unsafe_allow_html=True
)

api_choice = st.sidebar.radio(
    "Choose your API key option:",
    ("Use a purchased code from GeoJam", "Use my own API Key"),
)

max_pages = 1

# Handle passcode
if api_choice == "Use a purchased code from GeoJam":
    password = st.sidebar.text_input(
        "Enter GeoJam passcode:", 
        type="password", 
        placeholder="Input the code you have received from us"
    )
    if password:
        st.session_state.password_attempted = True

    try:
        matched_user = next(
            (user for user, data in stored_passcodes.items()
             if isinstance(data, dict) and password.strip() == data.get("code", "").strip()), None
        )
        if matched_user:
            max_pages = int(stored_passcodes[matched_user].get("max_pages", 1))
            api_key = secrets["google"].get("api_key", None)
            st.sidebar.success(f"✅ Welcome, {matched_user}. Access granted. Max pages: {max_pages}")
            st.session_state.password_attempted = False
        else:
            st.sidebar.error("❌ Invalid passcode. Please try again.")
            st.stop()
    except KeyError:
        st.sidebar.error("GeoJam API key or passcode is not configured. Contact the administrator.")
        st.stop()

# Handle custom API key
elif api_choice == "Use my own API Key":
    api_key = st.sidebar.text_input("Enter your Google API Key:")
    if not api_key.strip():
        st.sidebar.warning("Please enter a valid API key to proceed.")
        st.stop()

# Ensure we have an API Key
if not api_key:
    st.error("⚠️ No API Key found. Please enter a valid passcode or API Key.")
    st.stop()

# Main input fields
query = st.sidebar.text_input("Enter search query (e.g., restaurants, cafes):")
location_str = st.sidebar.text_input("Enter location (latitude,longitude):", placeholder="40.7128,-74.0060")

radius = st.sidebar.slider(
    "Select radius (in meters):", 
    min_value=100, 
    max_value=10000,
    value=1000, 
    step=100
)
st.sidebar.markdown(
    "<p style='text-align: center; font-weight: bold;'>Max radius: 10km</p>", 
    unsafe_allow_html=True
)

run_query = st.sidebar.button("Run Search", help="Click to start searching")

# Show map if location is valid
if location_str.strip():
    try:
        lat_lng = location_str.split(",")
        if len(lat_lng) != 2:
            st.error("Invalid location format. Please use latitude,longitude.")
            st.stop()
        lat, lng = map(float, lat_lng)
        location = (lat, lng)

        m = folium.Map(location=location, zoom_start=12)
        folium.Circle(location=location, radius=radius, color="blue", fill=True, fill_opacity=0.2).add_to(m)
        folium.Marker(location=location, popup="Center Point").add_to(m)
        st_folium(m, width=1660, height=500)

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")
        st.stop()

def calculate_distance(lat1, lon1, lat2, lon2):
    return round(geodesic((lat1, lon1), (lat2, lon2)).meters, 2)  # Distance in meters

# Nearby Search + Place Details
if run_query:
    if not query.strip():
        st.error("⚠️ Please enter a search query.")
        st.stop()
    if not location_str.strip():
        st.error("⚠️ Please enter a valid location.")
        st.stop()

    try:
        st.session_state.results = []
        page_count = 1
        next_page_token = None

        while page_count <= max_pages:
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "keyword": query,
                "key": api_key
            }
            if next_page_token:
                params["pagetoken"] = next_page_token
                # A short delay so the next_page_token is recognized
                time.sleep(2)

            response = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)
            data = response.json()

            if "error_message" in data:
                st.error(f"⚠️ API Error: {data['error_message']}")
                st.stop()

            for result in data.get("results", []):
                place_id = result.get("place_id", "")
                name = result.get("name", "N/A")
                lat_ = result["geometry"]["location"]["lat"]
                lng_ = result["geometry"]["location"]["lng"]
                distance = calculate_distance(lat, lng, lat_, lng_)  # Calculate distance from input location
        
                vicinity = result.get("vicinity", "N/A")
                open_now = None
                if "opening_hours" in result:
                    open_now = result["opening_hours"].get("open_now", None)

                user_ratings_total = result.get("user_ratings_total", "N/A")
                price_level = result.get("price_level", "N/A")
                types = result.get("types", [])
                # Might also have a "plus_code" in the search result
                plus_code_search = result.get("plus_code", {}).get("compound_code", "N/A")

                # Default placeholders
                address = "N/A"
                google_url = "N/A"
                website = "N/A"
                phone = "N/A"
                hours_text = "N/A"
                plus_code_details = "N/A"
                wheelchair_accessible = "N/A"

                # Optional: Detailed data fetch
                if place_id:
                    details_params = {
                        "place_id": place_id,
                        "fields": (
                            "formatted_address,"
                            "website,"
                            "formatted_phone_number,"
                            "international_phone_number,"
                            "opening_hours,"
                            "url,"
                            "price_level,"
                            "user_ratings_total,"
                            "plus_code,"
                            "types,"
                            "wheelchair_accessible_entrance"  # may be beta or unsupported
                        ),
                        "key": api_key
                    }
                    details_res = requests.get("https://maps.googleapis.com/maps/api/place/details/json", params=details_params).json()
                    detail = details_res.get("result", {})

                    address = detail.get("formatted_address", address)
                    google_url = detail.get("url", google_url)
                    website = detail.get("website", website)
                    # Prefer international phone if present, else fallback
                    phone = detail.get("international_phone_number") or detail.get("formatted_phone_number") or phone

                    # Overwrite with details if available
                    if "opening_hours" in detail:
                        od = detail["opening_hours"]
                        # "open_now" might also be here
                        open_now = od.get("open_now", open_now)
                        # Hours schedule
                        weekday_text = od.get("weekday_text", [])
                        if weekday_text:
                            hours_text = "\n".join(weekday_text)

                    # Price level from details
                    if "price_level" in detail:
                        price_level = detail["price_level"]
                    # Ratings count from details
                    if "user_ratings_total" in detail:
                        user_ratings_total = detail["user_ratings_total"]
                    # plus_code from details
                    if "plus_code" in detail:
                        plus_code_details = detail["plus_code"].get("compound_code", plus_code_search)
                    # wheelchair accessible (beta)
                    # might be a boolean or missing altogether
                    if "wheelchair_accessible_entrance" in detail:
                        wheelchair_accessible = detail["wheelchair_accessible_entrance"]

                    # Merge types if details has more
                    detail_types = detail.get("types", [])
                    if detail_types:
                        types = detail_types

                # Final plus_code fallback
                final_plus_code = plus_code_details if plus_code_details != "N/A" else plus_code_search

                # Convert open_now to something more user-friendly
                if open_now is True:
                    open_status = "Open Now"
                elif open_now is False:
                    open_status = "Closed Now"
                else:
                    open_status = "Unknown"

                # Turn types list into a string
                types_str = ", ".join(types) if types else "N/A"

                # Add to results
                st.session_state.results.append({
                    "Name": name,
                    "Latitude": lat_,
                    "Longitude": lng_,
                    "Distance (m)": distance,  # Add calculated distance
                    "Address": address,
                    "Phone": phone,
                    "Hours": hours_text,
                    "Vicinity": vicinity,
                    "Status (Open Now)": open_status,
                    "User Ratings Total": user_ratings_total,
                    "Price Level": price_level,
                    "Website": website,
                    "Wheelchair Accessible": wheelchair_accessible,
                    "Plus Code": final_plus_code,
                    "Place ID": place_id,
                    "Types": types_str,
                    "Google URL": google_url
                })

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

            page_count += 1
            st.sidebar.info(f"Fetching page {page_count}...")

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")
        st.stop()

# Display the results
if st.session_state.results:
    results_df = pd.DataFrame(st.session_state.results)
    results_df.index = range(1, len(results_df) + 1)  # Ensure index starts from 1
    st.write("### Search Results")
    st.dataframe(results_df)

    filename = st.text_input("Enter a filename for export:", "results")

    if st.button("Save as CSV"):
        if filename.strip():
            st.download_button(
                "Download CSV",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{filename}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Please enter a valid filename.")

    if st.button("Save as KML"):
        def save_as_kml(data, filename):
            kml = simplekml.Kml()
            for index, row in data.iterrows():
                kml.newpoint(
                    name=row["Name"],
                    coords=[(row["Longitude"], row["Latitude"])],
                    description=(
                        f"<b>Address:</b> {row['Address']}<br>"
                        f"<b>Google URL:</b> {row['Google URL']}<br>"
                        f"<b>Phone:</b> {row['Phone']}<br>"
                        f"<b>Website:</b> {row['Website']}<br>"
                    )
                )
            kml.save(f"{filename}.kml")

        if filename.strip():
            save_as_kml(results_df, filename)
            with open(f"{filename}.kml", "rb") as file:
                st.download_button(
                    "Download KML",
                    data=file,
                    file_name=f"{filename}.kml",
                    mime="application/vnd.google-earth.kml+xml"
                )
        else:
            st.warning("⚠️ Please enter a valid filename.")
