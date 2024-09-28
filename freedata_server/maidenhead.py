import math
import random

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the Earth (specified in decimal degrees).

    Parameters:
    lat1, lon1: Latitude and longitude of point 1.
    lat2, lon2: Latitude and longitude of point 2.

    Returns:
    float: Distance between the two points in kilometers.
    """
    # Radius of the Earth in kilometers. Use 3956 for miles
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Difference in coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return distance


def maidenhead_to_latlon(grid_square):
    """
    Convert a Maidenhead locator to latitude and longitude coordinates.
    The output coordinates represent the southwestern corner of the grid square.

    Parameters:
    grid_square (str): The Maidenhead locator.

    Returns:
    tuple: A tuple containing the latitude and longitude (in that order) of the grid square's center.
    """

    grid_square = generate_full_maidenhead(grid_square)

    grid_square = grid_square.upper()
    lon = -180 + (ord(grid_square[0]) - ord('A')) * 20
    lat = -90 + (ord(grid_square[1]) - ord('A')) * 10
    lon += (int(grid_square[2]) * 2)
    lat += int(grid_square[3])

    if len(grid_square) >= 6:
        lon += (ord(grid_square[4]) - ord('A')) * (5 / 60)
        lat += (ord(grid_square[5]) - ord('A')) * (2.5 / 60)

    # not needed now as we always have 6 digits
    if len(grid_square) == 8:
        lon += int(grid_square[6]) * (5 / 600)
        lat += int(grid_square[7]) * (2.5 / 600)

    # Adjust to the center of the grid square
    # not needed now as we always have 6 digits
    if len(grid_square) <= 4:
        lon += 1
        lat += 0.5
    elif len(grid_square) == 6:
        lon += 2.5 / 60
        lat += 1.25 / 60
    else:
        lon += 2.5 / 600
        lat += 1.25 / 600

    return lat, lon


def distance_between_locators(locator1, locator2):
    """
    Calculate the distance between two Maidenhead locators and return the result as a dictionary.

    Parameters:
    locator1 (str): The first Maidenhead locator.
    locator2 (str): The second Maidenhead locator.

    Returns:
    dict: A dictionary containing the distances in kilometers and miles.
    """
    lat1, lon1 = maidenhead_to_latlon(locator1)
    lat2, lon2 = maidenhead_to_latlon(locator2)
    km = haversine(lat1, lon1, lat2, lon2)
    miles = km * 0.621371
    return {'kilometers': km, 'miles': miles}


import random


import random
import string

def generate_full_maidenhead(grid_square):
    """
    Convert a Maidenhead locator of 2 or 4 characters to a 6-character locator
    by generating random characters for the missing positions, while ensuring the correct format:
    1-2: Uppercase letters (A-R)
    3-4: Digits (0-9)
    5-6: Lowercase letters (a-r)

    Parameters:
    grid_square (str): A 2, 4, or 6 character Maidenhead locator.

    Returns:
    str: A 6-character Maidenhead locator.
    """

    grid_square = grid_square.upper()

    # If the grid square is longer than 6 characters, strip it to 6 characters
    if len(grid_square) > 6:
        grid_square = grid_square[:6]

    if len(grid_square) == 2:
        # Generate random digits for positions 3 and 4
        grid_square += f"{random.randint(0, 9)}{random.randint(0, 9)}"
        # Generate random lowercase letters from 'a' to 'r' for positions 5 and 6
        grid_square += random.choice("abcdefghijklmnopqr")
        grid_square += random.choice("abcdefghijklmnopqr")

    elif len(grid_square) == 4:
        # Generate random lowercase letters from 'a' to 'r' for positions 5 and 6
        grid_square += random.choice("abcdefghijklmnopqr")
        grid_square += random.choice("abcdefghijklmnopqr")

    elif len(grid_square) == 6:
        # If grid square is valid and already 6 characters, enforce format
        grid_square = grid_square[:2].upper() + grid_square[2:4] + grid_square[4:6].lower()
        return grid_square

    else:
        raise ValueError("Grid square must be 2, 4, or 6 characters long.")

    # Adjust the case for the last two characters
    grid_square = grid_square[:4] + grid_square[4:].lower()
    return grid_square


