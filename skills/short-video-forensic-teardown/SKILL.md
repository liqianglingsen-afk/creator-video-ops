---
name: short-video-forensic-teardown
description: Use for Chinese short-video teardown, scoring, cover and opening analysis, or an executable CapCut/Jianying edit plan grounded in timestamped footage. Produces evidence-backed Chinese HTML unless text only is requested.
---

# 短视频拆解与评分 · 0.6.0

先按[委托与证据约定](references/creative-evidence.md)确定受众、入口、期望结果、时长和素材。有缺项先做可核部分。只做技术质检走 postproduction-review。只设计封面或开场时交对应设计成果。只给方案时交剪前快照，执行改剪时才另存成片。批量委托逐片建底稿。

1. 保存原始链接、实际媒体及其来源。检查实际时长、分辨率、声音和字幕。按真实剪点填镜头，在长镜头内记动作和揭示事件。可按需使用 video-understanding、字幕测量脚本及[剪映参数参考](references/jianying-ops.md)。用正常速度看片，针对声画关系再分轨复看。
2. 用 Framecheck 0.6 的 `postscore brief input.mp4 --output notes.json` 生成底稿。先定简报，再用实片填写十维内容、适用的封面、开场、结尾与保留项。按[评分量表](references/score-rubric.md)给证据、得分及上限。证据不足写 pending。开头可信线索回到源帧，不能用结尾倒推。
3. 综合报告使用 `postscore review input.mp4 --preset short_social --editorial notes.json --html --json`。图文、逐镜、分项、优先建议和保留项从同一份结果生成。用户需要全片排查闪帧时加 `--full-frame-scan`，逐个回看候选。改剪时密查开尾、剪点、文字及动作边界。按[交付与校验](references/forensic-output-contract.md)核对。
4. 有值得动的部分，按实际影响选 0–3 项，发布阻碍另外列全。先保护表演、动态、构图、声音、文字语义和证据。给[全片方案与标准复评](references/full-revision.md)，包含源至成片的完整时间线、首选方案及预测区间。低于目标时先查现有素材，再针对已证明缺口提出最小增补。复刻教学仅对值得保留或用户指定的片段给[剪映操作](references/jianying-ops.md)。
5. 默认交可打开的图文 HTML 和对应 JSON。原片位置、内容分、按简报技术分、真实封面状态、发布阻碍和保留项能在报告中找到。需要预测或原改复评时同时交对应快照或对照表。线上传播表现用真实后台数据和窗口另列。
