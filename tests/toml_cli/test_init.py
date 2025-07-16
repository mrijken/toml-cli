import pathlib

from typer.testing import CliRunner

from toml_cli import app

runner = CliRunner()


# def normalized(item):
#     if isinstance(item, dict):
#         return sorted((key, normalized(values)) for key, values in item.items())
#     if isinstance(item, list):
#         return sorted(normalized(x) for x in item)
#     else:
#         return item


# def compare(item1, item2):
#     assert normalized(eval(item1)) == normalized(item2)


def test_get_value(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12
happy = false
addresses = ["Rotterdam", "Amsterdam"]

[person.education]
name = "University"

[[person.vehicles]]
model = "Golf"
year = 2020

[[person.vehicles]]
model = "Prius"
year = 2016
"""
    )

    def get(args, exit_code=0):
        result = runner.invoke(app, args)
        assert result.exit_code == exit_code
        return result.stdout.strip()

    assert get(["get", "--toml-path", str(test_toml_path), "person"]) == (
        "{'name': 'MyName', 'age': 12, 'happy': False, "
        "'addresses': ['Rotterdam', 'Amsterdam'], 'education': {'name': 'University'}, "
        "'vehicles': [{'model': 'Golf', 'year': 2020}, {'model': 'Prius', 'year': 2016}]}"
    )

    assert get(["get", "--toml-path", str(test_toml_path), "person.education"]) == "{'name': 'University'}"

    assert get(["get", "--toml-path", str(test_toml_path), "person.education.name"]) == "University"

    assert get(["get", "--toml-path", str(test_toml_path), "person.age"]) == "12"

    assert (
        get(
            [
                "get",
                "--toml-path",
                str(test_toml_path),
                "person.hobby",
                "--default",
                "programming",
            ]
        )
        == "programming"
    )

    assert (
        get(
            [
                "get",
                "--toml-path",
                str(test_toml_path),
                "person.hobby",
                "--default",
                '""',
            ]
        )
        == '""'
    )

    assert get(["get", "--toml-path", str(test_toml_path), "person.addresses"]) == "['Rotterdam', 'Amsterdam']"

    assert get(["get", "--toml-path", str(test_toml_path), "person.addresses[1]"]) == "Amsterdam"

    assert get(["get", "--toml-path", str(test_toml_path), "person.vehicles"]) == (
        "[{'model': 'Golf', 'year': 2020}, {'model': 'Prius', 'year': 2016}]"
    )

    assert get(["get", "--toml-path", str(test_toml_path), "person.vehicles[1]"]) == "{'model': 'Prius', 'year': 2016}"

    assert get(["get", "--toml-path", str(test_toml_path), "person.vehicles[1].model"]) == "Prius"

    assert get(["get", "--toml-path", str(test_toml_path), "person.not_existing_key"], 1) == ""
    assert get(["get", "--toml-path", str(test_toml_path), "person.vehicles[122]"], 1) == ""

    assert get(["get", "--toml-path", str(test_toml_path), "person.not_existing_key[122]"], 1) == ""


def test_search(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12
happy = false
addresses = ["Rotterdam", "Amsterdam"]

[person.education]
name = "University"

[[person.vehicles]]
model = "Golf"
year = 2020

[[person.vehicles]]
model = "Prius"
year = 2016
"""
    )

    result = runner.invoke(app, ["search", "--toml-path", str(test_toml_path), "person.vehicles[*].model"])
    assert result.exit_code == 0
    assert result.stdout.strip() == (
        "['Golf', 'Prius']"
    )

    result = runner.invoke(app, ["search", "--toml-path", str(test_toml_path), "person.vehicles[*].not_existing_property"])
    assert result.exit_code == 0
    assert result.stdout.strip() == (
        "No result found"
    )

    result = runner.invoke(app, ["search", "--toml-path", str(test_toml_path), "wrong-expression"])
    assert result.exit_code == 1
    assert "error: invalid jmespath expression" in result.stderr


def test_set_value(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
happy = false
age = 12
skills = ["python", "pip"]

[person.education]
name = "University"
"""
    )

    result = runner.invoke(
        app,
        [
            "set",
            "--toml-path",
            str(test_toml_path),
            "person.KEY_THAT_DOES_NOT_EXIST.name",
            "15",
        ],
    )
    assert result.exit_code == 1

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.age", "15"])
    assert result.exit_code == 0
    assert 'age = "15"' in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.age", "15", "--to-int"])
    assert result.exit_code == 0
    assert "age = 15" in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.age", "a", "--to-int"])
    assert result.exit_code != 0

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.gender", "male"])
    assert result.exit_code == 0
    assert 'gender = "male"' in test_toml_path.read_text()

    result = runner.invoke(
        app,
        ["set", "--toml-path", str(test_toml_path), "person.age", "15", "--to-float"],
    )
    assert result.exit_code == 0
    assert "age = 15.0" in test_toml_path.read_text()

    result = runner.invoke(
        app,
        ["set", "--toml-path", str(test_toml_path), "person.age", "a", "--to-float"],
    )
    assert result.exit_code != 0

    result = runner.invoke(
        app,
        [
            "set",
            "--toml-path",
            str(test_toml_path),
            "person.happy",
            "True",
            "--to-bool",
        ],
    )
    assert result.exit_code == 0
    assert "happy = true" in test_toml_path.read_text()

    result = runner.invoke(
        app,
        [
            "set",
            "--toml-path",
            str(test_toml_path),
            "person.addresses",
            '["Amsterdam","London"]',
            "--to-array",
        ],
    )
    assert result.exit_code == 0
    assert 'addresses = ["Amsterdam", "London"]' in test_toml_path.read_text()

    result = runner.invoke(
        app,
        [
            "set",
            "--toml-path",
            str(test_toml_path),
            "person.KEY_THAT_DOES_NOT_EXIST[0]",
            "git",
        ],
    )
    assert result.exit_code == 1

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.skills[1]", "toml"])
    assert result.exit_code == 0
    assert 'skills = ["python", "toml"]' in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "person.skills[2]", "git"])
    assert result.exit_code == 0
    assert 'skills = ["python", "toml", "git"]' in test_toml_path.read_text()

    result = runner.invoke(
        app,
        ["set", "--toml-path", str(test_toml_path), "person.skills[1337]", "h4ck3rm4n"],
    )
    assert result.exit_code == 0
    assert 'skills = ["python", "toml", "git", "h4ck3rm4n"]' in test_toml_path.read_text()


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


def test_set_in_out_of_order_table(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[root.d1]
f1 = "f1"
[root]
f2 = "f2"
"""
    )

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "root.f3", "f3"])
    assert result.exit_code == 0
    assert """[root]
f2 = "f2"
f3 = "f3"
""" in test_toml_path.read_text()


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

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person.education.name"])
    assert result.exit_code == 0
    assert "[person.education]" in test_toml_path.read_text()
    assert "University" not in test_toml_path.read_text()

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person.education"])
    assert result.exit_code == 0
    assert "[persion.education]" not in test_toml_path.read_text()

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person"])
    assert result.exit_code == 0
    assert len(test_toml_path.read_text()) == 1  # just a newline


def test_no_command():
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "--help" in result.stdout
    assert "Commands" in result.stdout
    assert "Commands" in result.stdout
