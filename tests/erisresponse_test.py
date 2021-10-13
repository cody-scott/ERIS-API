import unittest
from unittest.mock import MagicMock, patch

from ERIS_API.ERIS_Parameters import ERISRequest, ERISTag
from ERIS_API import utils
from ERIS_API import ERIS_Responses

from datetime import datetime

import requests
from pathlib import Path
import json

from uuid import UUID

from pathlib import Path

import logging

class ERISResponse(unittest.TestCase):
    json_fixture_path = Path("./tests/fixtures/json_response.json")
    json_error_fixture_path = Path("./tests/fixtures/json_response_error_one_tag.json")
    json_no_data_fixture_path = Path("./tests/fixtures/json_response_no_data.json")
    json_blank_value = Path("./tests/fixtures/json_response blank value.json")
    xml_two_tags = Path('./tests/fixtures/xml_two_tag.xml')
    xml_one_tags = Path('./tests/fixtures/xml_one_tag.xml')
    xml_one_tags_one_data = Path('./tests/fixtures/xml_one_tag_one_data.xml')
    xml_two_tags_one_day = Path('./tests/fixtures/xml_two_tags_one_day.xml')
    xml_two_tags_one_error = Path('./tests/fixtures/xml_two_tags_one_error.xml')

    def setUp(self) -> None:
        self.mock_uids = MagicMock(side_effect=["uid1", "uid2"], spec=UUID)
        logging.disable(logging.CRITICAL)
        return super().setUp()

    def load_json(self, _path):
        with open(_path) as fl:
            return json.loads(fl.read())

    def load_xml(self, _path):
        with open(_path) as fl:
            return fl.read()

    def request_response_json(self, data):
        mk = MagicMock(spec=requests.Response)
        mk.json.return_value = data
        return mk

    def request_response_xml(self, data):
        mk = MagicMock(spec=requests.Response)
        mk.text = data
        return mk

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

    def setup_ERIS_Response(self, fixture_data, is_xml):
        fixture_data = self.load_json(fixture_data) if not is_xml else self.load_xml(fixture_data)
        mock_response = self.request_response_json(fixture_data) if not is_xml else self.request_response_xml(fixture_data)
        
        tags = self.create_valid_params()
        eris_r = self.create_valid_request(tags)

        return ERIS_Responses.ERISResponse(mock_response, eris_r, is_xml)

    def test_json_match_tags(self):
        er_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        res = er_class.process_results()
        self.assertEqual(res[0].eris_tag.request_uuid, 'uid1')
        self.assertEqual(res[1].eris_tag.request_uuid, 'uid2')

    def test_xml_match_tags(self):
        er_class = self.setup_ERIS_Response(self.xml_two_tags, True)
        res = er_class.process_results()
        self.assertEqual(res[0].eris_tag.request_uuid, 'uid1')
        self.assertEqual(res[1].eris_tag.request_uuid, 'uid2')

    def test_xml_process(self):
        data_class = self.setup_ERIS_Response(self.xml_two_tags_one_day, True)
        res = data_class.process_results()

        self.assertEqual(len(res), 2)
        
        self.assertEqual(len(res[0].data), 1)

        self.assertEqual(res[0].data[0].timestamp, datetime(2021,7,1,0,0))
        self.assertEqual(res[0].data[0].value, 1861.0)
        self.assertEqual(res[0].data[0].tag, 'tag1')

        self.assertEqual(res[1].data[0].timestamp, datetime(2021,7,1,0,0))
        self.assertEqual(res[1].data[0].value, 558.0703)
        self.assertEqual(res[1].data[0].tag, 'tag2')

    def test_json_process(self):
        data_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        res = data_class.process_results()

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

    def test_json_response(self):
        data_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        res =  data_class._parse_json(data_class.response_class.json())

        self.assertEqual(isinstance(res, dict), True)
        self.assertEqual(len(res['tag']), 2)

    def test_json_response_missing_value(self):
        """this tests to see that a missing value of blank is returned as None"""
        data_class = self.setup_ERIS_Response(self.json_blank_value, False)
        res =  data_class.process_results()
        self.assertIsNone(res[0].data[0].value)
        

    def test_xml_response(self):
        data_class = self.setup_ERIS_Response(self.xml_two_tags, True)
        res =  data_class._parse_xml(data_class.response_class.text)

        self.assertEqual(isinstance(res, dict), True)
        self.assertEqual(len(res['tag']), 2)

    def test_xml_response_one_error(self):
        data_class = self.setup_ERIS_Response(self.xml_two_tags_one_error, True)
        res =  data_class._parse_xml(data_class.response_class.text)

        self.assertEqual(isinstance(res, dict), True)
        self.assertEqual(len(res['tag']), 1)

    def test_tag_to_dataframe(self):
        er_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        er_res = er_class.process_results()
        df = er_class.tag_to_dataframe(er_class.tag_data[0])

        self.assertEqual(df.shape, (6,3))
        self.assertEqual(df.Tag.values[0], 'lbl1')

    def test_all_tags_to_dataframe(self):
        er_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        er_res = er_class.process_results()
        df = er_class.convert_tags_to_dataframes()

        self.assertEqual(df.shape, (12,3))
        self.assertEqual(df.Tag.values[0], 'lbl1')
        self.assertEqual(df.Tag.values[-1], 'lbl2')

    def test_tag_to_dataframe_one_error(self):
        er_class = self.setup_ERIS_Response(self.json_error_fixture_path, False)
        res = er_class.process_results()
        df = er_class.tag_to_dataframe(er_class.tag_data[1])

        self.assertEqual(df, None)

    def test_all_tags_to_dataframe_one_error(self):
        er_class = self.setup_ERIS_Response(self.json_error_fixture_path, False)
        res = er_class.process_results()
        df = er_class.convert_tags_to_dataframes()

        self.assertEqual(df.shape, (6,3))
        self.assertEqual(df.Tag.values[0], 'lbl1')

    def test_tag_to_dataframe_no_data(self):
        er_class = self.setup_ERIS_Response(self.json_no_data_fixture_path, False)
        res = er_class.process_results()
        df = er_class.tag_to_dataframe(er_class.tag_data[1])

        self.assertEqual(df, None)

    def test_all_tags_to_dataframe_no_data(self):
        er_class = self.setup_ERIS_Response(self.json_no_data_fixture_path, False)
        res = er_class.process_results()
        df = er_class.convert_tags_to_dataframes()

        self.assertEqual(df, None)

    def test_process_raise_error(self):
        er_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        with patch.object(ERIS_Responses.ERISResponse, 'load_model') as mock_method:
            mock_method.side_effect = Exception('Test Error')
            er_class.process_results()
            self.assertEqual(isinstance(er_class.response_dict, dict), True)
            self.assertEqual(er_class.raw_model, None)
            self.assertEqual(er_class.tag_data, None)

    def test_save_eris_request(self):
        er_class = self.setup_ERIS_Response(self.json_fixture_path, False)
        er_res = er_class.process_results()

        with patch.object(utils, '_save_file') as mock_method:
            utils.export_eris_response(er_class)
            self.assertEqual(mock_method.call_count, 5)
