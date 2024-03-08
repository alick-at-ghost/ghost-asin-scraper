import requests
import urllib.parse
from credentials import credentials

# North America SP API endpoint (from https://developer-docs.amazon.com/sp-api/docs/sp-api-endpoints)
endpoint = "https://sellingpartnerapi-na.amazon.com"

# US Amazon Marketplace ID (from https://developer-docs.amazon.com/sp-api/docs/marketplace-ids)
marketplace_id = "ATVPDKIKX0DER"


def get_token(credentials):
    # Getting the LWA access token using the Seller Central App credentials. The token will be valid for 1 hour until it expires.
    token_response = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": credentials["refresh_token"],
            "client_id": credentials["lwa_app_id"],
            "client_secret": credentials["lwa_client_secret"],
        },
    )
    access_token = token_response.json()["access_token"]
    return access_token


def get_items(request_params):
    access_token = get_token(credentials)
    items = requests.get(
        endpoint
        # https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-reference#get-catalog2022-04-01items
        + "/catalog/2022-04-01/items"
        + "?"
        # encode query parameters to the URL
        + urllib.parse.urlencode(request_params),
        headers={
            # access token from LWA, every SP API request needs to have this header
            "x-amz-access-token": access_token,
        },
    )
    return items


def get_item_details_by_keyword(keyword):
    request_params = {
        "marketplaceIds": marketplace_id,  # required parameter
        "keywords": keyword,
        "includedData": 'identifiers, images, summaries, salesRanks, attributes, dimensions'
    }

    items = get_items(request_params)
    return items


def get_item_details_by_gtin(ean):
    request_params = {
        "marketplaceIds": marketplace_id,  # required parameter
        "identifiers": ean,
        "identifiersType": "EAN",
        "includedData": 'identifiers, images, summaries, salesRanks, attributes, dimensions'
    }

    items = get_items(request_params)
    return items