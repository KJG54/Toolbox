# Watch Test Baseline

The migrated component suite initially exposed five baseline failures. They were repaired as
part of the approved Watch confirmation work:

1. Restored the generic public Claude MCP manifest required by the packaging contract.
2. Declared PyYAML as a development-test dependency because the agent-document validator
   explicitly parses YAML code fences.
3. Made the Playwright doctor unit test mock optional-package availability, so it tests the
   repair branch without downloading Playwright.

The complete Watch suite and the independent Toolbox suite must pass before the Toolbox
baseline is committed or pushed.
