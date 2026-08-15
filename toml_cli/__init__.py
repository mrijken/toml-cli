import json
import pathlib
import re

import tomlrt
import typer

import jmespath


app = typer.Typer(no_args_is_help=True)


DEFAULT_TOML_PATH = pathlib.Path("config.toml")


def path_callback(value: pathlib.Path):
    if not value.exists():
        raise typer.BadParameter(f"{value} does not exists")
    return value


def read_toml(toml_path: pathlib.Path) -> tomlrt.Document:
    with toml_path.open("rb") as toml_file:
        return tomlrt.load(toml_file)


def write_toml(document: tomlrt.Document, toml_path: pathlib.Path) -> None:
    with toml_path.open("wb") as toml_file:
        tomlrt.dump(document, toml_file)


@app.command("get")
def get(
    key: str | None = typer.Argument(None),
    toml_path: pathlib.Path = typer.Option(DEFAULT_TOML_PATH, callback=path_callback),
    default: str | None = typer.Option(None),
):
    """Get a value from a toml file."""
    toml_part = read_toml(toml_path)

    if key is not None:
        for key_part in key.split("."):
            match = re.search(r"(?P<key>.*?)\[(?P<index>\d+)\]", key_part)
            if match:
                key = match.group("key")
                index = int(match.group("index"))
                try:
                    toml_part = toml_part[key]
                except KeyError as err:
                    if default is not None:
                        typer.echo(default)
                        return

                    typer.echo(f"error: key '{key}' not found", err=True)
                    raise typer.Exit(code=1) from err

                try:
                    toml_part = toml_part[index]
                except IndexError as err:
                    if default is not None:
                        typer.echo(default)
                        return

                    typer.echo(f"error: index '{index}' not found", err=True)
                    raise typer.Exit(code=1) from err
            else:
                if key_part not in toml_part and default is not None:
                    toml_part[key_part] = default
                try:
                    toml_part = toml_part[key_part]
                except KeyError as err:
                    typer.echo(f"error: key '{key_part}' not found", err=True)
                    raise typer.Exit(code=1) from err

    typer.echo(toml_part)


@app.command("set")
def set_(
    key: str,
    value: str,
    toml_path: pathlib.Path = typer.Option(DEFAULT_TOML_PATH, callback=path_callback),
    to_int: bool = typer.Option(False),
    to_float: bool = typer.Option(False),
    to_bool: bool = typer.Option(False),
    to_array: bool = typer.Option(
        False,
        help='accepts a valid json array and covert it to toml, ie ["Amsterdam","Rotterdam"]',
    ),
):
    """Set a value to a toml file."""
    toml_part = toml_file = read_toml(toml_path)

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except KeyError as err:
            typer.echo(
                f"error: non-existent key '{key}' can not be set to value '{value}'",
                err=True,
            )
            raise typer.Exit(code=1) from err

    try:
        parsed_value: str | int | float | bool | list
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
    except ValueError as err:
        typer.echo(f"error: '{value}' can't be cast to selected type", err=True)
        raise typer.Exit(code=1) from err

    last_key = key.split(".")[-1]  # 'key' may access an array with index, example: tool.poetry.authors[0]
    match = re.search(r"(?P<array>.*?)\[(?P<index>\d+)\]", last_key)
    if match:
        array = match.group("array")
        try:
            toml_part = toml_part[array]
        except KeyError as err:
            typer.echo(f"error: non-existent array '{array}'", err=True)
            raise typer.Exit(code=1) from err

        index = int(match.group("index"))
        if len(toml_part) <= index:
            toml_part.insert(index, parsed_value)
        else:
            toml_part[index] = parsed_value
    else:
        toml_part[last_key] = parsed_value

    write_toml(toml_file, toml_path)


@app.command("add_section")
def add_section(
    key: str,
    toml_path: pathlib.Path = typer.Option(DEFAULT_TOML_PATH, callback=path_callback),
):
    """Add a section with the given key."""
    toml_file = read_toml(toml_path)

    try:
        toml_file.ensure_table(key)
    except tomlrt.TOMLError as err:
        typer.echo(f"error: can not add section '{key}' - {err}", err=True)
        raise typer.Exit(code=1) from err

    write_toml(toml_file, toml_path)


@app.command("unset")
def unset(
    key: str,
    toml_path: pathlib.Path = typer.Option(DEFAULT_TOML_PATH, callback=path_callback),
):
    """Unset a value from a toml file."""
    toml_part = toml_file = read_toml(toml_path)

    for key_part in key.split(".")[:-1]:
        try:
            toml_part = toml_part[key_part]
        except KeyError:
            typer.echo(f"Key {key} can not unset", err=True)

    del toml_part[key.split(".")[-1]]

    write_toml(toml_file, toml_path)


@app.command("search")
def search(
    jmespath_expression: str,
    toml_path: pathlib.Path = typer.Option(DEFAULT_TOML_PATH, callback=path_callback),
):
    """Search for a value in a toml file using JMESPath query."""
    toml_data = read_toml(toml_path)

    try:
        result = jmespath.search(jmespath_expression, toml_data) or "No result found"
    except jmespath.exceptions.JMESPathError as err:
        typer.echo(f"error: invalid jmespath expression - {err}", err=True)
        raise typer.Exit(code=1) from err

    typer.echo(result)


def main():
    app()


if __name__ == "__main__":
    main()
