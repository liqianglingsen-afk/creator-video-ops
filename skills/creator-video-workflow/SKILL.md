---
name: creator-video-workflow
description: Orchestrate an end-to-end Chinese creator-video workflow from public link or local file through source verification, video understanding, transcript and frame evidence, forensic teardown, Jianying/CapCut editing recommendations, and post-production QA. Use when users ask for a complete video workflow, want to turn a reference video into an executable improvement plan, or provide both a reference and a revised final video for teardown and quality scoring.
---

# Creator Video Workflow

Coordinate the existing specialist Skills. Do not reimplement their detailed analysis rules in this file.

## Route the Request

- Full reference-to-QA workflow: follow all available stages below.
- Reference teardown only: invoke `short-video-forensic-teardown`.
- Metadata, download, transcript, or frame extraction only: invoke `video-understanding`; use `youtube-video-analyst` or `viral-video-deep-dive` helpers when platform-specific handling is needed.
- Finished-video score only: invoke `postproduction-review`.
- Optimization requested and source available: render a separate first cut using existing material. For plan-only work or an unavailable export, mark final QA pending.

## Stage 1: Preserve the Source Chain

Record the exact user input before redirects or downloads. Distinguish the original URL/path, resolved platform URL, selected analysis source, probed media resolution, frame resolution, and subtitle source.

If a platform source cannot be obtained, ask for a local MP4 or screen recording. Never invent visual evidence.

## Stage 2: Build the Evidence Pack

Use `video-understanding` for metadata, transcript, dense 0–5 second frames, full-timeline frames, and local fallbacks. Use the YouTube transcript helper or Xiaohongshu probe only when relevant.

Follow [workflow-contract.md](references/workflow-contract.md) for stage status and artifact handoff.

## Stage 3: Produce the Forensic Teardown

Invoke `short-video-forensic-teardown`. Require the image-rich HTML report, first-three-seconds hook lab, timestamped shot timeline, highlight-line audio-visual sync, good-part replication cards, weak-part replacement cards, fixed score rubric, and report validators.

## Stage 4: Produce the Editing Plan

Convert findings into a priority-ordered execution list:

1. Must fix before publishing.
2. High-impact retention and clarity changes.
3. Packaging polish.
4. Optional experiments.

Use the [edit-plan contract](../short-video-forensic-teardown/references/edit-plan.md). Set a minimum of 85/100, choose a higher brief when applicable, and build a source-to-output cut list Codex can execute. Render and inspect a new file when asked to optimize. Specify new content only for a demonstrated gap after examining available material or reviewing a trial cut.

## 传播评分与修改排序 · v0.3.0

短视频评分、拆解及优化共用[传播与美学审片约定](../short-video-forensic-teardown/references/editorial-review.md)。先核目标受众、入口、前三秒承诺及兑现、结尾收益与真实承接，检查哪些镜头必须保留。按事实问题、目标瓶颈、证据和成本选 1–3 项。前台分别显示十维内容分、后期技术分、封面双轴分和发布前问题。按委托制作首选与挑战剪法或封面，复核手机预览与实际导出。单纯评分保留原片。

使用 Framecheck 0.3+ 的 `postscore brief` 创建底稿并由 Codex 依据实际审片填写，再用 `review --editorial` 或 `batch --editorial-dir` 生成报告。初次裸跑技术检查时传播判断待核。纯技术任务可直接交付；用户问传播/转化或综合评分时继续完成可验证的创意审片，包含内容百分制及封面证据。缺真实发布封面或转化组件时写待核，按当前素材提出候选。需要成交、关注或回访数据时用可选的 metrics_csv 导入。

## Stage 5: Review the Revised Final Video

When a revised video exists, invoke `postproduction-review` with the most relevant preset. For multiple files or a folder, use batch mode. Rescore content against the same ten dimensions and evidence caps when content is in scope. Report content and technical QA separately, with exact file, baseline, target and revised score for each. If either requested check falls short, revise recoverable cuts or document the remaining evidence and the minimum pickup. Link the cut, execution file, reports and outstanding items.

Treat platform download credentials as task-local authorization. Never place cookies, tokens, or downloaded copyrighted media in the plugin repository or generated public examples.

## Completion Rules

A full workflow is complete only when every requested stage has an artifact or a clearly stated blocker. A teardown report alone does not prove the revised video passed QA. A QA score without source provenance and report coverage does not prove a full teardown was completed.
