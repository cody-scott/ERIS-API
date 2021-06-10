from urllib.parse import urlparse, unquote, parse_qs
from .ERIS_API import ERISTag

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


    result = json.dumps(
        {
            "start": st,
            "end": et,
            "tags": [dict(_) for _ in tag_classes]
        },
        indent=4
    )

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
