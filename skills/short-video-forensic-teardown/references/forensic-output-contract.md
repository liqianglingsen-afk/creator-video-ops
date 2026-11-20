# 新版交付和校验

综合拆解使用 Framecheck 0.6 的 review --editorial --html --json 输出，沿用同目录同名 HTML/JSON。用关联的真实媒体标识与版次生成单条报告，包括目标与入口、实际镜头和事件、创作依据、逐项得分或待核原因、传播与美学、保留项、全部问题、优先建议、技术覆盖及后台数据状态。截图及声音以支撑判断为准，可额外附剪映教学或逐帧对照。需要新旧对照时交 revision-compare 输出。

```sh
python "<skill-dir>/scripts/check_report_contract.py" report.html --require-v06
python "<skill-dir>/scripts/check_report_layout.py" report.html
python "<skill-dir>/scripts/check_report_contract.py" plan/plan.html --revision-stage plan --require-v06
python "<skill-dir>/scripts/check_report_contract.py" comparison/comparison.html --revision-stage comparison --require-v06
```

用装有 postscore 的 Python 运行新版内容一致性校验，它按同一个 JSON 重新渲染并比对可见结果。计分、镜头及编辑建议有改动时更新底稿并重出，保持所有视图一致。旧模板和旧参数只用于复查对应历史版次。纯技术检测交实际技术结果与覆盖范围，专项封面或开场交其委托成果。
