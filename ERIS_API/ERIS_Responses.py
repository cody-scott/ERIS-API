
import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import json
import logging

from typing import Optional, List, Dict, Union, Mapping, Any

from pydantic import ValidationError

import requests
from requests.models import requote_uri
import xmltodict

from ERIS_API import ERIS_Parameters, models


class ERISResponse(object):
    def __init__(self, request_response: requests.Response, eris_parameters: ERIS_Parameters.ERISRequest, is_xml: bool) -> None:
        super().__init__()

        self.response_class = request_response
        self.is_xml = is_xml
        self.eris_parameters = eris_parameters
        
        self.response_dict = None
        self.raw_model = None
        self.tag_data = None
        self.tag_dataframes = []



    def _match_tags(self):
        eris_tags = self.eris_parameters.tags
        for tag in self.tag_data:
            tag.eris_tag = self._match_tag(eris_tags, tag)
    
    def _match_tag(self, eris_tags, tag):
        for e_tag in eris_tags:
            if tag.tagUID==e_tag.request_uuid: 
                return e_tag
        return None

    def process_results(self):
        try:
            data_obj = self.parse_data()
            result_data = self.load_model(data_obj)
            self._match_tags()
            return self.tag_data
        
        except:
            logging.exception("Error processing results. Partial results may be available in class parameters")

    def parse_data(self) -> Dict:
        """this converts the request to the valid json"""
        data_obj = None
        if self.is_xml:
            data_obj = self._parse_xml(self.response_class.text)
        else:
            data_obj = self._parse_json(self.response_class.json())
        self.response_dict = data_obj
        return self.response_dict

    def _parse_json(self, response_content: Dict) -> Dict:
        return response_content

    def _parse_xml(self, response_content: str) -> Dict:
        tag_tree = xmltodict.parse(response_content, attr_prefix="")
        if not 'tagDataset' in tag_tree:
            logging.warning("No tagDataset found in response")
            return
        
        tag_tree = tag_tree['tagDataset']
        if not isinstance(tag_tree['tag'], list):
            tag_tree['tag'] = [tag_tree['tag']]

        tag_data = []
        for i, _ in enumerate(tag_tree['tag']):
            _data = _.get('data')
            if _data is None:
                continue

            if not isinstance(_.get('data'), list):
                _['data'] = [_['data']]
            tag_data.append(_)
        tag_tree['tag'] = tag_data
        return tag_tree

    def load_model(self, data_obj) -> List[models.ERISData]:
        tag_model = models.RawERISResponse(**data_obj)
        self.raw_model = tag_model
        self.tag_data = [models.ERISData(**tag.dict()) for tag in tag_model.tags]
        return self.tag_data

    def convert_tags_to_dataframes(self, concat=None) -> pd.DataFrame:
        """Convert all internal tag data to individual data frames

        If concat is True, then it will concatenate it to a single dataframe as the return.
        Default is to concatenate the dataframes.

        Option to attempt to parse datetime in default format %Y-%m-%dT%H:%M:%S
        Will round to the closest second.
        Will default to True if not specified

        Option to also attempt to convert the value field to a numeric type.
        Will default to True if not specified
        """
        concat = True if concat is None else concat
        for tag in self.tag_data:
            self.tag_to_dataframe(tag)
        if len(self.tag_dataframes) == 0:
            logging.warning("No dataframes in response")
            return

        result = pd.concat(self.tag_dataframes) if concat == True else self.tag_dataframes
        return result

    def _determine_tag_label(self, tag_dict: models.ERISData, tag_label=None, custom_label=None) -> Optional[str]:
        tag_label = 'name' if tag_label is None else tag_label
        eris_tag = tag_dict.eris_tag
        eris_label = eris_tag.label if eris_tag is not None else None

        label_name = None
        if eris_label is not None:
            label_name = eris_label
        elif custom_label is None:
            label_name = tag_dict.dict().get(tag_label)
        else:
            label_name = custom_label

        return label_name

    def tag_to_dataframe(self, tag: models.ERISData, tag_label=None, custom_label=None) -> pd.DataFrame:
        """Convert a tag to a pandas data frame of the format 
        If a label is given in the ERISTag class it will try and match to this in the processing. This is the label to use.
        Otherwise it will either use a custom label if provided or default to the name attribute in the response.

        Option to attempt to parse datetime in default format %Y-%m-%dT%H:%M:%S
        Will round to the closest second.
        Will default to True if not specified

        Option to also attempt to convert the value field to a numeric type.
        Will default to True if not specified

        Timestamp, Tag, Value
        Args:
            tag (dictionary of tag): dictionary of the tag returned from _process_tree
            tag_label (string): One of the dictionary keys to use as a label. Default is 'name'
            custom_label (string): Label of own choosing
        """
        # tag_label = 'tagUID' if tag_label is None else tag_label
        # label_name = tag.get(tag_label) if custom_label is None else custom_label
        label_name = self._determine_tag_label(tag, tag_label, custom_label)

        if len(tag.data) == 0:
            _uid = tag.name
            logging.warning(f"No data for tag {_uid} - {label_name}")
            return

        df = pd.DataFrame([_.dict() for _ in tag.data])
        df.rename(columns={
            'timestamp': 'Timestamp',
            'tag': 'Tag',
            'value': 'Value'
        }, inplace=True)
        df["Tag"] = label_name

        self.tag_dataframes.append(df)
        return df
