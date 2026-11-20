# Creator Video Ops

面向中文短视频创作者的 Codex 插件，把视频来源获取、媒体理解、法医级拆解、剪辑修改建议和成片质检串成一条可追溯工作流。

## 包含的 Skills

| Skill | 作用 |
|---|---|
| `creator-video-workflow` | 总控入口，根据任务状态编排完整流程或路由到单阶段 |
| `video-understanding` | 获取公开视频元数据、下载/抽帧、字幕与多模态理解 |
| `short-video-forensic-teardown` | 前 3 秒钩子、镜头、剪辑、字幕、包装与音画同步的法医级 HTML 拆解 |
| `viral-video-deep-dive` | 兼容旧调用，并提供小红书等平台的来源质量探测 |
| `youtube-video-analyst` | YouTube 字幕获取与长视频分析补充 |
| `postproduction-review` | 调用 Framecheck / postscore-ai 对修改后的成片进行评分与报告生成 |

## 典型流程

```text
公开视频链接或本地视频
  → 来源与清晰度验证
  → 转录、抽帧和证据整理
  → 法医级拆解报告
  → 剪映/CapCut 可执行修改清单
  → 修改后视频
  → postscore-ai 最终质检
```

如果用户只要求拆解、字幕建议或成片评分，总控 Skill 会直接进入对应阶段，不强制跑完整流水线。

0.3.0 的十项内容权重直接相加为 100 分。新旧版本比较需按同一量表重评两份成片。短视频优化最低目标为 85/100。分析任务交付带源片与成片时码、执行参数及验收条件的剪辑单；执行任务优先用现有素材导出新版本。内容拆解和后期技术分分别复评。仅在素材有明确缺口时附最小补拍方案。详见[剪辑与复评约定](skills/short-video-forensic-teardown/references/edit-plan.md)。

传播审片、封面双轴评分、真实选帧与多画幅封面生成、同素材挑战剪辑、发布数据导入和校准方法见[新版操作约定](skills/short-video-forensic-teardown/references/editorial-review.md)。封面工具需 Pillow 和本地字体，跨工具审片需 Framecheck 0.3+。

## 0.4.0 全片修改与复评

优化前交付逐项预测与完整剪辑单，修改后交付相同量表的原改对照、品牌资产保留情况和版位 UI 校样。操作及依赖见[全片修改与原改复评](skills/short-video-forensic-teardown/references/full-revision.md)。需要 Framecheck 0.4+；旧单片报告继续可读。

## 依赖

- Python 3.10+
- FFmpeg / ffprobe
- 推荐安装 `uv`、`yt-dlp`
- 可选 `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`；没有云端模型时使用本地抽帧和字幕降级路径
- 最终成片评分需要安装 [`framecheck`](https://github.com/liqianglingsen-afk/framecheck) 仓库中的 `engine/`（postscore-ai）

平台链接可能受登录或反爬策略影响。插件不会携带 cookies、tokens 或下载素材；获取失败时应让用户提供本地 MP4。

## 验证

```bash
python path/to/plugin-creator/scripts/validate_plugin.py .
python path/to/skill-creator/scripts/quick_validate.py skills/creator-video-workflow
```

短视频 HTML 报告还必须通过插件内的 `check_report_contract.py` 与 `check_report_layout.py`。

## 0.5.0 封面、开场与产品展示

综合评分使用 Framecheck 0.5，分别核对独立封面、平台实显与候选，按四项证据计算前三秒，保护有辨识价值的镜头。主体误认和错误屏显进入发布前必改清单。见[字段与交付验收](skills/short-video-forensic-teardown/references/creative-evidence.md)。
