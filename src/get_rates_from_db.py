#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta, timezone
from typing import Dict

import boto3
from boto3.dynamodb.conditions import Key


def get_rates_delta(event: dict, context: object) -> dict:
    """
    Gets present and previous days exchange rates data from DB and calculates delta.

    This Lambda handler function is triggered by an event.
    It queries DynamoDB for the exchange rates of the current and previous day, then calculates the changes in rates.

    Args:
        event (dict): AWS Lambda event dict.
        context (object): AWS Lambda context object.

    Returns:
        dict: Contains statuscode and response body.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("CurrencyRates")

    today_date = datetime.now(timezone.utc).date()
    today_date_iso = today_date.isoformat()
    yesterday_iso = (today_date - timedelta(days=1)).isoformat()

    present_rates = get_rates_by_date(table, today_date_iso)
    previous_rates = get_rates_by_date(table, yesterday_iso)

    response = {
        "present_rates": present_rates,
        "delta": {currency: present_rates[currency] - previous_rates.get(currency, 0) for currency in present_rates},
    }

    return {"statusCode": 200, "body": json.dumps(response)}


def get_rates_by_date(table, date: str) -> Dict[str, float]:
    """
    Retrieves exchange rates for a specific date from a DynamoDB table.

    Args:
        table (boto3.DynamoDB.Table): DynamoDB table resource representing the table where exchange rates are stored.
        date (str): The date in ISO format (YYYY-MM-DD) for which exchange rates are retrieved.

    Returns:
        dict: A dictionary where keys are currency codes (str) and values are related exchange rates (float).
    """
    return {item["Currency"]: float(item["Rate"]) for item in
            table.query(IndexName="TSIndex", KeyConditionExpression=Key("Timestamp").eq(date))["Items"]}
