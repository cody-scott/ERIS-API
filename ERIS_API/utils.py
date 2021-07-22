from ERIS_API.ERIS_Parameters import ERISRequest
from ERIS_API.ERIS_Responses import ERISResponse
from urllib.parse import urlparse, unquote, parse_qs
from .ERIS_API import ERISTag

from typing import Dict, Optional
from pathlib import Path

import json


def extract_tags_from_url(url):
    """Return the components of the requested url. This is normally obtained via the Source link at the bottom of a request.

    Returns the start/end times, but those are for reference. Main intent is to extract the requested tag from the url"""
    parsed_url = urlparse(url)
    query = unquote(parsed_url.query)
    qs_content = parse_qs(query)

    st = qs_content.get("start")
    et = qs_content.get("end")

    tags = qs_content.get("tags")
    tags = tags[0].split(",")

    tag_classes = [_parse_tag(_.split(":")) for _ in tags]


    result = {
            "start": st,
            "end": et,
            "tags": [dict(_) for _ in tag_classes]
        }

    return result


def _parse_tag(_tag):
    if len(_tag) == 3:
        return ERISTag(None, *_tag)
    else:
        return ERISTag(*_tag)


def json_to_tags(json_dict=None, json_path=None):
    """Helper to convert a json file or feature to ERISTags.

    Structure is expected as 
    [
        {
            "label": "lbl_value",
            "tag": "tag_value",
            "mode": "raw",
            "interval": "P1D"
        },
        {
            "label": "lbl_value2",
            "tag": "tag_value2",
            "mode": "raw",
            "interval": "P1D"
        }
    ]

    Args:
        json_dict (dict, optional): already parsed json file in a dictionary. Defaults to None.
        json_path (string, optional): path to the file. Defaults to None.

    Returns:
        [type]: [description]
    """
    if json_path is not None:
        _json_data = _load_json(json_path)
    elif json_dict is not None:
        _json_data = json_dict
    
    assert _json_data is not None, "No JSON data or path provided"

    _tags = []
    for _ in _json_data:
        tag = ERISTag(
            _.get('label'),
            _.get('tag'),
            _.get('mode'),
            _.get('interval')
        )
        _tags.append(tag)
    return _tags


def _load_json(_path):
    _data = None
    with open(_path, 'r') as fl:
        _data = json.loads(fl.read())
    return _data


def export_eris_response(response: ERISResponse, path: Optional[str] = None):
    """Helper to export the response from the ERIS API.
    This will export the stages of the ERISResponse to a series of files for debug.

    These include:
        - The raw response from the API
        - The parsed JSON response
        - The RawERISResponse
        - The ERISData
        - The ERISRequest

    Args:
        response (ERISResponse): response from the ERIS API.
        path (str, optional): path of folder to save the files. Defaults to None.
    """
    path = "" if path is None else path
    path = Path(path)

    _save_file(path/'request_response.txt', response.response_class.text)
    _save_eris_request(path, response.eris_parameters)
    _save_data_dict(path, response.response_dict)
    _save_raw_model(path, response)
    _save_tag_data(path, response)


def _save_data_dict(path: Path, data: Dict):
    _save_json(path/"parsed_data.json", data)


def _save_eris_request(path: Path, eris_request: ERISRequest):
    data = vars(eris_request)
    data['tags'] = [vars(_) for _ in data['tags']]
    _save_json(path/'eris_request.json', data)


def _save_raw_model(path: Path, request):
    _save_json(path/'raw_model.json', request.raw_model.dict())


def _save_tag_data(path: Path, request: ERISResponse):
    _save_json(path/"tag_data.json", [_.dict() for _ in request.tag_data])


def _save_json(path: Path, data: Dict):
    data = json.dumps(data, indent=4, default=str)
    _save_file(path, data)


def _save_file(_path, _data):
    with open(_path, 'w') as fl:
        fl.write(_data)
