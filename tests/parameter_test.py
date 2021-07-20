from unittest import mock
from ERIS_API import ERIS_API
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID
from ERIS_API.ERIS_Parameters import ERISRequest, ERISTag

class TestERISTag(unittest.TestCase):
    _norm_uuid = MagicMock(return_value=UUID('f2a8f445-45f9-4608-a9a3-5c1fa9fcbe7b'))

    def _get_actual_uuid(self):
        return str(self._norm_uuid.return_value).replace("-","")

    @patch('ERIS_API.ERIS_Parameters.uuid4', new=_norm_uuid)
    def test_uuid(self):
        _actual = self._get_actual_uuid()
        _tag = ERIS_API.ERISTag("lbl","tag","mode","interval")
        self.assertEqual(_tag.request_uuid, _actual)

    @patch('ERIS_API.ERIS_Parameters.uuid4', new=_norm_uuid)
    def test_valid_params_all(self):       
        _actual_uuid = self._get_actual_uuid()
        _actual_label = 'lbl'
        _actual_tag = 'tag'
        _actual_mode = 'mode'
        _actual_interval = 'interval'

        _tag = ERIS_API.ERISTag("lbl","tag","mode","interval")
        self.assertEqual(_tag.label, _actual_label)
        self.assertEqual(_tag.tag, _actual_tag)
        self.assertEqual(_tag.mode, _actual_mode)
        self.assertEqual(_tag.interval, _actual_interval)
        self.assertEqual(_tag.request_uuid, _actual_uuid)

    @patch('ERIS_API.ERIS_Parameters.uuid4', new=_norm_uuid)
    def test_valid_params_no_label(self):       
        _actual_uuid = self._get_actual_uuid()
        _actual_tag = 'tag'
        _actual_mode = 'mode'
        _actual_interval = 'interval'

        _tag = ERISTag(tag="tag",mode="mode",interval="interval")
        self.assertEqual(_tag.label, None)
        self.assertEqual(_tag.tag, _actual_tag)
        self.assertEqual(_tag.mode, _actual_mode)
        self.assertEqual(_tag.interval, _actual_interval)
        self.assertEqual(_tag.request_uuid, _actual_uuid)
    
    def test_missing_one_valid_param(self):       
        _actual_tag = 'tag'
        _actual_mode = 'mode'
        _actual_interval = 'interval'
        with self.assertRaises(AssertionError) as ae:
            _tag = ERIS_API.ERISTag()
        self.assertEqual(str(ae.exception), 'Must supply a tag, mode and interval')

    def test_missing_valid_params(self):       
        _actual_tag = 'tag'
        _actual_mode = 'mode'
        _actual_interval = 'interval'

        with self.assertRaises(AssertionError) as ae:
            _tag = ERIS_API.ERISTag(tag="a", mode="m")
        self.assertEqual(str(ae.exception), 'Must supply a tag, mode and interval')

    @patch('ERIS_API.ERIS_Parameters.uuid4', new=_norm_uuid)
    def test_tag_to_string(self):
        _actual = self._get_actual_uuid()
        _valid = f"{_actual}:tag:mode:interval"
        _tag = ERIS_API.ERISTag("lbl","tag","mode","interval")
        _result = _tag.tag_to_string()
        self.assertEqual(_valid, _result)

    def test_str_method_label(self):
        _valid = "Label: lbl\nTag: tag\nMode: mode\nInterval: interval"
        _tag = ERIS_API.ERISTag("lbl","tag","mode","interval")
        self.assertEqual(str(_tag), _valid)

    def test_str_method_no_label(self):
        _valid = "Tag: tag\nMode: mode\nInterval: interval"
        _tag = ERIS_API.ERISTag(tag="tag",mode="mode",interval="interval")
        self.assertEqual(str(_tag), _valid)

    def test_iter_method(self):
        _valid = [('label', 'lbl'), ('tag','tag'), ('mode','mode'), ('interval','interval')]
        _tag = ERIS_API.ERISTag(label='lbl', tag="tag",mode="mode",interval="interval")
        self.assertEqual(_valid, [_ for _ in _tag])

    def test_iter_method_to_dict(self):
        _valid = {'label': 'lbl', 'tag':'tag', 'mode': 'mode', 'interval':'interval'}
        _tag = ERIS_API.ERISTag(label='lbl', tag="tag",mode="mode",interval="interval")
        self.assertEqual(_valid, dict(_tag))


class TestERISRequest(unittest.TestCase):
    def create_eris_tag(self):
        return ERIS_API.ERISTag("lbl", "tag","mode","interval")

    def test_valid_request_single(self):
        _tag = self.create_eris_tag()
        _st = "ST"
        _et = "ET"

        req = ERIS_API.ERISRequest(_st, _et, _tag)

        self.assertEqual(req.start, _st)
        self.assertEqual(req.end, _et)
        self.assertEqual(req.tags, [_tag])
        self.assertEqual(req.regex, None)
        self.assertEqual(req.compact, None)

    def test_valid_request_list(self):
        _tag = [self.create_eris_tag()]*4
        _st = "ST"
        _et = "ET"

        req = ERIS_API.ERISRequest(_st, _et, _tag)

        self.assertEqual(req.start, _st)
        self.assertEqual(req.end, _et)
        self.assertEqual(req.tags, _tag)
        self.assertEqual(req.regex, None)
        self.assertEqual(req.compact, None)

    def test_invalid_request_single(self):
        _tag = "a"
        _st = "ST"
        _et = "ET"
        with self.assertRaises(AssertionError) as ae:
            req = ERIS_API.ERISRequest(_st, _et, _tag)
        self.assertEqual(str(ae.exception), "Must provide only ERISTag classes as a tag")

    def test_invalid_request_list(self):
        _tag = ["a", self.create_eris_tag()]*2
        _st = "ST"
        _et = "ET"
        with self.assertRaises(AssertionError) as ae:
            req = ERIS_API.ERISRequest(_st, _et, _tag)
        self.assertEqual(str(ae.exception), "Must provide only ERISTag classes as a tag")

    def test_valid_regex(self):
        _tag = [self.create_eris_tag()]*2
        _st = "ST"
        _et = "ET"
        req = ERIS_API.ERISRequest(_st, _et, _tag,regex=True)
        self.assertEqual(True, req.regex)

    def test_valid_compact(self):
        _tag = [self.create_eris_tag()]*2
        _st = "ST"
        _et = "ET"
        req = ERIS_API.ERISRequest(_st, _et, _tag,compact=True)
        self.assertEqual(True, req.compact)

    def test_invalid_regex(self):
        _tag = [self.create_eris_tag()]*2
        _st = "ST"
        _et = "ET"
        req = ERIS_API.ERISRequest(_st, _et, _tag,regex="a")
        self.assertEqual(None, req.regex)

    def test_invalid_compact(self):
        _tag = [self.create_eris_tag()]*2
        _st = "ST"
        _et = "ET"
        req = ERIS_API.ERISRequest(_st, _et, _tag,compact="a")
        self.assertEqual(None, req.compact)

if __name__ == "__main__":
    unittest.main()