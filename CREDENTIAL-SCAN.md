# Clean export scan

29 exported files were scanned offline before this report was added. No real credentials
were detected by the checks performed.

- Checked for private-key blocks, common GitHub/AWS/Google/Slack token formats, JWTs,
  credential-bearing URLs and quoted credential assignments.
- The only pattern finding was the dummy `user:password@host` SQL connection example
  in `.env.example`; it is a documentation placeholder.
- Compared the export with six known legacy connection/account values from the source
  repository's HEAD configuration. None appeared in the export.
- Verified that the export excludes Git history, Java sources, virtual environments,
  logs, reports, browser drivers, compiled files and Python package build metadata.
- Verified source/copy hashes for all 27 unchanged files. README.md and VALIDATION.md
  were adjusted to describe an export without an installed environment or report artifacts.

These are local pattern and known-value checks, not a guarantee that every possible
secret format will be detected. No files were uploaded to a scanning service.

At the time of this scan, no repository had been initialized and nothing had been
committed or pushed. The clean export is intended for a separate Git repository,
without the parent workspace's history.
