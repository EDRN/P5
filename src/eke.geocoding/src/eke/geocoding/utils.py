# encoding: utf-8

'''🗺 EDRN Knowledge Environment geocoding: models.'''


from .models import InvestigatorAddress, Geocoding
from geocoder.uscensus_batch import USCensusBatch
from wagtail.models import Site
import logging, boto3, botocore, time

_aws_index = 'EDRN-Portal'
_logger    = logging.getLogger(__name__)
_max_wait  = 32
_reg       = 'us-east-2'


def _get_addresses_from_census(seq: list) -> list:
    '''Geecode locations of the addresses in ``seq`` using the free API from the United States Census.'''
    rc = []
    _logger.debug('Asking the US Census for %d addresses', len(seq))
    batch = USCensusBatch(seq)
    for addr, result in zip(seq, batch):
        if result.lat is None or result.lng is None: continue
        ia, _ = InvestigatorAddress.objects.get_or_create(address=addr, defaults=dict(lat=result.lat, lon=result.lng))
        rc.append((addr, ia))
    return rc


def _get_addresses_from_amazon(acc: str, sec: str, seq: list) -> list:
    '''Geocode locations of the addresses in ``seq`` using Amazon Location Servics.

    ``acc`` is the AWS access key ID while ``sec`` is the corresponding secret access key.
    '''
    client, wait, rc = boto3.client('location', aws_access_key_id=acc, aws_secret_access_key=sec, region_name=_reg), 1, []
    _logger.debug('Asking AWS for %d addresses', len(seq))
    while len(seq) > 0:
        addr = seq.pop(0)
        try:
            response = client.search_place_index_for_text(IndexName=_aws_index, Language='en', MaxResults=1, Text=addr)
            wait = 1
            results = response.get('Results', [])
            if len(results) > 0:
                place = results[0].get('Place', {})
                geometry = place.get('Geometry', {})
                point = geometry.get('Point', [])
                if len(point) == 2:
                    lon, lat = point[0], point[1]
                    ia, _ = InvestigatorAddress.objects.get_or_create(address=addr, defaults=dict(lat=lat, lon=lon))
                    rc.append((addr, ia))
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                continue
            elif e.response['Error']['Code'] == 'ThrottlingException':
                seq.append(addr)
                time.sleep(wait)
                wait *= 2
                if wait > _max_wait:
                    # We're waiting too long now so continuing on with the rest of the list is pointless.
                    # We'll just return what we've found so far. A future call with the missing addresses
                    # might have better luck.
                    return rc
            else:
                raise
    return rc


def get_addresses(seq: list) -> list:
    '''Geocode the addresses in the given ``seq``.

    Returns a new list of pairs: one address in ``seq`` and one ``InvestigatorAddress`` that matches it.
    Note that the length of the returned list may be less than that of ``seq``; that's because not all
    addresses may be found.
    '''
    settings = Geocoding.for_site(Site.objects.filter(is_default_site=True).first())
    if settings:
        acc, sec = settings.access_key, settings.secret_key
        if len(acc) > 5 and len(sec) > 5:
            return _get_addresses_from_amazon(acc, sec, seq)
    return _get_addresses_from_census(seq)


# Outside of all this, I called::
#
#     client.create_place_index(DataSource='Esri', Description='EDRN geocoding for the public portal', IndexName='EDRN-Portal')
#
# And got this return value::
#
#     {
#         'ResponseMetadata': {
#             'RequestId': 'f2cb271d-0065-47d7-ad7b-ec60efcd8967',
#             'HTTPStatusCode': 200,
#             'HTTPHeaders': {
#                 'date': 'Mon, 25 Jul 2022 20:30:14 GMT',
#                 'content-type': 'application/json',
#                 'content-length': '139',
#                 'connection': 'keep-alive',
#                 'x-amzn-requestid': 'f2cb271d-0065-47d7-ad7b-ec60efcd8967',
#                 'access-control-allow-origin': '*',
#                 'x-amz-apigw-id': '[REDACTED]',
#                 'access-control-expose-headers': 'x-amzn-errortype,x-amzn-requestid,x-amzn-errormessage,x-amzn-trace-id,x-amz-apigw-id,date',
#                 'x-amzn-trace-id': 'Root=1-62defd56-4c546d6d5379164f2bab24cc'
#             }, 
#             'RetryAttempts': 0
#         },
#         'CreateTime': datetime.datetime(2022, 7, 25, 20, 30, 14, 565000, tzinfo=tzlocal()),
#         'IndexArn': 'arn:aws:geo:us-east-2:300153749881:place-index/EDRN-Portal',
#         'IndexName': 'EDRN-Portal'
#     }
#
# This sets the ``_aws_index`` used above.
