from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Literal

from arclet.alconna import (
    Alconna,
    Arg,
    Args,
    Option,
    OptionResult,
    Subcommand,
    SubcommandResult,
)
from arclet.alconna.action import Action
from arclet.alconna.typing import TPrefixes
from nepattern import AllParam, AnyOne, AnyString, BasePattern, Empty
from pyhocon import ConfigTree, HOCONConverter
from typing_extensions import get_origin


def action_dict(act: Action) -> ConfigTree:
    res = ConfigTree()
    res.put("type", act.type.value)
    res.put("value", "..." if act.value is ... else act.value)
    return res


def arg_dict(arg: Arg) -> ConfigTree:
    if arg.value == AllParam:
        _val = "&all_param"
    elif arg.value == AnyOne:
        _val = "&any"
    elif arg.value == AnyString:
        _val = "&any_string"
    else:
        _val = (
            arg.value.alias
            or (get_origin(arg.value.origin) or arg.value.origin).__name__
        )
    _default = "&empty" if arg.field.default is Empty else arg.field.default
    res = ConfigTree()
    res.put("value", _val)
    if _default is not None:
        res.put("default", _default)
    if arg.notice:
        res.put("notice", arg.notice)
    if arg.flag:
        res.put("flag", [flag.value for flag in arg.flag])
    if arg.separators != (" ",):
        res.put("separators", arg.separators)
    return res


def args_dict(args: Args) -> ConfigTree:
    res = ConfigTree()
    for arg in args:
        res.put(arg.name, arg_dict(arg))
    return res


def option_result_dict(opt: OptionResult) -> ConfigTree:
    res = ConfigTree()
    if opt.value is not ...:
        res["value"] = opt.value
    if opt.args:
        res["args"] = opt.args
    return res


def subcommand_result_dict(sub: SubcommandResult) -> ConfigTree:
    res = ConfigTree()
    if sub.value is not ...:
        res["value"] = sub.value
    if sub.args:
        res["args"] = sub.args
    if sub.options:
        res["options"] = {
            key: option_result_dict(opt) for key, opt in sub.options.items()
        }
        res["subcommands"] = {
            key: subcommand_result_dict(sub) for key, sub in sub.subcommands.items()
        }
    return res


def option_dict(opt: Option) -> ConfigTree:
    res = ConfigTree()
    res.put("name", opt.name)
    if opt.aliases:
        res.put("aliases", list(opt.aliases))
    if not opt.args.empty:
        res.put("args", args_dict(opt.args))
    if opt.default is not None:
        if isinstance(opt.default, OptionResult):
            _default = option_result_dict(opt.default)
            _default.put("model", True)
            res.put("default", _default)
        else:
            res.put("default", ConfigTree(model=False, value=opt.default))
    if opt.action is not None:
        res.put("action", action_dict(opt.action))
    if opt.dest != opt.name:
        res.put("dest", opt.dest)
    if opt.separators != (" ",):
        res.put("separators", list(opt.separators))
    if opt.help_text != opt.dest:
        res.put("help", opt.help_text)
    if opt.requires:
        res.put("requires", opt.requires)
    res.put("priority", opt.priority)
    res.put("compact", opt.compact)
    return res


def subcommand_dict(sub: Subcommand) -> ConfigTree:
    res = ConfigTree()
    res.put("name", sub.name)
    if not sub.args.empty:
        res.put("args", args_dict(sub.args))
    if sub.options:
        res.put(
            "options",
            [option_dict(opt) for opt in sub.options if isinstance(opt, Option)],
        )
        res.put(
            "subcommands",
            [
                subcommand_dict(sub)
                for sub in sub.options
                if isinstance(sub, Subcommand)
            ],
        )
    if sub.default is not None:
        if isinstance(sub.default, SubcommandResult):
            _default = subcommand_result_dict(sub.default)
            _default.put("model", True)
            res.put("default", _default)
        else:
            res.put("default", ConfigTree(model=False, value=sub.default))
    if sub.dest != sub.name:
        res.put("dest", sub.dest)
    if sub.help_text != sub.dest:
        res.put("help", sub.help_text)
    if sub.separators != (" ",):
        res.put("separators", list(sub.separators))
    if sub.requires:
        res.put("requires", sub.requires)
    return res


def prefixes_dict(prefixes: TPrefixes) -> dict:
    res = {"pair": isinstance(prefixes[0], tuple), "data": []}
    for header in prefixes:
        if isinstance(header, str):
            res["data"].append({"type": "str", "value": header})
        elif isinstance(header, type):
            res["data"].append(
                {"type": "type", "module": header.__module__, "name": header.__name__}
            )
        elif isinstance(header, BasePattern):
            res["data"].append(
                {
                    "type": "pattern",
                    "key": header.alias
                    or (get_origin(header.origin) or header.origin).__name__,
                    "module": header.__module__,
                }
            )
        elif isinstance(header, tuple):
            res["data"].append(
                {
                    "type": "pair",
                    "data": [
                        {
                            "type": "type",
                            "module": header[0].__module__,
                            "name": header[0].__name__,
                        },
                        {"type": "str", "value": header[1]},
                    ],
                }
            )
    return res


def to_conf(alconna: Alconna) -> ConfigTree:
    res = ConfigTree()
    res.put("namespace", alconna.namespace)
    res.put("command", str(alconna.command))
    if alconna.prefixes:
        res.put("prefixes", prefixes_dict(alconna.prefixes))
    if not alconna.args.empty:
        res.put("args", args_dict(alconna.args))
    if alconna.options:
        res.put(
            "options",
            [
                option_dict(opt)
                for opt in alconna.options[:-3]
                if isinstance(opt, Option)
            ],
        )
        res.put(
            "subcommands",
            [
                subcommand_dict(sub)
                for sub in alconna.options[:-3]
                if isinstance(sub, Subcommand)
            ],
        )
    res.put("meta", ConfigTree(**asdict(alconna.meta)))
    if alconna.separators != (" ",):
        res.put("separators", list(alconna.separators))
    return res


def dumps(
    alconna: Alconna,
    output_format: Literal["hocon", "yaml", "json"] = "hocon",
    indent: int = 2,
):
    return HOCONConverter.convert(to_conf(alconna), output_format, indent=indent)


def dump(
    alconna: Alconna,
    path: str | Path,
    output_format: Literal["hocon", "yaml", "json"] = "hocon",
    indent: int = 2,
):
    _path = Path(path) if isinstance(path, str) else path
    with _path.open("w+", encoding="utf-8") as f:
        f.write(dumps(alconna, output_format, indent=indent))
