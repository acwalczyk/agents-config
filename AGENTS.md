# Maintaining agents-config

This repository manages selected personal AI configuration. Read README.md and
docs/migration.md before changing deployment behavior.

- Keep credentials, native authentication, transcripts, databases and machine state outside Git.
- Chezmoi is the configuration deployment owner. Preserve unmanaged settings.
- Default commands must inspect or preview. Applying configuration and updating
  native plugins are separate, explicit operations.
- Do not run setup against the real home directory as a test. Use temporary destinations.
- Preserve existing provider choices and permissions unless the user changes them.
- Keep project instructions and project skills owned by their projects.
- Developer workflows, custom skill design and cost optimization are subsequent work.

Validation: `make test` (Python 3.11+ and chezmoi 2.73.3+). Use `CHEZMOI=/path/to/chezmoi`
when the executable is not on PATH. Review the actual diff before committing.
