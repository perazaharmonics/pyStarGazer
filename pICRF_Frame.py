"""
This script makes use of the TLEs to estimate the position of the satellite as it projects its contour unto earth. It works by using the velocity and position vectors of the TLE and rotating the matrices until it
arrives at its final frame. It then plots is projected position unto a 2D representation of the Earth.

Future fixes: Add an error checking function to compare precision of position estimate:
# Obtain satellite data from a trusted API source
API_URL = 'https://api.trustedsource.com/satellite_position'
https://in-the-sky.org/ephemeris.php
params = {'satellite_name': satellite_name, 'time': t.utc_iso()}
trusted_data = requests.get(API_URL, params=params).json()

# Extract latitude and longitude from the trusted source
trusted_longitude = trusted_data['longitude']
trusted_latitude = trusted_data['latitude']

# Calculate the error in degrees
error_longitude = subpoint_longitude - trusted_longitude
error_latitude = subpoint_latitude - trusted_latitude

# Print and/or log the error
print(f"Error in Longitude: {error_longitude:.5f} degrees")
print(f"Error in Latitude: {error_latitude:.5f} degrees")

# Add a marker for the trusted source's subpoint
plt.plot(trusted_longitude, trusted_latitude, 'go', markersize=20, transform=ccrs.PlateCarree(), label='Trusted Source')

Author: Enrique Peraza



"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from skyfield.api import load, Topos
import numpy as np
from scipy.spatial.transform import Rotation as R
from time import gmtime, strftime
from datetime import datetime


# Load TLE data from Celestrak for satellites.
satellites = load.tle_file('https://celestrak.com/NORAD/elements/stations.txt')
by_name = {sat.name: sat for sat in satellites}

print("\n Listing of all satellites: \n")

satellite_names = list(by_name.keys())
for i, satellite_name in enumerate(satellite_names, start=1):
    print(f"{i}. {satellite_name}")

choice = int(input("\n Please choose a satellite number from the list above: \n"))
satellite_name = satellite_names[choice - 1]
satellite = by_name.get(satellite_name.strip())

if satellite is None:
    print("Satellite not found.")
else:
    # Load the timescale object.
    ts = load.timescale()

    # Get the current time.
    t = ts.now()
    
    # Compute the geocentric position and velocity of the satellite at time t.
    geocentric = satellite.at(t)
    # Position vector in the Geocentric Coordinate System (GCRS), aka ECI.
    r = geocentric.position.km
    print (" \n The position vector of the satellite of interest is given by: \n")
    print(r)

    # I, J, K components of the position vector in the ECI frame
    print("\n The Earth-Centered Inertial coordinate matrix: \n ")
    I, J, K = r
    IJK = np.vstack((I, J, K)).T
    print(IJK)

    print("\n at time: ")
    print(datetime.utcnow())

    print("\n Obtaining UT1: \n")
    # Get the current UT1
    UT1 = t.ut1
    print(UT1)

   

    # Get Greenwich Sidereal Time (GST)
    greenwich = Topos('0 N', '0 E')
    print(greenwich)

    print("\n Computing GST in degrees: \n")
    # Compute GST
    GST_deg = (UT1 * 360.98564724) % 360  # This gives GST in degrees
    print("\n The Greenwich Sidereal Time (GST) in degrees: \n")
    print(GST_deg)
    # Convert GST to radians
    GST_rad = np.deg2rad(GST_deg)

    print(" \n Defining the Earth Rotation Matrix around Z-axis: \n")
    # Define the Earth rotation matrix
    earth_rotation = R.from_rotvec(GST_rad * np.array([0, 0, 1]))  # Rotation around Z axis
    print(earth_rotation)

    # Define the position vector in the PECI frame
    r_PECI = r  # Use the actual position vector

    # Define the Earth rotation angle 
    earth_rotation_angle = GST_rad  # in radians
    print("\n The Earth rotation angle given by Greenwhich Sidereal Time (radians): \n")
    print(earth_rotation_angle)
    # Apply the rotation to the position vector to get True Equator True Mean 
    r_TOD = earth_rotation.apply(r_PECI)


    
    print("The ICRF J2000 coordinates of the satellite are: \n", r)
    # Get the longitude and latitude for the subpoint 
    # (the point on the Earth directly below the satellite).
    subpoint_longitude = geocentric.subpoint().longitude.degrees
    subpoint_latitude = geocentric.subpoint().latitude.degrees

    # Create a map using cartopy
    fig = plt.figure(figsize=(10, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()  # ensure we see the whole world map
    ax.coastlines()  # draw the coastlines

    # Add a marker for the satellite's subpoint
    sat_marker = plt.plot(subpoint_longitude, subpoint_latitude, 'ro', markersize=20, transform=ccrs.PlateCarree(), label='Satellite')

    # Add a marker for the satellite's beam
    beam_marker = plt.plot(subpoint_longitude, subpoint_latitude, 'bo', markersize=10, transform=ccrs.PlateCarree(), label='Beam Footprint')

    # Add a legend
    plt.legend(handles=[sat_marker[0], beam_marker[0]], loc='upper right')

    # Display longitude and latitude on the plot
    plt.text(subpoint_longitude + 5, subpoint_latitude + 5, f'Longitude: {subpoint_longitude:.2f}\nLatitude: {subpoint_latitude:.2f}', fontsize=9, transform=ccrs.PlateCarree())

    # Add a title to the plot with the satellite name
    plt.title(f"Satellite Projection: {satellite_name}")
    # Display UTC timestamp on the plot
    utc_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    plt.text(-170, 80, f'UTC Timestamp: {utc_time}', fontsize=9, transform=ccrs.PlateCarree())

    # zoom into the region around the subpoint
    # Adjust the values 
    zoom_scale = 550
    left_lon = max(-180, subpoint_longitude - zoom_scale)
    right_lon = min(180, subpoint_longitude + zoom_scale)
    bottom_lat = max(-90, subpoint_latitude - zoom_scale)
    top_lat = min(90, subpoint_latitude + zoom_scale)
    ax.set_extent([left_lon, right_lon, bottom_lat, top_lat])

    plt.show()
