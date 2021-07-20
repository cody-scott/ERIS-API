# tests for the responses
from datetime import date, datetime
from types import new_class
from unittest import mock
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

from ERIS_API.ERIS_Parameters import ERISRequest, ERISTag
from ERIS_API import ERIS_Responses

import requests
from pathlib import Path
import json

from ERIS_API import models

import pandas as pd

class TestResponse(unittest.TestCase):
    mock_uids = MagicMock(side_effect=["uid1", "uid2"], spec=UUID)
    json_fixture_path = Path("./tests/fixtures/json_response.json")
    json_error_fixture_path = Path("./tests/fixtures/json_response_error_one_tag.json")
    json_no_data_fixture_path = Path("./tests/fixtures/json_response_no_data.json")
    xml_two_tags = Path('./tests/fixtures/xml_two_tag.xml')
    xml_one_tags = Path('./tests/fixtures/xml_one_tag.xml')
    xml_one_tags_one_data = Path('./tests/fixtures/xml_one_tag_one_data.xml')
    xml_two_tags_one_day = Path('./tests/fixtures/xml_two_tags_one_day.xml')
    xml_two_tags_one_error = Path('./tests/fixtures/xml_two_tags_one_error.xml')

    def setUp(self) -> None:
        self.mock_uids = MagicMock(side_effect=["uid1", "uid2"], spec=UUID)
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def load_json(self, _path):
        with open(_path) as fl:
            return json.loads(fl.read())

    def load_xml(self, _path):
        with open(_path) as fl:
            return fl.read()

    def request_response(self, data):
        mk = MagicMock(spec=requests.Response)
        mk.json.return_value = data
        return mk

    def request_response_xml(self, data):
        mk = MagicMock(spec=requests.Response)
        mk.text = data
        return mk

    def create_uuid(self):
        for _ in ['uid1', 'uid2']:
            yield MagicMock(return_value=_)

    @patch('ERIS_API.ERIS_Parameters.uuid4')
    def create_valid_params(self, mk):
        # mk.return_value
        mk.side_effect = ['uid1', 'uid2']
        tags = [
            ERISTag(label="lbl1", tag="tag1", mode="m", interval='i'),
            ERISTag(label="lbl2", tag="tag2", mode="m", interval='i')
        ]
        return tags

    def create_valid_request(self, tags):
        return ERISRequest(
            start_time=datetime(2021,1,1),
            end_time=datetime(2021,1,7),
            tags=tags
        )

    def setup_ERIS_Response(self, fixture_data):
        mock_response = self.request_response(fixture_data)
        tags = self.create_valid_params()
        eris_r = self.create_valid_request(tags)
        res_class = ERIS_Responses.JSONResponse(mock_response, eris_r)
        return res_class

    def setup_ERIS_Response_XML(self, fixture_xml):
        mock_response = self.request_response_xml(fixture_xml)
        tags = self.create_valid_params()
        eris_r = self.create_valid_request(tags)
        res_class = ERIS_Responses.XMLResponse(mock_response, eris_r)
        return res_class

    def test_valid_json_response(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_fixture_path))
        res = er_class._process_response()
        r0 = res[0]
        r1 = res[1]

        self.assertEqual(len(res), 2)

        self.assertEqual(len(r0.data), 6)
        self.assertEqual(len(r1.data), 6)

        self.assertEqual(r0.data[0].timestamp, datetime(2021,1,1,0,0))
        self.assertEqual(r0.data[0].value, 1718.0)
        self.assertEqual(r0.data[0].tag, '')

        self.assertEqual(r1.data[1].timestamp, datetime(2021,1,2,0,0))
        self.assertEqual(r1.data[1].value, 6.0)
        self.assertEqual(r1.data[1].tag, '')

    def test_valid_json_response_one_tag_error(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_error_fixture_path))
        res = er_class._process_response()
        self.assertEqual(len(res), 2)
        
        self.assertEqual(len(res[0].data), 6)
        self.assertEqual(len(res[1].data), 0)

        self.assertEqual(res[0].data[0].timestamp, datetime(2021,1,1,0,0))
        self.assertEqual(res[0].data[0].value, 1718.0)
        self.assertEqual(res[0].data[0].tag, '')

    def test_valid_xml_response(self):
        er_class = self.setup_ERIS_Response_XML(self.load_xml(self.xml_two_tags))
        res = er_class._process_response()
        r0 = res[0]
        r1 = res[1]

        self.assertEqual(len(res), 2)

        self.assertEqual(len(r0.data), 24)
        self.assertEqual(len(r1.data), 1)

        self.assertEqual(r0.data[0].timestamp, datetime(2021,7,19,0,0))
        self.assertEqual(r0.data[0].value, 2281768)
        self.assertEqual(r0.data[0].tag, 'tag1')

        self.assertEqual(r1.data[0].timestamp, datetime(2021,7,19,0,0))
        self.assertEqual(r1.data[0].value, 586.881)
        self.assertEqual(r1.data[0].tag, 'tag2')

    def test_valid_xml_response_one_tag(self):
        er_class = self.setup_ERIS_Response_XML(self.load_xml(self.xml_one_tags))
        res = er_class._process_response()
        self.assertEqual(len(res), 1)
        
        self.assertEqual(len(res[0].data), 144)

        self.assertEqual(res[0].data[0].timestamp, datetime(2021,7,1,0,0))
        self.assertEqual(res[0].data[0].value, 2255520.0)
        self.assertEqual(res[0].data[0].tag, 'tag1')

    def test_valid_xml_response_one_tag_error(self):
        er_class = self.setup_ERIS_Response_XML(self.load_xml(self.xml_two_tags_one_error))
        res = er_class._process_response()
        self.assertEqual(len(res), 1)
        
        self.assertEqual(len(res[0].data), 1)

        self.assertEqual(res[0].data[0].timestamp, datetime(2021,7,1,0,0))
        self.assertEqual(res[0].data[0].value, 1861.0)
        self.assertEqual(res[0].data[0].tag, 'tag1')


    def test_valid_xml_response_two_tags_one_day(self):
        er_class = self.setup_ERIS_Response_XML(self.load_xml(self.xml_two_tags_one_day))
        res = er_class._process_response()
        self.assertEqual(len(res), 2)
        
        self.assertEqual(len(res[0].data), 1)

        self.assertEqual(res[0].data[0].timestamp, datetime(2021,7,1,0,0))
        self.assertEqual(res[0].data[0].value, 1861.0)
        self.assertEqual(res[0].data[0].tag, 'tag1')

        self.assertEqual(res[1].data[0].timestamp, datetime(2021,7,1,0,0))
        self.assertEqual(res[1].data[0].value, 558.0703)
        self.assertEqual(res[1].data[0].tag, 'tag2')

    def test_json_match_tags(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_fixture_path))
        res = er_class.process_data()
        self.assertEqual(res[0].eris_tag.request_uuid, 'uid1')
        self.assertEqual(res[1].eris_tag.request_uuid, 'uid2')

    def test_xml_match_tags(self):
        er_class = self.setup_ERIS_Response_XML(self.load_xml(self.xml_two_tags))
        res = er_class.process_data()
        self.assertEqual(res[0].eris_tag.request_uuid, 'uid1')
        self.assertEqual(res[1].eris_tag.request_uuid, 'uid2')

    def test_tag_to_dataframe(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_fixture_path))
        res = er_class.process_data()
        er_res = ERIS_Responses.ERISResponse(er_class)
        df = er_res.tag_to_dataframe(er_res.tag_data[0])

        self.assertEqual(df.shape, (6,3))
        self.assertEqual(df.Tag.values[0], 'lbl1')

    def test_all_tags_to_dataframe(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_fixture_path))
        res = er_class.process_data()
        er_res = ERIS_Responses.ERISResponse(er_class)
        df = er_res.convert_tags_to_dataframes()

        self.assertEqual(df.shape, (12,3))
        self.assertEqual(df.Tag.values[0], 'lbl1')
        self.assertEqual(df.Tag.values[-1], 'lbl2')

    def test_tag_to_dataframe_one_error(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_error_fixture_path))
        res = er_class.process_data()
        er_res = ERIS_Responses.ERISResponse(er_class)
        df = er_res.tag_to_dataframe(er_res.tag_data[1])

        self.assertEqual(df, None)

    def test_all_tags_to_dataframe_one_error(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_error_fixture_path))
        res = er_class.process_data()
        er_res = ERIS_Responses.ERISResponse(er_class)
        df = er_res.convert_tags_to_dataframes()

        self.assertEqual(df.shape, (6,3))
        self.assertEqual(df.Tag.values[0], 'lbl1')

    def test_tag_to_dataframe_no_data(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_no_data_fixture_path))
        res = er_class.process_data()
        er_res = ERIS_Responses.ERISResponse(er_class)
        df = er_res.tag_to_dataframe(er_res.tag_data[1])

        self.assertEqual(df, None)

    def test_all_tags_to_dataframe_no_data(self):
        er_class = self.setup_ERIS_Response(self.load_json(self.json_no_data_fixture_path))
        res = er_class.process_data()
        er_res = ERIS_Responses.ERISResponse(er_class)
        df = er_res.convert_tags_to_dataframes()

        self.assertEqual(df, None)


if __name__ == "__main__":
    unittest.main()