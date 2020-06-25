import boto3
import os

s3 = boto3.client("s3", region_name="eu-west-1")


def get_matching_s3_objects(bucket, prefix="", key_pattern=""):
    """
    Generate objects in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch objects whose key starts with this string (optional).
    :param key_pattern: Only fetch objects whose key includes this string (optional).
    """
    kwargs = {"Bucket": bucket, "Prefix": prefix}

    while True:
        resp = s3.list_objects_v2(**kwargs)

        try:
            contents = resp["Contents"]
        except KeyError:
            return

        for obj in contents:
            key = obj["Key"]
            if key_pattern in key:
                yield obj

        try:
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
        except KeyError:
            break


def get_matching_s3_keys(bucket, prefix="", key_pattern=""):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param key_pattern: Only fetch keys that include this string (optional).
    """
    print(
        "\tLooking for S3 keys with prefix '{}' and including pattern '{}' in bucket '{}'".format(
            prefix, key_pattern, bucket
        )
    )
    for obj in get_matching_s3_objects(bucket, prefix, key_pattern):
        yield obj["Key"]


def parse_bucket_and_key_path(s3_url):
    url_tokens = s3_url.split("/")
    bucket = url_tokens[2]
    key_path = "/".join(url_tokens[3:])
    return bucket, key_path


def create_file(bucket_name, key, content_bytes):
    return s3.put_object(Bucket=bucket_name, Key=key, Body=content_bytes)


def delete_file(bucket_name, key):
    return s3.delete_object(Bucket=bucket_name, Key=key)


def copy_file(bucket_name, key, new_obj_key):
    copy_source = {'Bucket': bucket_name, 'Key': key}
    return s3.copy_object(CopySource=copy_source, Bucket=bucket_name, Key=new_obj_key)


def object_fetch(bucket_name, fileName):
    return s3.get_object(Bucket=bucket_name, Key=fileName)


def object_exists(bucket_name, key):
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
        return True
    except Exception as e:
        return False


def list_directories(bucket_name, key):
    result = s3.list_objects(Bucket=bucket_name, Prefix=key, Delimiter='/')
    contents = result.get('Contents')
    if contents:
        return [os.path.basename(content['Key']) for content in contents]
    elif 'CommonPrefixes' in result and result['CommonPrefixes']:
        return [prefix['Prefix'] for prefix in result['CommonPrefixes']]
    else:
        return []


def get_presigned_url(s3_file):
    bucket, key = parse_bucket_and_key_path(s3_file)
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        # 7 days
        ExpiresIn=604800,
    )
