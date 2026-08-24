# Agent identity

Fleet-managed identity has two distinct models and cannot be changed after it is set.

Fixed credentials suit a centralized migration service, Slack/Teams bot, or scheduled agent. All users act through the owner's connected service accounts, so restrict repository scope and preserve actor information in Fleet traces.

User credentials suit developer assistants where GitHub authorization and audit must follow the invoking user. Each user connects their own account. Do not combine fixed ShiftIQ MCP authentication with an assumption that it automatically enforces per-user GitHub permissions; the Fleet GitHub integration and repository policy must do that.
