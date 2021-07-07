# tests for the responses
from datetime import date, datetime
from types import new_class
from unittest import mock
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

from ERIS_API.ERIS_API import ERISRequest, ERISTag
from ERIS_API import ERIS_Responses

import requests
from pathlib import Path
import json

class TestResponse(unittest.TestCase):
    mock_uids = MagicMock(side_effect=["uid1", "uid2"], spec=UUID)
    json_fixture_path = Path("./tests/fixtures/json_response.json")
    json_error_fixture_path = Path("./tests/fixtures/json_response_error_one_tag.json")
    json_no_data_fixture_path = Path("./tests/fixtures/json_response_no_data.json")

    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def load_fixture(self, _fixture_json):
        data = None
        with open(_fixture_json) as fl:
            data = json.loads(fl.read())
        return data

    def load_valid_fixture(self):
        self.json_data =  self.load_fixture(self.json_fixture_path)

    def load_no_data_fixture(self):
        self.json_data = self.load_fixture(self.json_no_data_fixture_path)

    def load_error_fixture(self):
        self.json_data =  self.load_fixture(self.json_error_fixture_path)

    def request_response(self):
        mk = MagicMock(spec=requests.Response)
        mk.json.return_value = self.json_data
        return mk

    def create_uuid(self):
        mk = MagicMock()
        mk.side_effect(['uid1', 'uid2'])
        return mk

    @patch('uuid.UUID', new=mock_uids)
    def create_valid_params(self):
        tags = [
            ERISTag(label="lbl", tag="tag1", mode="m", interval='i'),
            ERISTag(label="lbl", tag="tag2", mode="m", interval='i')
        ]
        return tags

    def create_valid_request(self, tags):
        return ERISRequest(
            start_time=datetime(2021,1,1),
            end_time=datetime(2021,1,7),
            tags=tags
        )

    def test_fixture(self):
        self.load_error_fixture()
        mock_response = self.request_response()
        tags = self.create_valid_params()
        eris_r = self.create_valid_request(tags)
        res_class = ERIS_Responses.JSONResponse(mock_response, eris_r)

        pass

if __name__ == "__main__":
    unittest.main()