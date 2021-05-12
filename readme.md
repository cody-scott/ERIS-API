# ERIS API

## About
Package to wrap the ERIS API.

Intended use is to simplify requesting data from ERIS.

To proceed the user must be added to the API group and you must also know the client ID of the group.

## Usage

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

4. class request_api_data method with request class


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
api.request_api_data(request_class)
```

## Extract Tag from  URL

If you have the URL of the tag, you can extract the components of the query via the method `extract_tags_from_url`

Calling this method will return a JSON String of the contents of the dictionary.

```
from ERIS_API import extract_tags_from_url

input_url = "https://eris.com/api/rest/tag/data?start=2021-03-29T00:00:00&end=P1M3D&tags=sample_label:sample_tag:first:PT2M"

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
            "tag": "sample_tag",
            "mode": "first",
            "interval": "PT2M"
        }
    ]
}

```