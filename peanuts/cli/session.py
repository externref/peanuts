# MIT License

# Copyright (c) 2024 sarthak

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import json
import os
import typing

import tabulate
from rich.console import Console

from src.common import DataTypeConflictException, display_syntax
from src.main import Instance
from src.schema import SchemaTypeToPyT

if os.name != "nt":
    # readline module enables arrow actions etc in the terminal stdin
    import readline  # type: ignore  # noqa: F401


class Session:
    dbname: str
    app: Instance
    console = Console()

    def __init__(self, dbname: str) -> None:
        self.dbname = dbname
        self.app = Instance(dbname)

    @staticmethod
    def map_insert_to_json(items: dict[str, SchemaTypeToPyT]) -> str:
        entries = {}
        for key, tdata in items.items():
            ind = Session.console.input(f"[cyan][bold]{key} (type: {tdata}): [/bold][/cyan]")
            if tdata == SchemaTypeToPyT.STRING:
                entries[key] = ind
            else:

                def verify_array(t: type, arr: list[typing.Any]) -> None:
                    for item in arr:
                        if not (isinstance(item, t)):
                            raise DataTypeConflictException(str(t), str(type(item)))  # type: ignore

                data: typing.Any = json.loads(ind)
                if tdata in (
                    SchemaTypeToPyT.A_BOOL,
                    SchemaTypeToPyT.A_FLOAT,
                    SchemaTypeToPyT.A_INTEGER,
                    SchemaTypeToPyT.A_STRING,
                ):
                    if tdata == SchemaTypeToPyT.A_STRING:
                        assert verify_array(str, data)
                    elif tdata == SchemaTypeToPyT.A_INTEGER:
                        assert verify_array(int, data)
                    elif tdata == SchemaTypeToPyT.A_FLOAT:
                        assert verify_array(float, data)
                    elif tdata == SchemaTypeToPyT.A_BOOL:
                        assert verify_array(bool, data)
                elif tdata == SchemaTypeToPyT.BOOL and not isinstance(data, bool):
                    raise DataTypeConflictException("bool", str(type(data)))  # type: ignore
                elif tdata == SchemaTypeToPyT.INTEGER and not isinstance(data, int):
                    raise DataTypeConflictException("int", str(type(data)))  # type: ignore
                elif tdata == SchemaTypeToPyT.FLOAT and not isinstance(data, float):
                    raise DataTypeConflictException("float", str(type(data)))  # type: ignore
                entries[key] = data

        return json.dumps(entries)

    def run_command(self, action: str, restargs: list[str]) -> None:
        if action == "!create_schema":
            self.app.add_schema(restargs[0], " ".join(restargs[1:]))
        elif action == "!drop_schema":
            self.app.drop_schema(restargs[0])
        elif action == "!load_cache":
            if len(restargs) == 0:
                for schema in self.app.schemas.values():
                    schema.cache.load()
            else:
                for sname in restargs:
                    try:
                        self.console.print(f"⌛[blue]Loading {sname} ...")
                        self.app.schemas[sname.strip()].cache.load()
                    except KeyError:
                        self.console.print(f"[red]No schema named [bold]{sname}[/bold] found.")
        elif action == "!display_schema":
            if len(restargs) != 1:
                self.console.print(display_syntax("!display_schema", "!display_schema <schema_name>"))
                return

            assert self.app.schemas.get(restargs[0]), f"No schema named [bold]{restargs[0]}[/bold] found"
            print(
                tabulate.tabulate(
                    self.app.schemas[restargs[0]].display_dict(),
                    headers="keys",
                    tablefmt="rounded_grid",
                    numalign="right",
                )
            )

        elif action == "insert":
            assert self.app.schemas.get(restargs[0]), f"No schema named [bold]{restargs[0]}[/bold] found"
            if len(restargs) == 2:
                try:
                    items = self.map_insert_to_json(self.app.schemas[restargs[0]].configs)
                    self.app.schemas[restargs[0]].write(restargs[1], items)
                except DataTypeConflictException as e:
                    self.console.print(f"[red]{e}")
                except json.decoder.JSONDecodeError:
                    self.console.print("[red]Invalid Input.")
                return
            self.app.schemas[restargs[0]].write(restargs[1], " ".join(restargs[2:]))
        elif action == "select":
            assert self.app.schemas.get(restargs[0]), f"No schema named {restargs[0]} found"
            try:
                data = self.app.schemas[restargs[0]].read(restargs[1])
                print(tabulate.tabulate(([k, v] for k, v in data.items()), tablefmt="rounded_grid"))
            except FileNotFoundError:
                self.console.print(f"[red]No data with ID {restargs[1]} found.")

        elif action in ["!q", "!quit", ":q", ":quit"]:
            raise KeyboardInterrupt
        else:
            self.console.print("[red]Invalid Command, use [bold]!help[/bold] to get a list of available commands.")

    def run_session(self) -> None:
        try:
            self.console.print(
                f" [bold][cyan]Welcome to peanuts 🥜, Connected to database: [bold]{self.dbname}[/bold][/cyan][/bold]"
            )
            while True:
                cmd = self.console.input("[bold][green]#[/green][/bold] ").strip()

                while not cmd.endswith(";"):
                    cmd += " " + self.console.input("[bold][green]>[/green][/bold] ").strip()
                vals = cmd.strip(" ;").split()
                args = [arg.strip() for arg in vals if arg != " "]
                try:
                    self.run_command(vals[0], args[1:])
                except AssertionError as e:
                    self.console.print(f"[red]{e}")
        except KeyboardInterrupt:
            self.console.print("[green]Thanks for using [bold]peanuts[/bold]!")
