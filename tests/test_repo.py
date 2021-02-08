"""
Tests for the repo module.

Author: Tom Fleet
Created: 05/02/2021
"""

import pathlib
import subprocess
import urllib.error

import pytest

import pytoil
from pytoil.exceptions import (
    GitNotInstalledError,
    LocalRepoExistsError,
    RepoNotFoundError,
)
from pytoil.repo import Repo


def test_repo_init(mocker, temp_config_file):

    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        repo = Repo(owner="me", name="myproject")

        assert repo.owner == "me"
        assert repo.name == "myproject"
        assert repo.url == "https://github.com/me/myproject.git"
        assert repo.path == pathlib.Path("Users/tempfileuser/projects/myproject")


def test_repo_init_defaults(mocker, temp_config_file):

    # Patch out to our fake config file to make sure it grabs from the config
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        # name is required
        repo = Repo(name="diffproject")

        assert repo.owner == "tempfileuser"
        assert repo.name == "diffproject"
        assert repo.url == "https://github.com/tempfileuser/diffproject.git"
        assert repo.path == pathlib.Path("Users/tempfileuser/projects/diffproject")


def test_repo_repr(mocker, temp_config_file):

    # Patch out to our fake config file to make sure it grabs from the config
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        repo = Repo(owner="me", name="myproject")

        assert repo.__repr__() == "Repo(owner='me', name='myproject')"


def test_repo_setters(mocker, temp_config_file):

    # Patch out to our fake config file to make sure it grabs from the config
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        repo = Repo(name="myproject")

        # Assert values before
        assert repo.url == "https://github.com/tempfileuser/myproject.git"
        assert repo.path == pathlib.Path("Users/tempfileuser/projects/myproject")

        # Set the values
        # repo.url is read only
        repo.path = pathlib.Path("fake/local/path/myproject")

        # Assert values after
        assert repo.url == "https://github.com/tempfileuser/myproject.git"
        assert repo.path == pathlib.Path("fake/local/path/myproject")


def test_repo_exists_local_returns_true_if_path_exists(mocker, temp_config_file):

    # Patch out the config file to point to our temporary one
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir in the config file exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        # Patch out Repo.path to something we know exists: this file
        with mocker.patch.object(pytoil.repo.Repo, "path", pathlib.Path(__file__)):

            repo = Repo(name="fakerepo")

            assert repo.exists_local() is True


def test_repo_exists_local_returns_false_if_path_doesnt_exist(mocker, temp_config_file):

    # Patch out the config file to point to our temporary one
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Patch out the projects_dir to our temp config file, purely so
        # it thinks project_dir exists
        with mocker.patch.object(
            pytoil.config.Config, "projects_dir", temp_config_file
        ):

            # Also patch out the return from pathlib.Path.exists to trick
            # it into thinking the projects_dir in the config file exists

            # Patch out Repo.path to something we know doesn't exist
            with mocker.patch.object(
                pytoil.repo.Repo, "path", pathlib.Path("not/here")
            ):

                repo = Repo(name="fakerepo")

                assert repo.exists_local() is False


def test_repo_exists_remote_returns_false_on_missing_repo(mocker, temp_config_file):

    # Patch out the config file to point to our temporary one
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Patch out urllib.request.urllopen to always raise a 404 not found
        # which is our indication in `exists_remote` that the repo doesn't exist
        mocker.patch(
            "pytoil.api.urllib.request.urlopen",
            autospec=True,
            side_effect=urllib.error.HTTPError(
                "https://api.github.com/not/here",
                404,
                "Not Found",
                {"header": "yes"},
                None,
            ),
        )

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        # Rest of the params will be filled in by our patched config file
        repo = Repo(name="missingproject")

        assert repo.exists_remote() is False


def test_repo_exists_remote_returns_true_on_valid_repo(mocker, temp_config_file):

    # Same trick with the config file
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Now patch out API.get_repo to return some arbitrary dict
        # Indication that everything worked okay
        mocker.patch(
            "pytoil.api.API.get_repo",
            autospec=True,
            return_value={"repo": "yes", "name": "myproject"},
        )

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        repo = Repo(name="myproject")

        assert repo.exists_remote() is True


@pytest.mark.parametrize(
    "error_code, message",
    [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (408, "Request Timeout"),
        (502, "Bad Gateway"),
        (500, "Internal Server Error"),
    ],
)
def test_repo_exists_remote_raises_on_other_http_error(
    mocker, temp_config_file, error_code, message
):

    # Same trick with the config file
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Patch out urllib.request.urlopen to raise
        # other HTTP errors from our parametrize
        mocker.patch(
            "pytoil.api.urllib.request.urlopen",
            autospec=True,
            side_effect=urllib.error.HTTPError(
                "https://api.nothub.com/not/here",
                error_code,
                message,
                {"header": "yes"},
                None,
            ),
        )

        # Also patch out the return from pathlib.Path.exists to trick
        # it into thinking the projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        repo = Repo(name="myproject")

        with pytest.raises(urllib.error.HTTPError):
            repo.exists_remote()


