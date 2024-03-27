import math

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
    if len(grid_square) < 4 or len(grid_square) % 2 != 0:
        raise ValueError("Grid square must be at least 4 characters long and an even length.")

    grid_square = grid_square.upper()
    lon = -180 + (ord(grid_square[0]) - ord('A')) * 20
    lat = -90 + (ord(grid_square[1]) - ord('A')) * 10
    lon += (int(grid_square[2]) * 2)
    lat += int(grid_square[3])

    if len(grid_square) >= 6:
        lon += (ord(grid_square[4]) - ord('A')) * (5 / 60)
        lat += (ord(grid_square[5]) - ord('A')) * (2.5 / 60)

    if len(grid_square) == 8:
        lon += int(grid_square[6]) * (5 / 600)
        lat += int(grid_square[7]) * (2.5 / 600)

    # Adjust to the center of the grid square
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
