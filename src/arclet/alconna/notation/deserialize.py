from __future__ import annotations

from pathlib import Path
from typing import Any

from arclet.alconna import (
    Alconna,
    Arg,
    Args,
    Option,
    OptionResult,
    Subcommand,
    SubcommandResult,
    CommandMeta,
)
from arclet.alconna.action import Action, ActType, store_false, store_true, append, count, store_value
from arclet.alconna.typing import TPrefixes
from nepattern import AllParam, AnyOne, AnyString, type_parser, Empty
from pyhocon import ConfigFactory
import importlib

_actions = {
    "store_false": store_false,
    "store_true": store_true,
    "append": append,
    "count": count,
}


def dict_action(data: dict | str) -> Action:
    if isinstance(data, str):
        return _actions.get(data, store_value(data))
    return Action(
        type=ActType(data["type"]),
        value=... if data["value"] == "..." else data["value"]
    )


def dict_arg(name: str, data: str | dict) -> Arg:
    if isinstance(data, str):
        return Arg(name=name, value=type_parser(data))
    if data["value"] == "&all_param":
        _val = AllParam
    elif data["value"] == "&any":
        _val = AnyOne
    elif data["value"] == "&any_string":
        _val = AnyString
    else:
        _val = type_parser(data["value"])
    _default = Empty if data.get("default", None) == "&empty" else data.get("default", None)
    if data.get("flag", None):
        name += ";" + "".join(data["flag"])
    return Arg(
        name=name,
        value=_val,
        field=_default,
        notice=data.get("notice", None),
        seps=data.get("separators", (" ",)),
    )


def dict_args(data: dict) -> Args:
    return Args(
        *[dict_arg(name, arg) for name, arg in data.items()]
    )


def dict_option_result(data: Any) -> OptionResult:
    if isinstance(data, dict):
        return OptionResult(**data)
    return OptionResult(value=data)


def dict_subcommand_result(data: Any) -> SubcommandResult:
    if not isinstance(data, dict):
        return SubcommandResult(value=data)
    _data = {}
    for name, value in data.items():
        if name == "options":
            _data[name] = {
                n: dict_option_result(v) for n, v in value.items()
            }
        elif name == "subcommands":
            _data[name] = {
                n: dict_subcommand_result(v) for n, v in value.items()
            }
        else:
            _data[name] = value

    return SubcommandResult(**_data)


def dict_option(data: dict) -> Option:
    return Option(
        name=data["name"],
        alias=data.get("aliases", None),
        args=dict_args(data.get("args", {})),
        default=dict_option_result(data["default"]) if data.get("default", None) is not None else None,
        action=dict_action(data["action"]) if data.get("action", None) is not None else None,
        dest=data.get("dest", None),
        help_text=data.get("help", None),
        requires=data.get("requires", None),
        priority=data.get("priority", 0),
        compact=data.get("compact", False),
        separators=data.get("separators", (" ",)),
    )


def dict_subcommand(data: dict) -> Subcommand:
    _opts = []
    if data.get("options", None) is not None:
        _opts.extend(dict_option(opt) for opt in data["options"])
    if data.get("subcommands", None) is not None:
        _opts.extend(dict_subcommand(sub) for sub in data["subcommands"])
    return Subcommand(
        data["name"],
        *dict_args(data.get("args", {})),
        *_opts,
        dest=data.get("dest", None),
        help_text=data.get("help", None),
        requires=data.get("requires", None),
        default=dict_subcommand_result(data["default"]) if data.get("default", None) is not None else None,
        separators=data.get("separators", (" ",)),
    )


def dict_prefixes(data: dict) -> TPrefixes:
    res = []
    if data["pair"]:
        res.extend(
            (
                importlib.import_module(pair["data"][0]["module"]).__getattr__(
                    pair["data"][0]["name"]
                ),
                pair["data"][1]["value"],
            )
            for pair in data["data"]
        )
    else:
        for item in data["data"]:
            if item["type"] == "str":
                res.append(item["value"])
            elif item["type"] == "type":
                res.append(importlib.import_module(item["module"]).__getattr__(item["name"]))
            else:
                res.append(type_parser(item["key"]))
    return res


def from_dict(data: dict) -> Alconna:
    _opts = []
    if data.get("options", None) is not None:
        _opts.extend(dict_option(opt) for opt in data["options"])
    if data.get("subcommands", None) is not None:
        _opts.extend(dict_subcommand(sub) for sub in data["subcommands"])
    return Alconna(
        data["command"],
        dict_prefixes(data["prefixes"]) if data.get("prefixes", None) is not None else [],
        *_opts,
        dict_args(data.get("args", {})),
        meta=CommandMeta(**data.get("meta", {})),
        namespace=data.get("namespace", None),
        separators=data.get("separators", (" ",)),
    )


def loads(conf: str) -> Alconna:
    return from_dict(ConfigFactory.parse_string(conf))


def load(path: str | Path, encoding: str = "utf-8") -> Alconna:
    return from_dict(ConfigFactory.parse_file(str(path), encoding=encoding))
