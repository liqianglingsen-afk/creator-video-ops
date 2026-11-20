# 委托与证据 · editorial-0.6

在 brief 内冻结 commission、entry_type、audio_intent、action_required、purpose、target_duration、placements、constraints、shot_style 和 color_style。外层 audience、goal、entry 是简报的一部分。若要求保留时长，填写“保持原时长”。原改两次使用同一任务及适用项。后台表现另录真实数据。单项“0”须有观察依据，“待核”列缺什么，特别注明已确认不存在的独立封面与平台实显未知。

每个实际镜头在 criteria.shots 写 start/end（源秒数）、purpose、evidence、events。一个长镜头可有多个事件。必要时写 framing、motion、sound、graphics、replication 说明声画和可执行复刻。素材完整覆盖原片，可零台词、零问题。对重要判断注明帧、原声或转写。按需测量字体、对比度、层级、阅读时间、视觉焦点和手机缩略可读性。相同帧重复引用仍是一份证据。

hook 四项上限为 4/4/5/4，各填 score、evidence、time（源秒数，小于 3 及实际时长）。继续看理由和本窗口内的可信线索分别打分。payoff 写兑现位置。高分起点 14；其中看下去的理由至少 4，可信线索至少 3。允许有意识地保留谜底。弱开场要优化时给两个实质不同的动机、真实素材位置及具体剪法，一个保留原有叙事优势。每案记录 motive、beats、next_shot，beat 写成片 start/end、subject、picture、audio、caption；按实际节拍分段。无声或无字时如实写明。

发布封面、独立稿、首帧和设计候选分别登记。列表入口缺图、弱封面或专门委托时以不同点击理由提出两案。按传播与美学各 50 分，检查主体、具体利益点、标题与正文是否兑现、关键裁切。无字看视觉层级，无品牌要求看作品辨识度。设计应注明取帧、标题、焦点、构图、位置和失败条件，用 cover_variants.py 从可编辑 JSON 生成 A/B 实图与 180px 模拟预览，再核对目标版位。自动播放任务优先评价第一幅画面，无需凑列表封面。结尾按目标判定，教程能否复现、剧情能否收束、品牌能否记住、关注是否有未来价值、转化的利益和入口是否真实。

对涉及状态变化的片段写前提、触发时刻、参考、预期与实见。expected_state 和 observed_state 使用同一套状态名，sequence 写可核连续画面的 start/end。画面、屏显、图形和声音分别决定怎样处理。事实错误、误认、真实遮挡单列发布阻碍。每处自填 finding 须有 interval、track、dimension、evidence、action、acceptance、disposition（本次取舍）、score_review（受影响分数及理由）。同主题不同位置独立登记，首页可归组。改观察后同时复核分项和建议。同一后果在一个主责维度扣分。

十维分值继续用稳定字段名，语义依[量表](score-rubric.md)。缺某项时把该键从 marks 移到 pending，给原因；有证据再移回。复评和预测仅在基线完整时出正式总分。允许直接交部分报告。封面或开场的单项委托可单独提交设计稿、原图、源时码及校样，无需补一份整片评分。新量表为 creative-100-v2。


技术适用项在打分前指定。export_context 取平台发布、保留源规格或待核。规范未知时保留原始测量并标出待核项。更新同一成片的判断时可在 review 添加 --previous-review 旧报告.json，逐处说明已关闭的问题、证据变化和分项／建议如何处理。
保留或关闭历史观察时，closed_findings 按原问题 ID 填 evidence、score_review、disposition。对执行方向明确的发现，selected_edit 可写保留、微调、替换或删除，剪前快照会核对同一决定是否落在时间线上。
实片综合审片会密查开头、末尾、剪点、事实时段。字幕或运动边界可用 criteria.inspect_spans 追加 start/end；全片排查使用 --full-frame-scan。回看闪帧候选后在 frame_reviews 按源帧编号写 status（已核、有缺陷填须修、待核）和 evidence。
