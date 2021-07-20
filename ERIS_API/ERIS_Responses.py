
import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import json
import logging

from typing import Optional, List, Dict, Union, Mapping, Any

import requests
import xmltodict

from ERIS_API import models


class _BaseResponse(object):
    def __init__(self, requests_class) -> None:
        super().__init__()
        self.tag_data = None
        self.request = requests_class

    def _match_tags(self, request_parameters):
        eris_tags = request_parameters.tags
        for tag in self.tag_data:
            tag.eris_tag = self._match_tag(eris_tags, tag)
    
    def _match_tag(self, eris_tags, tag):
        for e_tag in eris_tags:
            if tag.tagUID==e_tag.request_uuid: 
                return e_tag
        return None

class XMLResponse(_BaseResponse):
    """XML Response object from an eris query.

    Flow is intiate response, process the response.

    Processed response can either be exported to a dataframe(s) or kept as the dictionary

    Args:
        object ([type]): [description]
    """
    def __init__(self, requests_class, request_parameters) -> None:
        """Init the class with the provided response content.

        Args:
            response_content ([type]): [description]
        """
        super().__init__(requests_class)
        self.tag_data = None
        self.response_content = requests_class.text
        self.request_parameters = request_parameters

    def process_data(self) -> None:
        self._process_response()
        self._match_tags(self.request_parameters)

        return self.tag_data

    def _process_response(self) -> List[models.ERISData]:
        tag_tree = xmltodict.parse(self.response_content, attr_prefix="")
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

        tag_model = models.RawERISResponse(**tag_tree)

        self.raw_model = tag_model
        self.tag_data = [models.ERISData(**tag.dict()) for tag in tag_model.tags]
        return self.tag_data

class JSONResponse(_BaseResponse):
    def __init__(self, requests_class: requests.Response, request_parameters) -> None:
        """Init the class with the provided response content.

        Args:
            response_content ([type]): [description]
        """
        super().__init__(requests_class)
        self.tag_data = None
        self.response_content = requests_class.json()
        self.request_parameters = request_parameters

    def process_data(self) -> None:
        self._process_response()
        self._match_tags(self.request_parameters)

        return self.tag_data

    def _process_response(self) -> List[models.ERISData]:
        tag_model = models.RawERISResponse(**self.response_content)
        if len(tag_model.tags) == 0:
            logging.warning("No data in eris tag response")
            return
        
        self.raw_model = tag_model
        self.tag_data = [models.ERISData(**tag.dict()) for tag in tag_model.tags]

        return self.tag_data

class ERISResponse(object):
    def __init__(self, type_response_class: Union[JSONResponse, XMLResponse]) -> None:
        super().__init__()
        self.tag_data = type_response_class.tag_data
        self.response_class = type_response_class
        self.response_content = self.response_class.response_content
        self.tag_dataframes = []

    def to_json(self, indent=None) -> str:
        indent = 4 if indent is None else indent
        return json.dumps(self.tag_data, indent=indent)

    def convert_tags_to_dataframes(self, concat=None, parse_datetime=None, parse_values=None) -> pd.DataFrame:
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

    def _parse_timestamp(self, df) -> pd.DataFrame:
        """Attempt to parse the Timestamp field to a pandas timestamp object

        Args:
            df (pandas.DataFrame): dataframe of the tag to parse

        Returns:
            pandas.DataFrame: data frame of parsed format, or original if error
        """
        try:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'],format="%Y-%m-%dT%H:%M:%S")
            df['Timestamp'] = df['Timestamp'].dt.round("S")
            return df
        except Exception as e:
            logging.warning(f"Error parsing timestamp. Field left as is. {e}")
        
    def _parse_values(self, df) -> pd.DataFrame:
        """Attempt to parse the Value field to a pandas numeric type

        Args:
            df (pandas.DataFrame): dataframe of the tag to parse

        Returns:
            pandas.DataFrame: data frame of parsed format, or original if error
        """
        try:
            df['Value'] = pd.to_numeric(df['Value'])
            return df
        except Exception as e:
            logging.warning(f"Error parsing Value. Field left as is. {e}")
