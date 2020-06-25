import s2sphere as s2
from ast import literal_eval as make_tuple


def grab_index_s2(tup):
    """
    Same as grab_index_s2 but for a (lat,lng) tuple
    :param tup: (lat,lng) or "(lat,lng)"
    :return:
    """
    if not isinstance(tup, tuple):
        tup = make_tuple(tup)
    return s2.CellId.from_lat_lng(s2.LatLng.from_degrees(tup[1], tup[0]))


def neighbourhood_of_point(cellid, angle):
    """
    Calculates Neighbourhood of a single point (with a view to be used on stretching boundary  of origin or destination
    gps traces)
    :param cellid:
    :return:
    """
    s2angle = s2.Angle.from_degrees(angle)
    if not isinstance(cellid, s2.CellId):
        cellid = s2.CellId(cellid)
    p = cellid.to_lat_lng()
    return s2.LatLngRect.from_point(p).convolve_with_cap(s2angle)


def s2_intersection(s2_cell_1, s2_cell_2, parent_level):
    return s2_cell_1.parent(parent_level).intersects(s2_cell_2.parent(parent_level))


def origins_destinations_intersect(s2_origin_series, s2_destination_series, parent_level):
    s2_origin_series_next = s2_origin_series.shift(-1).dropna()
    for i in s2_origin_series_next.index:
        if not s2_intersection(s2_origin_series_next[i], s2_destination_series[i], parent_level):
            return False
    return True


def cell_union_from_region_coverer(region_coverer_cells):
    cell_ids = []
    for cell in region_coverer_cells:
        l = len(cell)
        c = cell + '0' * (16 - l)
        cell_ids.append(s2.CellId(id_=int(c, 16)))
    return s2.CellUnion(cell_ids=cell_ids)


def intersection_mask(s2_cell_id_series, cell_union):
    def intersects(x, cell_union):
        return cell_union.intersects(x)

    return s2_cell_id_series.apply(lambda x: intersects(x, cell_union))


def get_trips_to_from_s2_cells(df_trips, hex_s2_cells):
    """
    Filter the trips on ones that have origin/destination in London
    get the whole day on which you have trips in london. This will form the basis of plans
    so don't want to skip any intermediate trips
    :return:
    """

    cell_union = cell_union_from_region_coverer(hex_s2_cells)
    df_ = df_trips[
        intersection_mask(df_trips['destination_s2'], cell_union) | intersection_mask(df_trips['origin_s2'],
                                                                                      cell_union)].reset_index(
        drop=True)

    # get the whole days of those trips
    return df_trips[df_trips['date'].isin(df_['date'].unique())]


def parse_spatial_data_df_trips(df_trips):
    """
    get lat lon and then s2 cells for origins and destinations for df_trips which have come from a postgis db
    :return:
    """
    from shapely import wkb

    def convert_to_lat_lon(encoded_point):
        return wkb.loads(encoded_point, hex=True).coords[0]

    df_trips['origin_lat_lon'] = df_trips['origin'].apply(lambda x: convert_to_lat_lon(x))
    df_trips['destination_lat_lon'] = df_trips['destination'].apply(lambda x: convert_to_lat_lon(x))
    df_trips['origin_lat'] = df_trips['origin_lat_lon'].apply(lambda x: x[1])
    df_trips['origin_lon'] = df_trips['origin_lat_lon'].apply(lambda x: x[0])
    df_trips['destination_lat'] = df_trips['destination_lat_lon'].apply(lambda x: x[1])
    df_trips['destination_lon'] = df_trips['destination_lat_lon'].apply(lambda x: x[0])
    df_trips['origin_s2'] = df_trips['origin_lat_lon'].apply(lambda x: grab_index_s2(x))
    df_trips['destination_s2'] = df_trips['destination_lat_lon'].apply(
        lambda x: grab_index_s2(x))
    return df_trips