@pytest.mark.parametrize("which_return", ["", None, False])
def test_repo_clone_raises_on_invalid_git(mocker, temp_config_file, which_return):

    # Same trick with the config file
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Patch out shutil.which
        mocker.patch(
            "pytoil.repo.shutil.which", autospec=True, return_value=which_return
        )

        # Patch out pathlib.exists to trick the test into thinking `projects_dir` exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        with pytest.raises(GitNotInstalledError):
            repo = Repo(owner="me", name="myproject")
            repo.clone()


def test_repo_clone_raises_if_local_repo_already_exists(mocker, temp_config_file):

    # Same trick with the config file
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Make it look like we have a valid git
        mocker.patch("pytoil.repo.shutil.which", autospec=True, return_value=True)

        # Make it think the repo already exists locally
        mocker.patch("pytoil.repo.Repo.exists_local", autospec=True, return_value=True)

        # Finally, make it think the configured projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        with pytest.raises(LocalRepoExistsError):
            repo = Repo(owner="me", name="myproject")
            repo.clone()


def test_repo_clone_correctly_calls_git(mocker, temp_config_file):

    # Same trick with the config file
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Make it look like we have a valid git
        mocker.patch("pytoil.repo.shutil.which", autospec=True, return_value=True)

        # Ensure the repo doesnt already exist
        mocker.patch("pytoil.repo.Repo.exists_local", autospec=True, return_value=False)

        # Ensure the repo "exists" on github
        mocker.patch("pytoil.repo.Repo.exists_remote", autospec=True, return_value=True)

        # Finally, make it think the configured projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        # Mock the subprocess of calling git
        mock_subprocess = mocker.patch("pytoil.repo.subprocess.run", autospec=True)

        repo = Repo(name="fakerepo")

        path = repo.clone()

        # Assert git would have been called with correct args
        mock_subprocess.assert_called_once_with(
            ["git", "clone", "https://github.com/tempfileuser/fakerepo.git"],
            cwd=pathlib.Path("Users/tempfileuser/projects"),
            check=True,
        )

        # Assert the path was updated
        assert path == pathlib.Path("Users/tempfileuser/projects/fakerepo")
        assert repo.path == pathlib.Path("Users/tempfileuser/projects/fakerepo")


def test_repo_clone_raises_subprocess_error_if_anything_goes_wrong(
    mocker, temp_config_file
):

    # Same trick with the config file
    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Make it look like we have a valid git
        mocker.patch("pytoil.repo.shutil.which", autospec=True, return_value=True)

        # Ensure the repo doesnt already exist
        mocker.patch("pytoil.repo.Repo.exists_local", autospec=True, return_value=False)

        # Ensure the repo "exists" on github
        mocker.patch("pytoil.repo.Repo.exists_remote", autospec=True, return_value=True)

        # Finally, make it think the configured projects_dir exists
        mocker.patch(
            "pytoil.config.pathlib.Path.exists", autospec=True, return_value=True
        )

        # Mock the subprocess of calling git, but have it raise an error
        mock_subprocess = mocker.patch(
            "pytoil.repo.subprocess.run",
            autospec=True,
            side_effect=[subprocess.CalledProcessError(-1, "cmd")],
        )

        repo = Repo(name="fakerepo")

        with pytest.raises(subprocess.CalledProcessError):

            repo.clone()

            # Assert git would have been called with correct args
            mock_subprocess.assert_called_once_with(
                ["git", "clone", "https://github.com/tempfileuser/fakerepo.git"],
                cwd=pathlib.Path("Users/tempfileuser/projects"),
                check=True,
            )


def test_repo_clone_raises_on_missing_remote_repo(mocker, temp_config_file):

    with mocker.patch.object(pytoil.config.Config, "CONFIG_PATH", temp_config_file):

        # Make it look like we have a valid git
        mocker.patch("pytoil.repo.shutil.which", autospec=True, return_value=True)

        # Ensure the repo doesnt already exist
        mocker.patch("pytoil.repo.Repo.exists_local", autospec=True, return_value=False)

        # Ensure the repo doesnt already exist
        mocker.patch(
            "pytoil.repo.Repo.exists_remote", autospec=True, return_value=False
        )

        # Finally, make it think the configured projects_dir exists
        # Hacky by pointing it to our config file but it works
        with mocker.patch.object(
            pytoil.config.Config, "projects_dir", temp_config_file
        ):

            repo = Repo(name="fakerepo")

            with pytest.raises(RepoNotFoundError):
                repo.clone()
