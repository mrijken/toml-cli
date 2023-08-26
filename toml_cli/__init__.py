"""toml-cli: Command line interface for toml files."""

import json
import pathlib
import re

import tomlkit
import tomlkit.exceptions
import typer

from typing import Optional


app = typer.Typer(no_args_is_help=True)


@app.command("get")
def get(
    key: Optional[str] = typer.Argument(None),
    toml_path: Optional[pathlib.Path] = typer.Option(pathlib.Path("config.toml")),
) -> None:
    """Get a value from a toml file."""
    toml_part = tomlkit.parse(toml_path.read_text())

    if key is not None:
        for key_part in key.split("."):
            match = re.search(r"(?P<key>.*?)\[(?P<index>\d+)\]", key_part)
            if match:
                key = match.group("key")
                index = int(match.group("index"))
                toml_part = toml_part[key][index]
            else:
                toml_part = toml_part[key_part]

    typer.echo(toml_part)


@app.command("set")
def set_(
    key: str,
    value: str,
    toml_path: Optional[pathlib.Path] = typer.Option(pathlib.Path("config.toml")),
    to_int: Optional[bool] = typer.Option(False),
    to_float: Optional[bool] = typer.Option(False),
    to_bool: Optional[bool] = typer.Option(False),
    to_array: Optional[bool] = typer.Option(
        False,
        help='Accepts a valid json array and covert it to toml, ie ["Amsterdam","Rotterdam"].',
    ),
) -> None:
    """Set a value to a toml file."""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except tomlkit.exceptions.NonExistentKey:
            typer.echo(f"Key {key} can not set", err=True)

    if to_int:
        value = int(value)
    if to_float:
        value = float(value)
    if to_bool:
        value = value.lower() in ["true", "yes", "y", "1"]
    if to_array:
        value = json.loads(value)

    toml_part[key.split(".")[-1]] = value

    toml_path.write_text(tomlkit.dumps(toml_file))


@app.command("add_section")
def add_section(
    key: str,
    toml_path: Optional[pathlib.Path] = typer.Option(pathlib.Path("config.toml")),
) -> None:
    """Add a section with the given key."""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())

    for key_part in key.split("."):
        if key_part not in toml_part:
            toml_part[key_part] = tomlkit.table()
        toml_part = toml_part[key_part]

    toml_path.write_text(tomlkit.dumps(toml_file))


@app.command("update_dependency_list")
def update_dependency_list(
    key: str,
    value: str,
    version: str,
    toml_path: Optional[pathlib.Path] = typer.Option(pathlib.Path("config.toml")),
) -> None:
    """Add/modify a value to a list element in a toml file."""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())
    modifiers = [">=", "!=", "==", ">=", "<=", "~=", "===", ">"]
    version_has_mod = any(m in version for m in modifiers)

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except tomlkit.exceptions.NonExistentKey:
            typer.echo(f"Key {key} can not set", err=True)

    if isinstance(toml_part[key.split(".")[-1]], tomlkit.items.Array):
        na = []
        for el in toml_part[key.split(".")[-1]]:
            if el.startswith(value):
                # The package was found
                for m in modifiers:
                    if m in el:
                        # The package was listed with a specific version
                        el = (
                            el.split(m)[0]
                            + (m if not version_has_mod else "")
                            + version
                        )
                        break
                else:
                    # The package was not listed with a specific version
                    el = value + (version if version_has_mod else ">=" + version)
            na.append(el)
        # Formatting
        ta = tomlkit.array()
        for n in na:
            ta.add_line(n)
        ta.add_line(indent="")
        # Modify toml
        toml_part[key.split(".")[-1]] = ta
    else:
        typer.echo(f"Key {key} does not point to an array", err=True)

    toml_path.write_text(tomlkit.dumps(toml_file))


@app.command("unset")
def unset(
    key: str,
    toml_path: Optional[pathlib.Path] = typer.Option(pathlib.Path("config.toml")),
) -> None:
    """Unset a value from a toml file."""
    toml_part = toml_file = tomlkit.parse(toml_path.read_text())

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except tomlkit.exceptions.NonExistentKey:
            typer.echo(f"Key {key} can not unset", err=True)

    del toml_part[key.split(".")[-1]]

    toml_path.write_text(tomlkit.dumps(toml_file))


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
