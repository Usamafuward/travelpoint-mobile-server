from geopy import distance
from pydantic import BaseModel

class CoordinateRequest(BaseModel):
    lat1: float
    lon1: float
    lat2: float
    lon2: float

async def calculate_coordinate_difference(coords: CoordinateRequest):
    point_A = (coords.lat1, coords.lon1)
    point_B = (coords.lat2, coords.lon2)
    
    # Calculate the distance between the two points using the geodesic distance formula
    distance_km = distance.distance(point_A, point_B).km
    return round(distance_km, 2)
