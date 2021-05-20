from ERIS_API import ERISTag, ERISAPI, ERISRequest, extract_tags_from_url

import datetime

url = "https://www.eris.com/"
client_id="000"
username="username"
token="abc123"

api = ERISAPI(
    base_url=url, 
    client_id=client_id,
    username=username, 
    token=token
)

request = ERISRequest(
    start_time=datetime.datetime(2021,1,1),
    end_time=datetime.datetime(2021,2,1),
    tags=[
        ERISTag(
            "Tag Label",
            "TAG",
            "periodTotal",
            "P1D",
        )
    ]
)
response = api.request_api_data(request)

df = response.convert_tags_to_dataframes()
