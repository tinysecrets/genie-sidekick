# Tools

Every specialist agent runs inside a **ReAct tool-use loop** (`agents/_loop.py`).
On each step the agent emits a JSON action — either a tool call or a `final` answer.

## Action format

```json
{"thought": "...", "tool": "fs.write", "args": {"path": "x.txt", "content": "y"}}
```

or to finish:

```json
{"thought": "...", "final": "<answer for Genie>"}
```

## Available tools

| Name | Args | Effect |
|---|---|---|
| `fs.read`    | `{"path": "<file>"}` | Read file contents. |
| `fs.write`   | `{"path": "<file>", "content": "<text>"}` | Write / overwrite. |
| `fs.list`    | `{"path": "<dir, optional>"}` | List entries. |
| `fs.glob`    | `{"pattern": "**/*.py", "base": "<dir, optional>"}` | Recursive glob. |
| `sh.run`     | `{"cmd": "<string>", "cwd": "<dir, optional>", "timeout": 60}` | Local shell. |
| `py.exec`    | `{"code": "<python>", "timeout": 30}` | Python subprocess. |
| `web.search` | `{"query": "<text>"}` | DuckDuckGo HTML, top 10. |
| `web.fetch`  | `{"url": "<https url>"}` | HTTP GET, text-extracted (≤8 KB). |
| `task.spawn` | `{"role": "<role>", "order": "<text>", "max_steps": 6}` | Recursive delegation. |

## Safety posture

By default the tools run with the user's local privileges — no sandbox. This is
intentional: the Super Key holder is sovereign and may treat their own machine as
they wish. If isolation is required, run the team inside the HP Pavilion's
VirtualBox snapshot (`infrastructure/virtualbox_sandbox.md`); the per-job
restore-to-pristine cycle gives you a fresh disposable VM every time.

## Extending

Add a new tool in three steps:

1. Implement `def my_tool(args: dict) -> str:` in `agents/tools/registry.py`.
2. Register it in the `TOOLS` and `TOOL_SCHEMAS` dicts.
3. (Optional) Document it here.

The agents will discover it automatically — `describe_tools()` enumerates the
registry at every step.
