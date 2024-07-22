# -*- coding: utf-8 -*-
import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import boto3

from src.get_rates_from_db import (
    get_rates_delta,
    get_rates_by_date,
)


class TestGetRatesFromDB(unittest.TestCase):

    def setUp(self):
        self.mock_dynamodb_table = MagicMock()
        self.mock_dynamodb = MagicMock()
        self.mock_dynamodb.Table = MagicMock(return_value=self.mock_dynamodb_table)
        boto3.resource = MagicMock(return_value=self.mock_dynamodb)

    def test_get_rates_from_db_positive(self):
        mock_todays_rates = {"USD": float("1.6"), "BGN": float("1.9")}
        self.mock_dynamodb_table.query.side_effect = [
            {
                "Items": [
                    {
                        "Currency": "USD",
                        "Rate": Decimal("1.6")
                    },
                    {
                        "Currency": "BGN",
                        "Rate": Decimal("1.9")
                    },
                ]
            },
            {
                "Items": [
                    {
                        "Currency": "USD",
                        "Rate": Decimal("2.6")
                    },
                    {
                        "Currency": "BGN",
                        "Rate": Decimal("3.045")
                    },
                ]
            },
        ]

        response = get_rates_delta({}, {})
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("present_rates", body)
        self.assertIn("delta", body)
        self.assertEqual(body["present_rates"], mock_todays_rates)

    def test_get_rates_by_date(self):
        mock_date = datetime.now(timezone.utc).date().isoformat()
        mock_response = {
            "Items": [
                {
                    "Currency": "USD",
                    "Rate": Decimal("2.6")
                },
                {
                    "Currency": "JPY",
                    "Rate": Decimal("3.045")
                },
            ]
        }

        self.mock_dynamodb_table.query.return_value = mock_response

        rates = get_rates_by_date(self.mock_dynamodb_table, mock_date)

        expected_rates = {"USD": 2.6, "JPY": 3.045}
        self.assertEqual(rates, expected_rates)

    def test_get_rates_by_date_empty(self):
        mock_date = datetime.now(timezone.utc).date().isoformat()
        self.mock_dynamodb_table.query.return_value = {"Items": []}

        rates = get_rates_by_date(self.mock_dynamodb_table, mock_date)
        self.assertEqual(rates, {})

