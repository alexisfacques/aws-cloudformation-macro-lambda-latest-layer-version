import logging
import os
import re
from typing import Dict, List

# From requirements.txt:
import boto3
import botocore
from logmatic import JsonFormatter


FUNCTION_NAME = os.getenv('AWS_LAMBDA_FUNCTION_NAME', __name__)
LOG_LEVEL = os.environ.get('LOG_LEVEL', logging.INFO)

LAMBDA_LAYER_RE = (r'^arn:(?:aws[a-zA-Z-]*)?:lambda:[a-z]{2}(?:(?:-gov)|(?:-is'
                   'o(?:b?)))?-[a-z]+-\d{1}:\d{12}:layer:([a-zA-Z0-9-_]+)')

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger(FUNCTION_NAME)
logger.propagate = False
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)

client = boto3.client('lambda')


def lambda_handler(event: Dict, *_args, **_kwargs):
    """
    CloudFormation Macro handler.

    This Lambda function, to be invoked by CloudFormation, takes a lambda
    'LayerName' as parameter and return the latest LayerVersionArn for given
    layer, if any.

    :param event: a dictionnary expected to contain the following keys:
                    - requestId: the CloudFormation requestId;
                    - params.LayerName: the lambda layer name.

    """
    response: Dict = {
        'requestId': event.get('requestId', ''),
        'status': 'failed'
    }

    logger.debug('Got event.', extra={'event': event})

    try:
        # Get the layer name.

        layer_name = ''.join(event['params']['LayerName'])

        compatible_runtime = ''.join(event['params']
                                     .get('CompatibleRuntime', ''))

        # Check if layer_name is an ARN.
        # If so, get the LayerVersion name.
        if (match := re.match(LAMBDA_LAYER_RE, layer_name)):
            layer_name = match.group(1)

    except KeyError as err:
        logger.error('Missing event parameter %s.', err,
                     extra={'error': type(err).__name__,
                            'errorDetail': str(err).strip('\''),
                            'event': event})

        return {**response,
                'errorMessage': 'Missing mandatory "LayerName" parameter.'}

    try:
        # Get the latest layer version.

        query_params: Dict = {
            'LayerName': layer_name,
            'MaxItems': 1
        }

        if compatible_runtime:
            query_params['CompatibleRuntime'] = compatible_runtime

        layer_version_arn = client.list_layer_versions(
            **query_params)['LayerVersions'][0]['LayerVersionArn']

        logger.debug('Got latest layer version.',
                     extra={'layer_version_arn': layer_version_arn})

    except (KeyError, TypeError) as err:
        logger.error('Received unexpected response from the Boto API.', err,
                     extra={'error': type(err).__name__,
                            'errorDetail': str(err).strip('\''),
                            'event': event})

        error_message = 'Unexpected response from the Boto API.'

    except (IndexError, client.exceptions.ResourceNotFoundException) as err:
        logger.warning('Lambda layer does not exist.', err,
                     extra={'error': type(err).__name__,
                            'errorDetail': str(err).strip('\''),
                            'event': event})

        error_message = 'Lambda layer "%s" %s does not exist.' % (
            layer_name, ('with compatible runtime "%s"' % compatible_runtime)
            if compatible_runtime else ''
        )

    except client.exceptions.InvalidParameterValueException as err:
        logger.warning('Failed to get a lambda layer version.', err,
                     extra={'error': type(err).__name__,
                            'errorDetail': str(err).strip('\''),
                            'event': event})

        error_message = 'Invalid layer name.'

    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'] == 'ValidationException' \
                and compatible_runtime:
            logger.warning('Failed to get a lambda layer version: Invalid '
                           'CompatibleRuntime.', err,
                           extra={'error': type(err).__name__,
                                  'errorDetail': str(err).strip('\''),
                                  'event': event})

            error_message = ('Parameter "CompatibleRuntime" failed to satisfy '
                             'constraint.')

        else:
            raise err

    except (client.exceptions.ServiceException, Exception) as err:
        logger.exception('Unhandled exception getting the lambda layer '
                         'versions',
                         extra={'error': type(err).__name__,
                                'errorDetail': str(err),
                                'event': event})

        error_message = 'Unhandled exception.'

    else:
        return {**response,
                'status': 'success',
                'fragment': layer_version_arn}

    return {**response,
            'errorMessage': error_message}
