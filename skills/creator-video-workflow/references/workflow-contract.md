# Workflow Contract

Track each stage as `complete`, `blocked`, `not_requested`, or `pending_user_revision`.

| Stage | Minimum evidence |
|---|---|
| Source acquisition | Original URL/path, resolved source, actual probed resolution, and any limitations |
| Video understanding | Transcript source, dense opening frames, timeline frames, and metadata |
| Forensic teardown | Validated HTML report with required contract markers and local evidence images |
| Editing plan | Priority, timestamp, operation, parameters, assets, and completion check for every action |
| Final QA | postscore HTML/JSON report for the revised file, coverage, score, and release verdict |

## Handoff Layout

Use one task directory when practical:

```text
outputs/<task-slug>/
  source.json
  transcript/
  frames/
  teardown.html
  editing-plan.md
  qa/
```

Existing specialist Skills may use their own filenames. Preserve their outputs and link them from the handoff instead of duplicating large files.

## Evidence Boundaries

- Page metadata resolution is not the downloaded stream resolution.
- Extracted frames are evidence only for the selected media source.
- Transcript text must identify whether it came from platform subtitles, OCR, Whisper, or page copy.
- Final QA applies to the exact revised file analyzed, not the reference video or an earlier export.
