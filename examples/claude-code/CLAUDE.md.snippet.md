## Project dashboard (AgentWorkbench)

- The dashboard at `https://workbench.example.com` is the source of truth for the list of projects, tasks, ideas, notes and status. Credentials are in `~/.claude/agentworkbench.env`, usage is described in the skill `agentworkbench`.
- When working on a project: fetch the briefing first, tick off finished tasks, add new tasks and ideas, save lasting knowledge as notes, and write a log entry at the end.
- Do not keep separate to-do lists in notes or files. Documentation and credentials stay where they are; the dashboard only links to them.
- **The closing check is mandatory** (without being asked, before the last answer of a work session): go through the open tasks of the project and tick off every one that was finished in this session or is proven done on the system. Tick off only with evidence; if unsure, name the task in your answer instead. At the start, compare open tasks with the real state and tick off what is already done.
