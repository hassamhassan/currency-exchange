#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from decimal import Decimal

import boto3
import requests


def get_exchange_rates(event, context):
    """
    This Lambda handler function is triggered by an event.
    Get the exchange rate xml data from the European Central Bank and stores it in DynamoDB.

    Args:
        event (dict): The event data that triggered the Lambda function.
        context (LambdaContext): The runtime information of the Lambda function.

    Returns:
        dict: A response containing the HTTP status code and a message indicating the success of the operation.
    Raises:
        requests.exceptions.RequestException: If there is an error fetching the XML data.
        boto3.exceptions.Boto3Error: If there is an error interacting with DynamoDB.
    """
    with requests.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml") as response:
        data = response.content

    currency_rates = parse_xml_exchange_rates(data)
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("CurrencyRates")

    items = [
        {
            "Currency": currency,
            "Rate": Decimal(str(rate)),
            "Timestamp": datetime.now(timezone.utc).date().isoformat(),
        }
        for currency, rate in currency_rates.items()
    ]

    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps("Exchange rates obtained and stored successfully."),
    }


def parse_xml_exchange_rates(xml_data):
    """
        Parse the XML data to get exchange rates.

        Args:
            data (bytes): XML data.

        Returns:
            dict: Dictionary of currency codes and their related exchange rates.
        """
    exchange_rates = {}

    root = ET.fromstring(xml_data)
    namespaces = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                  'default': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}

    for cube_time in root.findall('default:Cube/default:Cube', namespaces):
        for cube in cube_time.findall('default:Cube', namespaces):
            currency = cube.get('currency')
            rate = float(cube.get('rate'))
            exchange_rates[currency] = rate
    return exchange_rates
