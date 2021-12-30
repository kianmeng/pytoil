from pathlib import Path

import aiofiles
import pytest

from pytoil.config import Config, defaults


def test_config_init_defaults():

    config = Config()

    assert config.projects_dir == defaults.PROJECTS_DIR
    assert config.token == defaults.TOKEN
    assert config.username == defaults.USERNAME
    assert config.vscode == defaults.VSCODE
    assert config.code_bin == defaults.CODE_BIN
    assert config.common_packages == defaults.COMMON_PACKAGES
    assert config.init_on_new == defaults.INIT_ON_NEW


def test_config_init_passed():

    config = Config(
        projects_dir=Path("some/dir"),
        token="sometoken",
        username="me",
        vscode=True,
        code_bin="code-insiders",
        common_packages=["black", "mypy", "flake8"],
        init_on_new=False,
    )

    assert config.projects_dir == Path("some/dir")
    assert config.token == "sometoken"
    assert config.username == "me"
    assert config.vscode is True
    assert config.code_bin == "code-insiders"
    assert config.common_packages == ["black", "mypy", "flake8"]
    assert config.init_on_new is False


def test_config_helper():

    config = Config.helper()

    assert config.projects_dir == defaults.PROJECTS_DIR
    assert config.token == "Put your GitHub personal access token here"
    assert config.username == "This your GitHub username"
    assert config.vscode == defaults.VSCODE
    assert config.code_bin == defaults.CODE_BIN
    assert config.common_packages == defaults.COMMON_PACKAGES
    assert config.init_on_new == defaults.INIT_ON_NEW


@pytest.mark.asyncio
async def test_from_file_raises_on_missing_file():

    with pytest.raises(FileNotFoundError):
        await Config.from_file(path=Path("not/here.yml"))


def test_from_dict():

    config_dict = {
        "projects_dir": "some/dir",
        "token": "sometoken",
        "username": "me",
        "vscode": True,
        "code_bin": "code",
        "common_packages": ["black", "mypy", "flake8"],
        "init_on_new": False,
    }

    config = Config.from_dict(config_dict)

    assert config.projects_dir == Path("some/dir")
    assert config.token == "sometoken"
    assert config.username == "me"
    assert config.vscode is True
    assert config.code_bin == "code"
    assert config.common_packages == ["black", "mypy", "flake8"]
    assert config.init_on_new is False


def test_from_dict_wrong_types():
    """
    Tests that even if everything is brought in as a string
    the types of the config all get handled under the hood.

    Thanks pydantic!
    """

    config_dict = {
        "projects_dir": "some/dir",
        "token": "sometoken",
        "username": "me",
        "vscode": "True",
        "common_packages": ["black", "mypy", "flake8"],
        "init_on_new": "False",
    }

    config = Config.from_dict(config_dict)

    assert config.projects_dir == Path("some/dir")
    assert config.token == "sometoken"
    assert config.username == "me"
    assert config.vscode is True
    assert config.common_packages == ["black", "mypy", "flake8"]
    assert config.init_on_new is False


def test_from_dict_some_missing():
    """
    Tests that even if we pass a partial dict, the default values
    will be used for the missing bits.
    """

    config_dict = {
        "token": "sometoken",
        "username": "me",
        "common_packages": ["black", "mypy", "flake8"],
    }

    config = Config.from_dict(config_dict)

    assert config.projects_dir == defaults.PROJECTS_DIR
    assert config.token == "sometoken"
    assert config.username == "me"
    assert config.vscode is defaults.VSCODE
    assert config.common_packages == ["black", "mypy", "flake8"]
    assert config.init_on_new is defaults.INIT_ON_NEW


@pytest.mark.parametrize(
    "username, token, expected",
    [
        ("", "", False),
        ("", "something", False),
        ("something", "", False),
        (
            "This your GitHub username",
            "Put your GitHub personal access token here",
            False,
        ),
        ("", "Put your GitHub personal access token here", False),
        ("This your GitHub username", "", False),
        ("something", "something", True),
    ],
)
def test_can_use_api(username, token, expected):

    config = Config(username=username, token=token)

    assert config.can_use_api() is expected


@pytest.mark.asyncio
async def test_file_write():
    async with aiofiles.tempfile.NamedTemporaryFile("w") as file:
        # Make a fake config object
        config = Config(
            projects_dir=Path("some/dir"),
            token="sometoken",
            username="me",
            vscode=True,
            common_packages=["black", "mypy", "flake8"],
            init_on_new=False,
        )

        # Write the config
        await config.write(path=file.name)

        file_config = await Config.from_file(file.name)

        assert file_config == config
