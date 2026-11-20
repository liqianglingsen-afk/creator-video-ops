# Workflow Contract

Track each stage as `complete`, `blocked`, `not_requested`, or `pending_user_revision`.

| Stage | Minimum evidence |
|---|---|
| Source acquisition | Original URL/path, resolved source, actual probed resolution, and any limitations |
| Video understanding | Transcript source, dense opening frames, timeline frames, and metadata |
| Forensic teardown | Version-matched HTML/JSON, actual shots and evidence supporting each conclusion |
| Editing plan | Source and output timecodes, existing assets, executable operations and checks; pickup brief only for an evidenced gap |
| Final QA | Exact export, baseline and revised score per requested rubric, target ≥85, technical HTML/JSON, remaining gap |

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
