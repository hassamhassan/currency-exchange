# -*- coding: utf-8 -*-
import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, call

import boto3
import requests_mock

from src.get_rates_from_url import (
    get_exchange_rates,
    parse_xml_exchange_rates,
)


class TestGetExchangeRates(unittest.TestCase):

    def setUp(self):
        """
        Sets up required resources.
        """
        self.mock_dynamodb_table = MagicMock()
        boto3.resource = MagicMock(
            return_value=MagicMock(Table=lambda table_name: self.mock_dynamodb_table)
        )

    def test_fetch_exchange_rates_successful(self):
        """
        Test for successful scenario of getting and storing of exchange rates in DB.
        """
        mock_response_content = """<?xml version="1.0" encoding="UTF-8"?>
        <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
            <gesmes:subject>Reference rates</gesmes:subject>
            <gesmes:Sender>
                <gesmes:name>European Central Bank</gesmes:name>
            </gesmes:Sender>
            <Cube>
                <Cube time="2024-07-17">
                    <Cube currency="USD" rate="1.0934"/>
                    <Cube currency="JPY" rate="171.21"/>
                    <Cube currency="BGN" rate="1.9558"/>
                    <!-- More currencies here -->
                </Cube>
            </Cube>
        </gesmes:Envelope>"""
        with requests_mock.Mocker() as mock_requests:
            mock_requests.get(
                "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
                text=mock_response_content,
            )

            event = {}
            context = {}
            response = get_exchange_rates(event, context)
            self.assertEqual(response["statusCode"], 200)
            self.assertEqual(
                json.loads(response["body"]),
                "Exchange rates obtained and stored successfully.",
            )

            # Verify DynamoDB interactions
            self.mock_dynamodb_table.batch_writer.assert_called_once()
            batch_writer_context = (
                self.mock_dynamodb_table.batch_writer.return_value.__enter__.return_value
            )
            put_item_calls = batch_writer_context.put_item.call_args_list

            expected_calls = [
                call(
                    Item={
                        "Currency": "USD",
                        "Rate": Decimal("1.0934"),
                        "Timestamp": datetime.now(timezone.utc).date().isoformat(),
                    }
                ),
                call(
                    Item={
                        "Currency": "JPY",
                        "Rate": Decimal("171.21"),
                        "Timestamp": datetime.now(timezone.utc).date().isoformat(),
                    }
                ),
                call(
                    Item={
                        "Currency": "BGN",
                        "Rate": Decimal("1.9558"),
                        "Timestamp": datetime.now(timezone.utc).date().isoformat(),
                    }
                ),
            ]

            self.assertEqual(put_item_calls, expected_calls)

    def test_parse_ecb_data(self):
        """
        Tests parsing of ECB XML data.
        """
        response_content = """<?xml version="1.0" encoding="UTF-8"?>
                <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
                    <gesmes:subject>Reference rates</gesmes:subject>
                    <gesmes:Sender>
                        <gesmes:name>European Central Bank</gesmes:name>
                    </gesmes:Sender>
                    <Cube>
                        <Cube time="2024-07-17">
                            <Cube currency="USD" rate="1.0934"/>
                            <Cube currency="JPY" rate="171.21"/>
                            <Cube currency="BGN" rate="1.9558"/>
                            <!-- More currencies here -->
                        </Cube>
                    </Cube>
                </gesmes:Envelope>"""
        expected_rates = {"USD": 1.0934, "JPY": 171.21, "BGN": 1.9558}
        rates = parse_xml_exchange_rates(response_content)
        self.assertEqual(rates, expected_rates)
