# Standard 100-Point Short Video Score Rubric

Use this fixed rubric for every Chinese short-video forensic teardown unless the user provides a different explicit scoring system.

The rubric is intentionally stable across video types. Product launches, brand films, travel notes, oral explainers, course ads, and creator vlogs all use the same weights. The video category changes the evidence interpretation, not the scoring standard.

## Scoring Principles

- Score every video out of 100 using the same 10 first-level dimensions.
- Each deduction must cite concrete evidence: timestamp, frame, subtitle/SRT line, transcript line, visual absence, missing CTA, or source limitation.
- Do not give full credit for a dimension that was not verified.
- Do not silently change weights for different video categories.
- If evidence is missing or partial, apply the cap rules below.
- Include current score, target score after optimization, and priority lift order.

## Fixed Dimensions

| Dimension | Weight | Subcriteria |
|---|---:|---|
| 前3秒语言心理钩子 | 15 | Opening line has concrete benefit/conflict/contrast 4; target audience is clear 3; 0-3s visuals support the hook 3; subtitle/audio/edit emphasis sync 3; creates a continue-watching question or promise 2 |
| 选题/标题/封面承诺 | 10 | Target user is clear 2; title/cover promise is concrete 3; first frame matches the promise 2; topic has scarcity/pain/emotion/curiosity 2; platform fit 1 |
| 脚本结构与信息递进 | 12 | Hook 2; setup/background 2; conflict/problem 2; proof/case/story 3; conclusion 2; CTA 1 |
| 高光句音画同步 | 12 | 爆点句 2; 结论句 2; 反差句 2; 冲突句 2; 价值句 1.5; 情绪句 1.5; 结果句/CTA 1 |
| 视觉画面与审美 | 10 | Subject clarity 2; composition stability 2; color/light 2; scene/material quality 2; visual information density 2 |
| 拍摄与运镜 | 8 | Shot-size variation 2; stabilization/focus 2; camera movement serves emphasis 2; people/product/scene blocking 2 |
| 剪辑节奏与留存 | 10 | 0-10s pace 2; mid-video visual interrupts 2; cut points match spoken beats 2; information density control 2; transitions/SFX are restrained and useful 2 |
| 字幕与包装 | 10 | Subtitle readability 2; size/position/safe area 2; keyword emphasis 2; packaging hierarchy 2; platform UI/contrast risk 2 |
| 证据链与可信度 | 6 | Data/case/screenshot/on-site proof 3; identity/professional authority 2; claims are credible and not exaggerated 1 |
| 转化/关注/评论引导 | 5 | CTA clarity 2; low action friction 1; timing is appropriate 1; CTA emotion matches content 1 |

## Score Bands

- `90-100`: Benchmark execution. Worth direct replication, with only small optimizations.
- `80-89`: Strong execution. Core mechanism works; optimize local packaging, rhythm, or CTA.
- `70-79`: Content works, but hook, packaging, or retention has obvious weaknesses.
- `60-69`: Brand or information is valid, but short-video retention structure is weak.
- `50-59`: At least two major systems are weak: hook, proof, pacing, subtitles, or CTA.
- `<50`: Missing the core hook, visual evidence, transcript/audio evidence, or basic short-video structure.

## Hard Cap Rules

- No verified source video: total score is capped at `45`, unless the user provides transcript and frame evidence.
- No first 3 seconds evidence: 前3秒语言心理钩子 is capped at `5/15`.
- No audio/transcript/SRT evidence: 高光句音画同步 is capped at `5/12`.
- No verified screenshots/frames: 视觉画面与审美, 拍摄与运镜, 剪辑节奏与留存, and 字幕与包装 cannot receive full credit.
- Transcript only, no visuals: visual, camera, editing, and subtitle packaging dimensions are capped at half credit.
- Oral-only video with no B-roll/proof scenes: 视觉画面与审美 is capped at `7/10`, 剪辑节奏与留存 is capped at `7/10`.
- CTA missing: 转化/关注/评论引导 is capped at `2/5`.
- Source resolution cannot be verified: do not score source quality as a creative deduction, but cap visual/camera claims to inspected evidence.

## Report Requirements

Every report must include:

- A score table with all 10 fixed dimensions.
- Current score and target score.
- Evidence for each deduction.
- Priority lift order, sorted by expected score increase.
- Any cap rule that was applied.
