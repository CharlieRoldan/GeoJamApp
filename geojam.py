import streamlit as st
import pandas as pd
import requests
from geopy.distance import distance


# Initialize session state variables
if "results" not in st.session_state:
    st.session_state.results = None


# Sidebar: Inputs and Logo
st.sidebar.title("GeoJam App")
st.sidebar.write("Your Location-Based Search Tool")

# Add a placeholder for the logo (use your own logo file here)
st.sidebar.image("https://via.placeholder.com/150", use_column_width=True)  # Replace with your logo URL or file path

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

# Map Display
if location_str.strip():
    try:
        # Parse the Lat/Long
        location = tuple(map(float, location_str.split(",")))

        # Display Map
        st.subheader("Location Map")
        st.map(pd.DataFrame([{"lat": location[0], "lon": location[1]}]), zoom=12)

    except ValueError:
        st.error("Invalid location format. Please enter as latitude,longitude.")