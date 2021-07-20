from typing import List, Union, Dict, Any, Optional
import datetime

from uuid import uuid4

class ERISTag(object):
    def __init__(self, label: Optional[str]=None, tag: Optional[str]=None, mode: Optional[str]=None, interval: Optional[str]=None) -> None:
        """Init the tag class

        to provide a matching back to the tag following the request, the tag is generated with a uuid to identify it.
        The UUID is used within the label and becomes the tagUID in the response. 

        The reasoning is to fix the spaces issues with the request. ERIS internally seems to want to change the encoding which introduces spaces into the reuqest internally, causing it to fail.
        This then alows for spaces in the label, but the query is sent without spaces and translated back afterwards.
        
        Args:
            label (str, optional): label to use in response dataframe. Defaults to None.
            tag (str, optional): tag to get data of. Defaults to None.
            mode (str, optional): sample mode. Defaults to None.
            interval (str, optional): sample interval. Defaults to None.
        """
        assert all([_ is not None for _ in [tag, mode, interval]]), "Must supply a tag, mode and interval"
        
        self.rr = uuid4()
        self.request_uuid = str(self.rr).replace("-","")
        self.label = label
        self.tag = tag
        self.mode = mode
        self.interval = interval

    def tag_to_string(self) -> str:
        vals = [_ for _ in [
            self.request_uuid,
            self.tag,
            self.mode,
            self.interval
        ] if _ is not None]

        return ":".join(vals)

    def __str__(self) -> str:
        lbl = f"Label: {self.label}" if self.label is not None else None
        tag = f"Tag: {self.tag}"
        mode = f"Mode: {self.mode}"
        interval = f"Interval: {self.interval}"
        vals = [_ for _ in [lbl, tag, mode, interval] if _ is not None]
        return "\n".join(vals)

    def __iter__(self) -> Dict[str, str]:
        zip_list = zip(["label", "tag","mode","interval"], [self.label, self.tag, self.mode, self.interval])
        for key, val in zip_list:
            yield (key, val)


class ERISRequest(object):
    def __init__(self, start_time: Union[datetime.datetime, str], end_time: Union[datetime.datetime, str], tags: List[ERISTag], regex: Optional[bool] =None, compact: Optional[bool]=None) -> None:
        if isinstance(tags, list):
            assert all([isinstance(_, ERISTag) for _ in tags]), "Must provide only ERISTag classes as a tag"
        else:
            assert isinstance(tags, ERISTag), "Must provide only ERISTag classes as a tag"
            tags = [tags]

        self.start = start_time
        self.end = end_time
        self.tags = tags
        self.regex = regex if isinstance(regex, bool) else None
        self.compact = compact if isinstance(compact, bool) else None
        