from requests.auth import HTTPBasicAuth

import logging
import requests
import datetime
import base64

from ERIS_API.ERIS_Responses import XMLResponse, JSONResponse, ERISResponse


class _Token_Auth(requests.auth.AuthBase):
    """Subclass request auth for token authorization"""
    def __init__(self, username, token):
        self.username = username
        self.token = token

    def __call__(self, r):
        assert self.username is not None, "No username supplied"
        assert self.token is not None, "No token supplied"
        _auth = ':'.join((self.username, self.token)).encode()
        _encoded = base64.b64encode(_auth).strip()
        authstr = 'Token ' + _encoded.decode()
        r.headers['Authorization'] = authstr
        return r


class ERISTag(object):
    def __init__(self, label=None, tag=None, mode=None, interval=None) -> None:
        self.label = label
        self.tag = tag
        self.mode = mode
        self.interval = interval

    def tag_to_string(self):
        vals = [_ for _ in [
            self.label,
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

    def __iter__(self):
        zip_list = zip(["label", "tag","mode","interval"], [self.label, self.tag, self.mode, self.interval])
        for key, val in zip_list:
            yield (key, val)


class ERISRequest(object):
    def __init__(self, start_time, end_time, tags, regex=None, compact=None) -> None:
        self.start = start_time
        self.end = end_time
        self.tags = tags if type(tags) is list else [tags]

        self.regex = regex if type(regex) is bool else None
        self.compact = compact if type(compact) is bool else None
        

class ERISAPI(object):
    def __init__(self, base_url, client_id, username, password=None, token=None, timeout=None):
        """ERIS Api class. 
        
        Handles the authentication, and parsing of the supplied ERISRequest.

        Args:
            base_url (str): URL of the ERIS page.
            client_id (str): client ID of the ERIS site

            username (str): username for authentication
                        
            password (str): password for login. Optional as a token can also be supplied. Default to password if both.
            token (str, optional): token for login. Optional as a password can also be supplied.

            timeout (int, optional): Set default timeout for request. Defaults to 1800 seconds if left as None.
        """
        super().__init__()

        self.base_url = base_url
        self.base_url = base_url[:-1] if self.base_url.endswith("/") else base_url

        self.base_esrm_url = self.base_url+"/esrm/rest"
        self.base_api_url = self.base_url+"/api/rest"

        self.authenticate_url = "/auth/login"
        self.data_url = "/tag/data"

        self.timeout = 1800 if timeout is None else timeout

        self.access_token = None
        self.client_id = client_id

        self.username = username
        self.password = password
        self.login_token = token

        assert any([_ is not None for _ in [self.login_token, self.password]]), "password or token must be supplied"

    def get_access_token(self):
        """Authenticate to ERIS and obtain an access token. 

        If token exists (aka a previous request) then the time is validated 
        against the expiry time of the current token
        """
        if self._current_token_valid():
            return self.access_token.get("x-access-token")

        auth_uri = self.base_api_url + self.authenticate_url

        result = requests.post(
            auth_uri, 
            auth=self.build_auth(), 
            headers={"x-client-id": self.client_id}
        )
        
        assert result.status_code == 200, "Failed to reach authentication page"
        result_json = result.json()

        _status = result_json.get("status")
        _message = result_json.get("message", "General Authentication Error")
        assert _status == 200, f"status: {_status} - message: {_message}"

        _data = result_json.get('data', {})
        self.token_contents = _data
        return self.token_contents.get("x-access-token")

    def build_auth(self):
        """Construct the requests authorization class

        Will return either HTTPBasicAuth or _Token_Auth.

        If password is present, then HTTPBasic, otherwise _Token_Auth
        """
        username = self.username
        password = self.password
        token = self.login_token
        if password is not None:
            return HTTPBasicAuth(username, password)
        elif token is not None:
            return _Token_Auth(username, token)
        
        raise "Username, Password and Token is empty"

    def _current_token_valid(self):
        """Validate if current token is valid.
        
        returns:
            bool: is token valid then True, else False
        """
        if self.access_token is None: return False

        expire_time = self.access_token.get("expires")
        if expire_time is None: return False

        check_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
        expire_time = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%S.%f")
        is_valid = True if expire_time>check_time else False
        return is_valid

    def request_api_data(self, request_parameters):
        """Request ERIS data via the API. Requires request parameters in the form of ERISResponse class.
        Args:
            request_parameters (
                {
                    "start": datetime.datetime,
                    "end": datetime.datetime,
                    tags: ["optional label", "tag", "sample mode", "period"]
                }): ERISResponse containing the requesting tags

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
                headers={
                    "x-access-token": access_token,
                    "x-client-id": self.client_id
                }
            )
            assert result.status_code == 200, "Failed to reach API"
            return ERISResponse(
                JSONResponse(result)
            )
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
            return ERISResponse(
                XMLResponse(result)
            )
        except AssertionError as e:
            logging.error(e)

    def _construct_request_parameters(self, tag_class):
        _start = tag_class.start
        _end = tag_class.end

        dt_format = "%Y-%m-%dT%H:%M:%S"
        _start = _start.strftime(dt_format) if type(_start) is datetime.datetime else _start
        _end = _end.strftime(dt_format) if type(_end) is datetime.datetime else _end
        _tags = ",".join([_.tag_to_string() for _ in tag_class.tags])
        out_params = {"start": _start, "end": _end, "tags": _tags}

        if tag_class.regex is not None:
            out_params["regex"] = tag_class.regex

        if tag_class.compact is not None:
            out_params['compact'] = tag_class.compact

        return out_params
