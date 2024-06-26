import json
import pathlib
import re
from typing import Optional

import tomlkit
import tomlkit.exceptions
import typer

app = typer.Typer(no_args_is_help=True)


@app.command("get")
def get(
    key: Optional[str] = typer.Argument(None),
    toml_path: pathlib.Path = typer.Option(pathlib.Path("config.toml")),
    default: Optional[str] = typer.Option(None),
):
    """Get a value from a toml file"""
    toml_part = tomlkit.parse(toml_path.read_text())

    if key is not None:
        for key_part in key.split("."):
            match = re.search(r"(?P<key>.*?)\[(?P<index>\d+)\]", key_part)
            if match:
                key = match.group("key")
                index = int(match.group("index"))
                try:
                    toml_part = toml_part[key]
                except KeyError:
                    if default:
                        typer.echo(default)
                        return

                    typer.echo(f"error: key '{key}' not found", err=True)
                    exit(1)

                try:
                    toml_part = toml_part[index]
                except IndexError:
                    if default:
                        typer.echo(default)
                        return

                    typer.echo(f"error: index '{index}' not found", err=True)
                    exit(1)
            else:
                if key_part not in toml_part and default:
                    toml_part[key_part] = default
                try:
                    toml_part = toml_part[key_part]
                except KeyError:
                    typer.echo(f"error: key '{key_part}' not found", err=True)
                    exit(1)

    typer.echo(toml_part.unwrap())


@app.command("set")
def set_(
    key: str,
    value: str,
    toml_path: pathlib.Path = typer.Option(pathlib.Path("config.toml")),
    to_int: bool = typer.Option(False),
    to_float: bool = typer.Option(False),
    to_bool: bool = typer.Option(False),
    to_array: bool = typer.Option(
        False,
        help='accepts a valid json array and covert it to toml, ie ["Amsterdam","Rotterdam"]',
    ),
):
    """Set a value to a toml file"""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except tomlkit.exceptions.NonExistentKey:
            typer.echo(f"error: non-existent key '{key}' can not be set to value '{value}'", err=True)
            exit(1)

    if to_int:
        parsed_value = int(value)
    elif to_float:
        parsed_value = float(value)
    elif to_bool:
        parsed_value = value.lower() in ["true", "yes", "y", "1"]
    elif to_array:
        parsed_value = json.loads(value)
    else:
        parsed_value = value

    last_key = key.split(".")[-1]  # 'key' may access an array with index, example: tool.poetry.authors[0]
    match = re.search(r"(?P<array>.*?)\[(?P<index>\d+)\]", last_key)
    if match:
        array = match.group("array")
        try:
            toml_part = toml_part[array]
        except tomlkit.exceptions.NonExistentKey:
            typer.echo(f"error: non-existent array '{array}'", err=True)
            exit(1)

        index = int(match.group("index"))
        if len(toml_part) <= index:
            toml_part.insert(index, parsed_value)
        else:
            toml_part[index] = parsed_value
    else:
        toml_part[last_key] = parsed_value

    toml_path.write_text(tomlkit.dumps(toml_file))


@app.command("add_section")
def add_section(
    key: str,
    toml_path: pathlib.Path = typer.Option(pathlib.Path("config.toml")),
):
    """Add a section with the given key"""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())

    for key_part in key.split("."):
        if key_part not in toml_part:
            toml_part[key_part] = tomlkit.table()
        toml_part = toml_part[key_part]

    toml_path.write_text(tomlkit.dumps(toml_file))


@app.command("unset")
def unset(key: str, toml_path: pathlib.Path = typer.Option(pathlib.Path("config.toml"))):
    """Unset a value from a toml file"""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except tomlkit.exceptions.NonExistentKey:
            typer.echo(f"Key {key} can not unset", err=True)

    del toml_part[key.split(".")[-1]]

    toml_path.write_text(tomlkit.dumps(toml_file))


def main():
    app()


if __name__ == "__main__":
    main()
