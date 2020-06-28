import logging
import os
import boto3
from botocore.exceptions import ClientError
from ask_sdk_model.slu.entityresolution import StatusCode

def get_slot_value(handler_input, name, default=None):
    #If it matched a canonical value return this
    slots = handler_input.request_envelope.request.intent.slots
    if not slots or not name in slots:
        return default
    slot = slots[name]
    if slot.resolutions and slot.resolutions.resolutions_per_authority[0].status.code == StatusCode.ER_SUCCESS_MATCH:
        return slot.resolutions.resolutions_per_authority[0].values[0].value.name

    #Otherwise return the actual spoken value
    result = slot.value
    if result == None:
        return default
    return result

def get_persistent_session_attribute(handler_input, name, default=None):
    attr = handler_input.attributes_manager.persistent_attributes
    if not attr:
        return default
    if name in attr:
        return attr[name]
    return default

def set_persistent_session_attribute(handler_input, name, value):
    attr = handler_input.attributes_manager.persistent_attributes
    attr[name] = value

def set_session_attribute(handler_input, name, val):
    attr = handler_input.attributes_manager.session_attributes
    attr[name] = val

def get_session_attribute(handler_input, name, default=None):
    attr = handler_input.attributes_manager.session_attributes
    if name in attr:
        return attr[name]
    return default

def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object with a capped expiration of 60 seconds

    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
    try:
        bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=60*1)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response