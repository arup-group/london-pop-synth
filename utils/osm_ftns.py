import osmapi
import pyproj
import numpy as np
import re
import pandas as pd


api = osmapi.OsmApi()


def postcode(string):
    x = re.findall(r'\b[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}\b', string)
    return x


def parse_osm_to_building_types(osm_rip):
    def add_to_buildings_count(building):
        if building in buildings.keys():
            buildings[building] = buildings[building] + 1
        else:
            buildings[building] = 1

    buildings = {}
    yes_building_types = ['religion', 'office', 'shop', 'tourism', 'amenity']
    # amenity could be many things, courthouse, library, casino, save those tag values instead

    for item in osm_rip:
        if item['type'] == 'way' and ('building' in item['data']['tag'].keys()):
            tags = item['data']['tag']
            # found a building, now what is it?
            if tags['building'] == 'yes':
                # it is a building, great.
                for tag in tags.keys():
                    if tag in yes_building_types:
                        if tag=='amenity':
                            add_to_buildings_count(building=tags[tag])
                        else:
                            add_to_buildings_count(building=tag)
                        break
            else:
                building = tags['building']
                if postcode(building):
                    pass
                else:
                    add_to_buildings_count(building)
    return buildings


def infer_activity_from_osm_buildings_count(buildings_count):
    activities = {
        'work': ['office', 'offices', 'industrial', 'warehouse'],
        'education': ['school', 'adult_education', 'university'],
        # ignore home for the time being, we assume the origin of the first trip is home and any other location isn't
        # 'home': ['house', 'apartments', 'bungalow', 'cabin', 'detached', 'dormitory', 'farm', 'hotel', 'houseboat',
        #          'residential', 'static_caravan', 'terrace', 'hut'],
        'shop': ['shop', 'commercial', 'retail', 'department_store', 'kiosk', 'supermarket', 'bakehouse'],
        'personal': ['courthouse', 'townhall', 'roof', 'pharmacy', 'dentist', 'hospital', 'bank', 'post_office',
                     'veterinary', 'register_office'],
        'recreation': ['library', 'casino', 'cinema', 'restaurant', 'pub', 'cafe', 'bar', 'community_centre',
                       'sports_centre', 'swimming_pool', 'fast_food', 'nightclub', 'food_court', 'social_facility'],
        'religious': ['place_of_worship', 'church', 'cathedral', 'chapel', 'church', 'mosque', 'religious', 'shrine',
                      'synagogue', 'temple'],
        'tourism': ['tourism'],
        # removed 'garage', 'garages' from other because there are shit loads of garages everywhere?!
        'other': ['parking', 'toilets', 'embassy', 'government', 'public', 'fuel'],
        'escort': ['kindergarten']
    }
    # flatten the dict above - the items in the lists are new keys and keys are values
    new_keys = []
    new_values = []
    for key, value in activities.items():
        for item in value:
            new_keys.append(item)
            new_values.append(key)
    flat_activities_dict = dict(zip(new_keys, new_values))

    # make a pd.DataFrame from the count dictionary
    _d = pd.DataFrame(buildings_count, index=['count']).T.reset_index().rename(columns={'index':'building'})
    # the new index is non-negative integers and 'building' column holds the building type from osm
    _d['activity'] = _d['building'].map(flat_activities_dict)
    df_activity = _d.groupby('activity').sum().reset_index()

    return df_activity.loc[df_activity['count'].idxmax(), 'activity']


def download_osm(lon, lat, radius):
    """
    Returns json response from the osm api bounded by lon and lat radius distance away from lon,lat
    :param lat:
    :param lon:
    :param radius: in meters
    :return:
    """
    # Only worked in the neighbourhood of Britain
    # p1 = pyproj.Proj(init='epsg:4326')
    # p2 = pyproj.Proj(init='epsg:27700')
    # Changed to approximation,  reference:
    # https://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    # 111,111 meters (111.111 km) in the y direction is 1 degree (of latitude)
    # and 111,111 * cos(latitude) meters in the x direction is 1 degree (of longitude).
    # unit_lon and unit_lon are unit displacements per meter
    lat_disp = float(radius) / 111111
    lon_disp = float(radius) / (111111 * np.cos(np.radians(float(lat))))
    min_lat, max_lat = float(lat) - lat_disp, float(lat) + lat_disp
    min_lon, max_lon = float(lon) - lon_disp, float(lon) + lon_disp

    # see https://wiki.openstreetmap.org/wiki/Map_Features for info on the output
    return api.Map(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)


'''
osm = download_osm(-1.2,51.51,1000)
print(osm)
'''
