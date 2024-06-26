# toml-cli

![Build](https://github.com/mrijken/toml-cli/workflows/CI/badge.svg)
![Hits](https://hitcounter.pythonanywhere.com/count/tag.svg?url=https%3A%2F%2Fgithub.com%2Fmrijken%toml-cli)

Command line interface for toml files.

This can be usefull for getting or setting parts of a toml file without an editor.
Which can be convinient when values have to be read by a script for example in
continuous development steps.


## Install

`pip install toml-cli`

## Get a value

`toml get --toml-path pyproject.toml tool.poetry.name`
`toml get --toml-path pyproject.toml tool.poetry.authors[0]`
`toml get --toml-path pyproject.toml tool.poetry.name --default marc`

## Set a value

`toml set --toml-path pyproject.toml tool.poetry.version 0.2.0`
`toml set --toml-path pyproject.toml tool.poetry.authors[0] "Marc Rijken <marc@rijken.org>"`

When the index exists, the item is changed.  Otherwise, the item will be added to the list.

## Add a section

`toml add_section --toml-path pyproject.toml tool.poetry.new_section`

## Unset a value

`toml unset --toml-path pyproject.toml tool.poetry.version`
