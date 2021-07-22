# ERIS API

## About
Package to wrap the ERIS API.

Intended use is to simplify requesting data from ERIS.

To proceed the user must be added to the API group and you must also know the client ID of the group.

# Install

```
pip install ERIS-API
```

# Usage

Basic flow is as follows. Example is also below:

1. Create ERISAPI Class with following parameters
    1. URL to ERIS. Include the trailing slash "https://www.eris.com/"
    1. Client ID
    1. Username
    1. Password or Token

you may choose to omit the username/password/token if they are set in your environment variables as eris_username/etc.
    
2. Build Tag list
    1. Each tag should be an instance of the `ERISTag` class

3. Build Request Class
    1. provide the start time, end time and either the single tag, or a list of tags

4. call `request_api_data` method with request class
    1. the response will be an `ERISResponse` class.

## Authorization

To authorize the request you need to supply a `username` and one of `password` or `token`, in addition to the `client_id`.

If both a password and a token are supplied, it will default to the password.

### Example
```
from ERIS_API import ERISAPI, ERISTag, ERISRequest
import datetime

start_time = datetime.datetime(2021,1,1)
end_time = datetime.datetime(2021,2,1)

input_tags = [
    ERISTag(label="sample label", tag="sampletag", mode="average", interval="P1D"),
    ERISTag(label="sample label 2", tag="sampletag", mode="average", label="P2M"),
]

request_class = ERISRequest(
    start_time=start_time,
    end_time=end_time,
    tags=input_tags
)

#password version
api = ERISAPI(base_url="https://www.eris.com/", client_id="CLIENT_ID", username="USERNAME", password="PASSWORD")

#token version
api = ERISAPI(base_url="https://www.eris.com/", client_id="CLIENT_ID", username="USERNAME", token="TOKEN")

result = api.request_api_data(request_class)
```

## Working with the response

Once you have a valid response, the response class can be used to parse the data into either a json string or a pandas dataframe.

Additionally, the response class will also contain additional information such as eng. units, tagUID, description, etc. Look at the ERIS_Response.py class for details.

Within the response object there is the following properties:

1. tag_data
    * this is the processed tag, which contains additional information. Type is a dictionary.
2. tag_dataframes
    * This is the collection of tags converted to dataframes. 
    * Columns are `Timestamp,Tag,Value`
3. response_class
    * raw response class from request
    * this contains the original response content

Finally, the response will attempt to process the `Timestamp` to a python datetime friendly format, rounding to the nearest second. It will also try and parse the `Value` to a numeric value.
If this fails it will remain as exported.

This can be ignored by setting parse_datetime or parse_values to False in the `convert_tags_to_dataframes` function.

### Example

```
# continuing from above.
result = api.request_api_data(request_class)

# for one tag - change index to particular tag
tag_df = result.tag_to_dataframe(result.tag_data[0])

# can also specify which dictionary key to use (see the Response class) or a custom label. Will use custom label if both are given.
tag_df = result.tag_to_dataframe(result.tag_data[0], custom_label="Custom Tag")

# for all tags - concat argument will return either a single dataframe if True, or a list of individual tag dataframes if False

# combined
tag_df = result.convert_tags_to_dataframes(True)

# individual
tag_dfs = result.convert_tags_to_dataframes(False) 
```

## Generic Request

To optionally pass a generic url to an eris endpoint use the `ERISAPI.request_data` function.

The function accepts a url and a dictionary of parameters. This is a generic wrapper around the `requests.get` function which takes care of the authentication step.

```
api = ERISAPI(url, username, password, client_id)
api.request_data("/tag/list", parameters={})
```

## Next Steps

You, the user, can decide how to work with the output data from here. Either saving the dataframe(s) to excel, csv, or loading it into an SQL database.

## Query Improvements

To improve query performance, your script should adjust the start date to the start/end times after any existing data to avoid re-requesting the same block.

# Additional Functions

## Extract Tag from  URL

If you have the URL of the tag, you can extract the components of the query via the method `extract_tags_from_url`

Calling this method will return a JSON String of the contents of the dictionary.

```
from ERIS_API import extract_tags_from_url

input_url = "https://eris.com/api/rest/tag/data?start=2021-03-29T00:00:00&end=P1M3D&tags=sample_label:sample.tag:first:PT2M"

extract_tags_from_url(input_url)

# RESULT
{
    "start": [
        "2021-03-29T00:00:00"
    ],
    "end": [
        "P1M3D"
    ],
    "tags": [
        {
            "label": "sample_label",
            "tag": "sample.tag",
            "mode": "first",
            "interval": "PT2M"
        }
    ]
}
```

## JSON to Tag

Method to convert a .json file of your tag list to a list of ERISTags

Input is either 
* `json_dict`: pre-loaded dictionary of your tags
* `json_file`: file path to a json dictionary in the structure below

### JSON Structure
```
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
```

### Usage
```
from ERIS_API import json_to_tags

json_dict = [
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
json_path = "eris_tags.json"

tags = json_to_tags(json_dict=json_dict)
tags = json_to_tags(json_path=json_path)
```