# Standard 100-Point Short Video Score Rubric

Use this fixed rubric for every Chinese short-video forensic teardown unless the user provides a different explicit scoring system.

The rubric is intentionally stable across video types. Product launches, brand films, travel notes, oral explainers, course ads, and creator vlogs all use the same weights. The video category changes the evidence interpretation, not the scoring standard.

## Scoring Principles

- Score every video out of 100 using the same 10 first-level dimensions.
- Each deduction must cite concrete evidence: timestamp, frame, subtitle/SRT line, transcript line, visual absence, missing CTA, or source limitation.
- Do not give full credit for a dimension that was not verified.
- Do not silently change weights for different video categories.
- If evidence is missing or partial, apply the cap rules below.
- 新报告采用 `creative-100-v1`。十项实得分直接相加，应用有依据的总分封顶后，以精确值比较目标。84.99 未过线，85.00 达到默认线。未标版本的 0.2.0 报告仍按原始分 × 100 / 98 解读。比较两次剪辑时，以同一版量表分别审看原片与新导出。
- 优化目标最低 85/100，更高目标按简报。分列原版、预估与实际导出复评。已有高分版本须查改后有无退步。评分采用下表固定权重，宣传方式与行动证据按片子目的解释。
- 每个子项从零至所列上限计分。缺失或相反为零，部分实现按可见证据给部分分，完整且在目标版位可复核才给满分。记录主要扣分的时码、文案或源帧；同一缺陷只扣其主责项，另一个维度可交叉引用。

## Fixed Dimensions

| Dimension | Weight | Subcriteria |
|---|---:|---|
| 前3秒语言心理钩子 | 17 | 首秒识别主体与动作 4；对目标受众具体相关 4；继续观看的理由 5；到第 3 秒已有可信线索 4 |
| 选题/标题/封面承诺 | 10 | 受众与场景 2；标题或入口表达具体价值 3；首帧承接 2；正文兑现入口承诺 3 |
| 脚本结构与信息递进 | 12 | 问题或情境清楚 3；信息与因果递进 4；关键回报放置合理 3；收束完整 2 |
| 高光句音画同步 | 8 | 关键语句或动作与画面同义 3；强调时点对齐 3；读数或结果给足辨认时间 2 |
| 视觉画面与审美 | 10 | 主体与构图 3；光色与质感 3；场景、道具和品牌气质 2；镜头间视觉一致 2 |
| 拍摄与运镜 | 6 | 景别与视角说明关系 2；对焦与稳定 2；运动或固定机位服务动作 2 |
| 剪辑节奏与留存 | 10 | 首次兑现所需时间 3；中段信息密度 3；剪点连续与呼吸 2；结尾时长合适 2 |
| 字幕与包装 | 8 | 手机端文字可读 2；层级与注意力 2；安全区与遮挡 2；字体、字卡及动效一致 2 |
| 证据链与可信度 | 9 | 关键主张与可查事实吻合 4；有可辨认的实证或叙事依据 3；限制条件清楚 2 |
| 转化/关注/评论引导 | 10 | 目标行动和观众收益匹配 3；下一步清楚 3；入口可用且低摩擦 2；时机自然 2 |

高光同步关注语义和时点。纯视觉片可核对动作、关键字卡与结果的对应。无需为凑分硬加口播或转场。封面独立审美另评，内容的入口项只评选题与承诺。缺真实封面时记录已核的标题、首帧及正文，封面特有判断标待核。成交片查商品承接，涨粉片查持续关注的收益；品牌片可按简报约定的品牌识别与回想线索给行动项评分，剧情片可用明确的情绪回收或真实的追看理由。提前写下该片希望观众带走什么，用结尾盲看来复核。

## Score Bands

- `90-100`: Benchmark on observed creative dimensions. Check for material factual errors and unusable action paths before recommending publication.
- `80-89`: Strong execution. Core mechanism works; optimize local packaging, rhythm, or CTA.
- `70-79`: Content works, but hook, packaging, or retention has obvious weaknesses.
- `60-69`: Brand or information is valid, but short-video retention structure is weak.
- `50-59`: At least two major systems are weak: hook, proof, pacing, subtitles, or CTA.
- `<50`: Missing the core hook, visual evidence, transcript/audio evidence, or basic short-video structure.

## Hard Cap Rules

- No verified source video: total score is capped at `45`, unless the user provides transcript and frame evidence.
- No first 3 seconds evidence: 前3秒语言心理钩子 is capped at `5/17`.
- For a sound-dependent highlight without audio/transcript/SRT evidence: 高光句音画同步 is capped at `4/8`.
- No verified screenshots/frames: 视觉画面与审美, 拍摄与运镜, 剪辑节奏与留存, and 字幕与包装 cannot receive full credit.
- Transcript only, no visuals: visual, camera, editing, and subtitle packaging dimensions are capped at half credit.
- For a talking-head or a fixed-camera scene, evaluate clarity, rhythm and the evidence required by the claim; a single shot may provide the whole demonstration.
- Where an explicit action is required but absent: 转化/关注/评论引导 is capped at `2/10`.
- Source resolution cannot be verified: do not score source quality as a creative deduction, but cap visual/camera claims to inspected evidence.

## Report Requirements

Every report must include:

- A score table with all 10 fixed dimensions.
- Current score and target score.
- Evidence for each deduction.
- The 1–3 most consequential changes and the shots to preserve. Mandatory review of the first three seconds and the ending. Rank misleading claims or broken action paths first, then the bottleneck for the stated goal; use strength of evidence, edit cost and expected score lift as tie-breakers.
- Any cap rule that was applied.
