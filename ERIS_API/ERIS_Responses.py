import pandas as pd
import xml.etree.ElementTree as ET
import json
import logging

class ERISResponse(object):
    def __init__(self, type_response_class) -> None:
        super().__init__()
        self.tag_data = type_response_class.tag_data
        self.response_class = type_response_class
        self.tag_dataframes = []

    def to_json(self, indent=None):
        indent = 4 if indent is None else indent
        return json.dumps(self.tag_data, indent=indent)

    def convert_tags_to_dataframes(self, concat=None, parse_datetime=None, parse_values=None):
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
            self.tag_to_dataframe(tag, 
            parse_datetime=parse_datetime, 
            parse_values=parse_values
        )
        if len(self.tag_dataframes) == 0:
            logging.warning("No dataframes in response")
            return

        result = pd.concat(self.tag_dataframes) if concat == True else self.tag_dataframes
        return result

    def _determine_tag_label(self, tag_dict, tag_label=None, custom_label=None):
        tag_label = 'name' if tag_label is None else tag_label
        eris_tag = tag_dict.get('eris_tag')
        eris_label = eris_tag.label if eris_tag is not None else None

        label_name = None
        if eris_label is not None:
            label_name = eris_label
        elif custom_label is None:
            label_name = tag_dict.get(tag_label)
        else:
            label_name = custom_label

        return label_name

    def tag_to_dataframe(self, tag, tag_label=None, custom_label=None, parse_datetime=None, parse_values=None) -> pd.DataFrame:
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
        parse_datetime = True if parse_datetime is None else parse_datetime
        parse_values = True if parse_values is None else parse_values

        # tag_label = 'tagUID' if tag_label is None else tag_label
        # label_name = tag.get(tag_label) if custom_label is None else custom_label
        label_name = self._determine_tag_label(tag, tag_label, custom_label)

        if len(tag['data']) == 0:
            _uid = tag['name']
            logging.warning(f"No data for tag {_uid} - {label_name}")
            return

        df = pd.DataFrame(tag['data'], columns=["Timestamp", "Tag", "Value"])
        df["Tag"] = label_name
        df = self._parse_timestamp(df) if parse_datetime == True else df
        df = self._parse_values(df) if parse_values == True else df

        self.tag_dataframes.append(df)
        return df

    def _parse_timestamp(self, df):
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
    
    def _parse_values(self, df):
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

class _BaseResponse(object):
    def __init__(self, requests_class) -> None:
        super().__init__()
        self.tag_data = None

        self.base_info_dict = {
            'tagUID': None,
            'name': None,
            'description': None,
            'engUnits': None,
            'sampleInterval': None,
            'samplingMode': None,
            'data': [],
            'provider': None
        }
        self.request = requests_class
        self.tag_data = None

    def _match_tags(self, request_parameters):
        eris_tags = request_parameters.tags
        for tag in self.tag_data:
            tag['eris_tag'] = self._match_tag(eris_tags, tag)
    
    def _match_tag(self, eris_tags, tag):
        for e_tag in eris_tags:
            if tag['tagUID']==e_tag.request_uuid: 
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
        self.response_content = requests_class.text
        self._process_response()
        self._match_tags(request_parameters)

    def _process_response(self):
        eris_tree = ET.fromstring(self.response_content)

        tag_data = []
        tags = []
        for c in eris_tree:
            if not "tag" in c.tag:
                continue
            tags.append(c)
        
        for tag in tags:
            tag_data.append(self._process_tag(tag))

        self.tag_data = tag_data

        return tag_data

    def _process_tag(self, tag_xml):
        info_dict = self.base_info_dict.copy()
        for row in tag_xml:
            _tag = row.tag
            _tag = _tag[_tag.find("}")+1:]

            if _tag not in info_dict: continue

            var = info_dict.get(_tag)
            if _tag == 'data':
                var.append(self._process_data(row))
            else:
                info_dict[_tag] = row.text if var is None else var
        
        return info_dict

    def _process_data(self, data_val):
        attribs = data_val.attrib
        return [attribs['time'], attribs['source'], attribs['value']]

class JSONResponse(_BaseResponse):
    def __init__(self, requests_class, request_parameters) -> None:
        """Init the class with the provided response content.

        Args:
            response_content ([type]): [description]
        """
        super().__init__(requests_class)
        self.response_content = requests_class.json()
        self._process_response()
        self._match_tags(request_parameters)

    def _process_response(self):
        tags = self.response_content.get("tag")
        if tags is None:
            logging.warning("No data in eris tag response")
            return

        tag_data = []
        for tag in tags:
            tag_data.append(self._process_tag(tag))

        self.tag_data = tag_data

        return tag_data

    def _process_tag(self, tag_json):
        info_dict = self.base_info_dict.copy()
        
        for value in tag_json:          
            if value not in info_dict: continue
            var = info_dict.get(value)
            if value == 'data': continue
            info_dict[value] = tag_json.get(value) if var is None else var
        
        info_dict['data'] = self._process_data(tag_json['data'])
        return info_dict

    def _process_data(self, _data):
        output_data = []
        for row in _data:
            output_data.append([row['time'], row['source'], row['value']])
        return output_data
