# ERIS API

## About
Package to wrap the ERIS API.

Intended use is to simplify requesting data from ERIS.

To proceed the user must be added to the API group and you must also know the client ID of the group.

# Usage

Basic flow is as follows. Example is also below:

1. Create ERISAPI Class with following parameters
    1. URL to ERIS. Include the trailing slash "https://www.eris.com/"
    1. Username
    1. Password
    1. Client ID

2. Build Tag list
    1. Each tag should be an instance of the ERIS_Tag class

3. Build Request Class
    1. provide the start time, end time and either the single tag, or a list of tags

4. call request_api_data method with request class
    1. the response will either be an XML or JSON response class. Functionally they are basically the same thing.


```
from ERIS_API import ERISAPI, ERIS_Tag, ERIS_Request
import datetime

start_time = datetime.datetime(2021,1,1)
end_time = datetime.datetime(2021,2,1)

input_tags = [
    ERIS_Tag(label="sample label", "sampletag", "average", "P1D"),
    ERIS_Tag(label="sample label 2", "sampletag", "average", "P2M"),
]

request_class = ERIS_Request(
    start_time=start_time,
    end_time=end_time,
    tags=input_tags
)

api = ERISAPI("https://www.eris.com/", "USERNAME", "PASSWORD")
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
    * Columns are `Timestamp,Tag Label,Value`



```
# continuing from above.
result = api.request_api_data(request_class)

# for one tag - change index to particular tag
tag_df = result.tag_to_dataframe(result.tag_data[0])

# for all tags - concat argument will return either a single dataframe if True, or a list of individual tag dataframes if False

# combined
tag_df = result.convert_tags_to_dataframes(True)

# individual
tag_dfs = result.convert_tags_to_dataframes(False) 
```

## Next Steps

You, the user, can decide how to work with the output data from here. Either saving the dataframe(s) to excel, csv, or loading it into an SQL database.

## Query Improvements

To improve query performance, your script should adjust the start date to the start/end times after any existing data to avoid re-requesting the same block.

Functionally, this is beyond the scope of the processing.

# Additional Functions

## Extract Tag from  URL

If you have the URL of the tag, you can extract the components of the query via the method `extract_tags_from_url`

Calling this method will return a JSON String of the contents of the dictionary.

```
from ERIS_API import extract_tags_from_url

input_url = "https://eris.com/api/rest/tag/data?start=2021-03-29T00:00:00&end=P1M3D&tags=sample_label:sample.tag:first:PT2M"

extract_tags_from_url(test_url)

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