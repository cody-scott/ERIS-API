import pandas as pd
import xml.etree.ElementTree as ET
import json

class ERIS_Response(object):
    def __init__(self, type_response_class) -> None:
        super().__init__()
        self.tag_data = type_response_class.tag_data
        self.response_content = type_response_class.response_content
        self.tag_dataframes = []

    def to_json(self, indent=None):
        indent = 4 if indent is None else indent
        assert self.tag_data is not None, "Run processes response before trying to export to json"
        return json.dumps(self.tag_data, indent=indent)

    def convert_tags_to_dataframes(self, concat=None):
        """Convert all internal tag data to individual data frames using 'description'

        If concat is True, then it will concatenate it to a single dataframe as the return.
        Default is to concatenate the dataframes.
        """
        concat = True if concat is None else concat
        for tag in self.tag_data:
            self.tag_to_dataframe(tag)
        result = pd.concat(self.tag_dataframes) if concat == True else self.tag_dataframes
        return result

    def tag_to_dataframe(self, tag, tag_label=None, custom_label=None) -> pd.Series:
        """Convert a tag to a pandas data frame of the format 
        Can either pull from one of the tag keys or use a custom label

        if both are blank then it will default to 'description'

        Timestamp, Tag Label, Value
        Args:
            tag (dictionary of tag): dictionary of the tag returned from _process_tree
            tag_label (string): One of the dictionary keys to use as a label. Default is 'description'
            custom_label (string): Label of own choosing
        """
        tag_label = 'description' if tag_label is None else tag_label
        label_name = tag.get(tag_label) if custom_label is None else custom_label
        df = pd.DataFrame(tag['data'], columns=["Timestamp", "Tag Label", "Value"])
        df["Tag Label"] = label_name
        self.tag_dataframes.append(df)
        return df


class XML_Response(object):
    """XML Response object from an eris query.

    Flow is intiate response, process the response.

    Processed response can either be exported to a dataframe(s) or kept as the dictionary

    Args:
        object ([type]): [description]
    """
    def __init__(self, response_content) -> None:
        """Init the class with the provided response content.

        Args:
            response_content ([type]): [description]
        """
        super().__init__()
        self.response_content = response_content
        self.tag_data = None
        self._process_response()
        
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
        info_dict = {
            'tagUID': None,
            'name': None,
            'description': None,
            'engUnits': None,
            'sampleInterval': None,
            'samplingMode': None,
            'data': []
        }
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

class JSON_Response(object):
    """Waiting for valid response to complete this.
    Likely will share many similarities, hence the _Generic_Response usage
    """
    pass
