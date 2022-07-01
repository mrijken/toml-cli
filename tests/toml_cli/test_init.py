import pathlib

import pytest

from typer.testing import CliRunner

from toml_cli import app

runner = CliRunner()


def test_get_value(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["get", "--toml-path", str(test_toml_path), "person"])
    assert result.exit_code == 0
    assert "{'name': 'MyName', 'age': 12, 'education': {'name': 'University'}}" in result.stdout

    result = runner.invoke(app, ["get", "--toml-path", str(test_toml_path), "person", "education"])
    assert result.exit_code == 0
    assert "{'name': 'University'}" in result.stdout

    result = runner.invoke(app, ["get", "--toml-path", str(test_toml_path), "person", "education", "name"])
    assert result.exit_code == 0
    assert "University" in result.stdout

    result = runner.invoke(app, ["get", "--toml-path", str(test_toml_path), "person", "age"])
    assert result.exit_code == 0
    assert "12" in result.stdout


def test_set_value(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
happy = false
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.age", "15"])
    assert result.exit_code == 0
    assert 'age = "15"' in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.age", "15", "--to-int"])
    assert result.exit_code == 0
    assert "age = 15" in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.gender", "male"])
    assert result.exit_code == 0
    assert 'age = 15\ngender = "male"' in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.age", "15", "--to-float"])
    assert result.exit_code == 0
    assert "age = 15.0" in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.happy", "True", "--to-bool"])
    assert result.exit_code == 0
    assert "happy = true" in test_toml_path.read_text()


def test_add_section(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["add_section", "--toml-path", str(test_toml_path), "address"])
    assert result.exit_code == 0
    assert "[address]" in test_toml_path.read_text()

    result = runner.invoke(app, ["add_section", "--toml-path", str(test_toml_path), "address.work"])
    assert result.exit_code == 0
    assert "[address]\n[address.work]" in test_toml_path.read_text()


def test_unset(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person", "education", "name"])
    assert result.exit_code == 0
    assert "[person.education]" in test_toml_path.read_text()
    assert "University" not in test_toml_path.read_text()

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person", "education"])
    assert result.exit_code == 0
    assert "[persion.education]" not in test_toml_path.read_text()

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person"])
    assert result.exit_code == 0
    assert len(test_toml_path.read_text()) == 1  # just a newline

def test_no_command():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "--help" in result.stdout
    assert "Commands" in result.stdout
