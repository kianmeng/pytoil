"""
Module responsible for querying the GitHub RESTv3 API.

Author: Tom Fleet
Created: 04/02/2021
"""

import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Union

from .config import Config

# Type hint for generic JSON API response
# Looks complicated but basically means APIResponse is
# either a single JSON blob or a list of JSON blobs
JSONBlob = Dict[str, Union[str, int, bool, Dict[str, Union[str, int, bool]]]]
APIResponse = Union[JSONBlob, List[JSONBlob]]


class API:
    def __init__(
        self, token: Optional[str] = None, username: Optional[str] = None
    ) -> None:
        """
        Representation of the GitHub API.

        Args:
            token (Optional[str], optional): GitHub Personal Access Token.
                Defaults to value from config file.

            username (Optional[str], optional): Users GitHub username.
                Defaults to value from config file.
        """
        # If token passed, set it
        # if not, get from config
        self._token = token or Config.get().token
        # If username passed, set it
        # if not, get from config
        self._username = username or Config.get().username

        self.baseurl: str = "https://api.github.com/"
        self._headers: Dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self._token}",
        }

    def __repr__(self) -> str:
        return (
            self.__class__.__qualname__
            + f"(token={self._token!r}, "
            + f"username={self.username!r})"
        )

    @property
    def token(self) -> Union[str, None]:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    @property
    def username(self) -> Union[str, None]:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        self._username = value

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    @headers.setter
    def headers(self, value: Dict[str, str]) -> None:
        """
        Incase we ever need to set headers explictly.
        """
        self._headers = value

    def get(self, endpoint: str) -> APIResponse:
        """
        Makes an authenticated request to a GitHub API endpoint
        e.g. 'users/repos'.

        Generic base for more specific get methods below.

        Args:
            endpoint (str): Valid GitHub API endpoint.

        Raises:
            HTTPError: If any HTTP error occurs, will raise an exception
                and give a description and standard HTTP status code.

        Returns:
            ApiResponse: JSON API response.
        """

        request = urllib.request.Request(
            url=self.baseurl + endpoint, method="GET", headers=self.headers
        )

        # TODO: Figure out a good way of testing the below block
        with urllib.request.urlopen(request) as r:
            try:
                response: APIResponse = json.loads(r.read())
            except urllib.error.HTTPError:
                raise

        return response

    def get_repo(self, repo: str) -> APIResponse:
        """
        Hits the GitHub REST API 'repos/{owner}/repo' endpoint
        and parses the response.

        In other words it gets the JSON representing a particular `repo`
        belonging to {owner}. In our case, {owner} is `self.username`.

        Args:
            repo (str): The name of the repo to fetch JSON for.

        Raises:
            MissingUsernameError: If `self.username` is None indicating it has
                not been set in the ~/.pytoil.yml config file.

        Returns:
            APIResponse: JSON response for a particular repo.
        """

        return self.get(f"repos/{self.username}/{repo}")

    def get_repos(self) -> APIResponse:
        """
        Hits the GitHub REST API 'user/repos' endpoint and parses
        the response.

        Function similar to `get_repo` the difference being `get_repos` returns
        a list of JSON blobs each representing a repo belonging to `self.username`

        This endpoint requires no parameters because it is the
        'get repos for authenticated user' endpoint and since at this point we have
        `self.token` this automatically fills in the {owner} for us.

        Returns:
            APIResponse: JSON response for a list of all users repos.
        """

        # Because the user is authenticated (token)
        # This gets their repos
        # get will raise if missing token
        return self.get("user/repos")
