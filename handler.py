import datetime
import json
import os
from io import BytesIO

import boto3
import PIL
from PIL import Image


def resized_image_url(resized_key, bucket, region):
    return "https://s3-{region}.amazonaws.com/{bucket}/{resized_key}".format(
        bucket=bucket, region=region, resized_key=resized_key
    )

def resize_image(bucket_name, key, size):
    size_split = size.split('x')
    s3 = boto3.resource('s3')
    obj = s3.Object(
        bucket_name=bucket_name,
        key=key,
    )
#
    file_ext_split = key.split('.')
    file_ext = str(file_ext_split[1])
    if file_ext == 'jpg':
        file_ext = 'jpeg'
#
    obj_body = obj.get()['Body'].read()

    img = Image.open(BytesIO(obj_body))
    img_width, img_height = img.size
    img_ratio = int(size_split[0]) * int(img_height)
    img_ratio //= int(img_width)
    img = img.resize(
        (int(size_split[0]), img_ratio), PIL.Image.ANTIALIAS
    )    
    
    # img = img.resize(
    #     (int(size_split[0]), int(size_split[1])), PIL.Image.ANTIALIAS
    # )
    buffer = BytesIO()
    img.save(buffer, file_ext.upper())
    buffer.seek(0)
    
    new_size = str(size_split[0]) + 'x' + str(img_ratio)
    resized_key="{size}_{key}".format(size=new_size, key=key)
    obj = s3.Object(
        bucket_name=bucket_name,
        key=resized_key,
    )
#
    ct_type = 'image/' + file_ext
#
    obj.put(Body=buffer, ContentType=ct_type)

    return resized_image_url(
        resized_key, bucket_name, os.environ["AWS_REGION"]
    )

def call(event, context):
    key = event["pathParameters"]["image"]
    size = event["pathParameters"]["size"]

    result_url = resize_image(os.environ["BUCKET"], key, size)

    response = {
        "statusCode": 301,
        "body": "",
        "headers": {
            "location": result_url
        }
    }

    return response
