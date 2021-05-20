from ERIS_API import json_to_tags, extract_tags_from_url

json_dict = [
    {
        "label": "Label",
        "tag": "TAG",
        "mode": "periodTotal",
        "interval": "P1D"
    }
]
tags = json_to_tags(json_dict=json_dict)

tags = json_to_tags(json_path="tag_list.json")


input_url = "https://eris.com/api/rest/tag/data?start=2021-03-29T00:00:00&end=P1M3D&tags=sample_label:sample.tag:first:PT2M"
url_tags = extract_tags_from_url(input_url)
