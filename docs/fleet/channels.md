# Channels

Fleet Chat is the primary interactive engineering interface. Slack and Microsoft Teams channel connections are Fleet-managed and require fixed agent identity.

Example: `@ShiftIQ analyze org/app for react-hooks; do not modify files.` Status prompts should remain read-only. Destructive actions must enter Fleet's tool approval experience; do not accept a plain channel message as authorization.

For Slack, create/link the app through Fleet Integrations, invite it to the channel, add only required Slack tools, and verify approval buttons in a test thread. Configure Teams through the agent Channels drawer and apply equivalent tool/identity restrictions.
