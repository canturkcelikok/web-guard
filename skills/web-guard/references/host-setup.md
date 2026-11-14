# Host setup

Use the same complete web-guard folder on either host. No model API key, dual-model orchestration or paid scanner is required by the skill itself. Host tools/network, Python 3.10+ and authorized access determine available execution; a chat-only host cannot modify a remote server without a connection.

Claude Code: place the folder at ~/.claude/skills/web-guard/ (personal) or .claude/skills/web-guard/ (project). Invoke /web-guard https://example.com. Do not add a second same-named legacy command.

Codex CLI/IDE: place it at ~/.agents/skills/web-guard/ (personal) or .agents/skills/web-guard/ (project). Invoke $web-guard https://example.com or select with /skills. ChatGPT personal installation is managed separately; it does not install the skill on another computer.

Transfer the COMPLETE folder, preserving scripts/references. Ask the source host to copy the installed folder to an accessible local host directory, or ask explicitly for a packaged export to move across computers. Never claim another host was installed unless its filesystem was actually updated. A skill does not create an executable terminal command.

Examples:
- /web-guard https://example.com
- /web-guard https://example.com fix --repo /path/project --run /path/audit-run
- /web-guard https://example.com retest --run /path/audit-run
- $web-guard https://example.com --repo /path/project

Resume the same run and stable findings across hosts; transfer only redacted reports/state and authorized source. Keep credentials host-local. Keep one host model active unless the user changes it. Token count depends on code size, findings and host model.

Official references; consult when installation behaviour changes:
- https://code.claude.com/docs/en/skills
- https://learn.chatgpt.com/docs/build-skills
