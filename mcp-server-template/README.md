# __DISPLAY_NAME__

__DESCRIPTION__

## Install

```bash
pip install __DIST_NAME__
```

## Connect a client

**Claude Code**

```bash
claude mcp add __DIST_NAME__ -- __DIST_NAME__
```

**Claude Desktop** (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "__DIST_NAME__": { "command": "__DIST_NAME__" }
  }
}
```

## Tools

| Tool | What it does |
|---|---|
| `echo` | Returns its input (a placeholder; replace with the real tools) |
| `server_info` | Reports the server's name and version |

## Documentation

- [`docs/README.md`](docs/README.md) — index of the user and contributor docs.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute.
- [`CHANGELOG.md`](CHANGELOG.md) — what changed in each release.
