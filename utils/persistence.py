import gzip
import os
import zlib
from io import BytesIO
import pandas as pd
import geopandas as gp
from lxml import etree as et
from halo import Halo

from utils import aws_s3_ftns


def is_s3_location(location):
    return location.lower().startswith("s3://")


def is_csv(location):
    return location.lower().endswith(".csv")


def is_xlsx(location):
    return location.lower().endswith(".xlsx")


def is_xml(location):
    return location.lower().endswith(".xml")


def is_shp(location):
    return location.lower().endswith(".shp")


def is_gzip(location):
    return location.lower().endswith(".gz") or location.lower().endswith(".gzip")


def file_exists(location):
    if is_s3_location(location):
        bucket, key = aws_s3_ftns.parse_bucket_and_key_path(location)
        return aws_s3_ftns.object_exists(bucket, key)
    else:
        return os.path.isfile(location)


def dir_exists(location):
    if is_s3_location(location):
        if location[-1] != '/':
            location = location + '/'
        bucket, key = aws_s3_ftns.parse_bucket_and_key_path(location)
        dirs = aws_s3_ftns.list_directories(bucket, key)
        return any(dirs)
    else:
        return os.path.exists(location)


def list_dir(location):
    if is_s3_location(location):
        if location[-1] != '/':
            location = location + '/'
        bucket, key_path = aws_s3_ftns.parse_bucket_and_key_path(location)
        return aws_s3_ftns.list_directories(bucket, key_path)
    else:
        return os.listdir(location)


def gzip_content(content):
    gz_body = BytesIO()
    gz = gzip.GzipFile(None, "wb", 9, gz_body)
    gz.write(content.encode("utf-8"))
    gz.close()
    return gz_body.getvalue()


def xml_content(content, matsim_DOCTYPE, matsim_filename):
    xml_version = b'<?xml version="1.0" encoding="UTF-8"?>'
    doc_type = '<!DOCTYPE {} SYSTEM "http://matsim.org/files/dtd/{}.dtd">'.format(matsim_DOCTYPE, matsim_filename).encode()
    tree = xml_tree(content)
    return xml_version+doc_type+tree


def xml_tree(content):
    tree = et.tostring(content,
                       pretty_print=True,
                       xml_declaration=False,
                       encoding='UTF-8')
    return tree


def read_content(location, **kwargs):
    print("\tReading data from location '{}'".format(location))
    if is_csv(location):
        location_content = pd.read_csv(location, **kwargs)
    elif is_xlsx(location):
        location_content = pd.read_excel(location, **kwargs)
    elif is_shp(location):
        location_content = gp.read_file(location, **kwargs)
    elif is_s3_location(location):
        bucket, key = aws_s3_ftns.parse_bucket_and_key_path(location)
        s3_obj = aws_s3_ftns.object_fetch(bucket, key)
        location_content = s3_obj["Body"].read()
        if is_gzip(location):
            location_content = zlib.decompress(location_content, 16 + zlib.MAX_WBITS)
    else:
        if is_gzip(location):
            content_file = gzip.open(location, "r")
        else:
            content_file = open(location, "r")
        location_content = content_file.read()
        content_file.close()

    return location_content


def create_local_dir(directory):
    if not os.path.exists(directory):
        print('Creating {}'.format(directory))
        os.makedirs(directory)


def write_content(content, location, **kwargs):
    if is_s3_location(location):
        bucket, key_path = aws_s3_ftns.parse_bucket_and_key_path(location)
        print("\tWriting output to S3 (bucket={}, key={})".format(bucket, key_path))
        if is_gzip(location):
            binary_content = gzip_content(content)
        elif is_csv(location):
            binary_content = content.to_csv(None).encode()
        elif is_xml(location):
            binary_content = xml_content(content, **kwargs)
        else:
            try:
                binary_content = content.encode("utf-8")
            except UnicodeDecodeError as e:
                # assume the content is already a binary stream
                binary_content = content
        aws_s3_ftns.create_file(bucket, key_path, binary_content)
    else:
        with Halo(text="\tWriting output to local file system at {}".format(location), spinner='dots') as spinner:
            create_local_dir(os.path.dirname(location))
            if isinstance(content, pd.DataFrame):
                content.to_csv(location)
            else:
                if is_xml(location):
                    content = xml_content(content, **kwargs)
                if is_gzip(location):
                    file = gzip.open(location, "w")
                else:
                    file = open(location, "wb")
                file.write(content)

                spinner.succeed('Content written to {}'.format(location))
                file.close()
