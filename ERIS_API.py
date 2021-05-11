import logging
import requests
import datetime
import json

from urllib.parse import urlparse, unquote, parse_qs

class ERISAPI(object):
    def __init__(self, base_url, username, password, timeout=None) -> None:
        super().__init__()

        self.base_url = base_url
        self.base_esrm_url = self.base_url+"esrm/rest"
        self.base_api_url = self.base_url+"api/rest"
        self.authenticate_url = "/auth/login"
        self.data_url = "/tag/data"

        self.timeout = 1800 if timeout is None else timeout

        self.access_token = None

        self.username = username
        self.password = password

    def get_access_token(self):
        """Authenticate to ERIS and obtain an access token. 

        If token exists (aka a previous request) then the time is validated 
        against the expiry time of the current token
        """
        if self._current_token_valid():
            return self.access_token.get("x-access-token")

        auth_uri = self.base_url + self.authenticate_url

        result = requests.post(
            auth_uri, auth=(self.username, self.password)
        )
        assert result.status_code == 200, "Failed to reach authentication page"
        # result = requests.post(
        #     auth_uri, 
        #     json={"userId": self.username, "password": self.password}
        # )

        result_json = result.json()

        _status = result_json.get("status")
        _message = result_json.get("message", "General Authentication Error")
        assert _status == 200, _message

        _access_token = result_json.get("access-token")
        self.token_contents = _access_token
        return self.access_token.get("x-access-token")

    def _current_token_valid(self):
        """Validate if current token is valid, if not request new one"""
        if self.access_token is None: return False

        expire_time = self.access_token.get("expires")
        if expire_time is None: return False

        check_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
        expire_time = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%S.%f")
        is_valid = True if expire_time>check_time else False
        return is_valid

    def request_api_data(self, request_parameters):
        """Request ERIS data via the API. Requires request parameters in the form of dictionary.
        Args:
            request_parameters (
                {
                    "start": datetime.datetime,
                    "end": datetime.datetime,
                    tags: ["optional label", "tag", "sample mode", "period"]
                }): dictionary containing the requesting tags

        Returns:
            dict: json result of the request as a dictionary
        """
        try:
            access_token = self.get_access_token()

            params = self._construct_request_parameters(request_parameters)
            uri = self.base_api_url + self.data_url

            result = requests.get(
                uri, 
                params=params, 
                timeout=self.timeout,
                headers={"x-access-token": access_token}
            )
            assert result.status_code == 200, "Failed to reach API"
            result_json = result.json()
            assert result_json.get('status') == 200, result_json.get("message", "Generic error with data request")
            return result.json()
        except AssertionError as e:
            logging.error(e)

    def request_esrm_data(self, request_parameters):
        """Requesting via the ESRM url
        requires API input dictionary and returns the XML content
        """
        try:
            params = self._construct_request_parameters(request_parameters)
            uri = self.base_esrm_url + self.data_url
            result = requests.get(
                uri, 
                params=params, 
                timeout=self.timeout,
            )
            assert result.status_code == 200, "Status Code failed"
            return result.text
        except AssertionError as e:
            logging.error(e)

    def _construct_request_parameters(self, tag_list):
        _start = tag_list.get(
            "start", 
            datetime.datetime.now()-datetime.timedelta(days=1)
        )
        _end = tag_list.get(
            "end",
            "P1D"
        )

        dt_format = "%Y-%m-%dT%H:%M:%S"
        _start = _start.strftime(dt_format) if type(_start) is datetime.datetime else _start
        _end = _end.strftime(dt_format) if type(_end) is datetime.datetime else _end
        _tags = ",".join([":".join(_) for _ in tag_list.get('tags', [])])

        return {"start": _start, "end": _end, "tags": _tags}


def extract_tags_from_url(url):
    """Return the components of the requested url. This is normally obtained via the Source link at the bottom of a request.

    Returns the start/end times, but those are for reference. Main intent is to extract the requested tag from the url"""
    parsed_url = urlparse(url)
    query = unquote(parsed_url.query)
    qs_content = parse_qs(query)

    st = qs_content.get("start")
    et = qs_content.get("end")

    tags = qs_content.get("tags")
    tags = tags[0]
    tag_list = [_.split(":") for _ in tags.split(",")]

    result = json.dumps(
        {
            "start": st,
            "end": et,
            "tags": tag_list
        },
        indent=4
    )

    return result
