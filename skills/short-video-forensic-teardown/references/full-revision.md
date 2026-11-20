# 短视频全片修改与原改复评 · v0.6.0

新综合评分、剪前保护和复评须同时执行[0.6 委托与证据约定](creative-evidence.md)。

仍采用 creative-100-v2 十维内容量表，最低目标为 85。修改依据是观众任务和整条片的声画效果。用户只委托评分时保留成片；委托剪辑时，把下列步骤做完并交付实际导出与标准原改报告。命令需 Framecheck 0.6+。编辑器、已核操作和具体素材根据项目选择。

## 剪前

先用相同业务目标对原片完成 `postscore review --editorial`，取得含十维评分的 JSON。分析与修改建议从同一个入口建底稿：

```sh
postscore revision-init original.mp4 before.json --output draft.json
postscore revision-plan original.mp4 before.json draft.json --output plan-v1
```

两条命令之间由 Codex 按实片填写 draft。forecast 的每个维度给 low、expected、high、basis、confidence。写绝对分，体现可能退步项和成立条件；软件逐维限幅并合计。目标与预估各自列示，方案低于目标也可提交，next_if_short 交代如何补差。技术分需导出实测。用 `check_report_contract.py plan.html --revision-stage plan --require-v06` 验收，归档 plan.json 和 plan.html 后再剪，方案变动生成新快照。无剪前记录的历史片使用 forecast_context=历史回放、forecast={}，不得补造预测。

timeline 从原片首帧覆盖到末帧，每段 source、destinations 使用 start/end 秒数；action 取保留、微调、替换、删除。分别写 picture、sound、graphics、reason、acceptance。删除的 destinations 为空；重用及转场按实际成片位置列出。多来源素材在 picture/sound 写明文件、轨道和入出点。完整单之外首页仍突出最多三项关键修改。仅有压制成片时核实烧录字与混音可否局部修复；先试现有素材，确有缺口才编补拍单。

protect 数组逐项填 name、kind、source、value、handling。kind 可取动态运镜、原字幕、品牌声音、表演动作、音乐落点、其他。纳入用户点名的好镜头，分别保护动态展示、原字幕和声音。动镜不能用同主体静帧算作保留。删换时给失去的价值和可执行的保留版；无值得单列项时如实写 no_assets_reason。

剪前即填写 packaging_plan 三项。行动收益写明受众为什么愿意迈出这一步及真实承接；手机易读性写屏上原文、出现时长和阅读次序；画面美感写构图、字体、色彩和字幕与镜头运动的配合。placement_plan 每个目标版位各列 platform、placement、ui_state、reference、layout、acceptance。缺真实平台截图时，在 reference 说明现有示意及待补实证，写明文字、动作和主体如何避让；验收时再对实际导出套版。

## 执行与评分

```sh
postscore revision-render original.mp4 plan-v1/plan.json --output cut-v1 --exec python edit.py --source '{source}' --output '{output}'
postscore revision-blind cut-v1/edited.mp4 --goal '沿用原片的业务目标' --brief notes.json --output blind.json
postscore revision-audit plan-v1/plan.json cut-v1/edited.mp4 --output audit.json
```

edit.py 是项目的真实剪辑脚本，两个占位参数由工具替换。也可直接指定 FFmpeg 参数。receipt.json 把实际导出绑定到方案和两份媒体指纹。手工导出可以复评，缺导出凭据时标明预测偏差待核。提供原片、改片、播放位置和原改关键连续帧；做动镜判断须看运动轨迹、拍点及声音。仅靠帧差标记疑点。

只将改片、业务目标与盲审表交给独立评审，隐藏原片、自评分、目标线和预测；评审写 reviewer 及十项时码依据。不具备独立评审时用自评。新导出须重新生成审片文件并用原预设、版本及抽样设置运行 `postscore review --editorial`。历史报告缺抽样配置时允许读取，保留技术可比性待核。

audit 的 protected 按每个保护项填 status（保留、替换已核、丢失、待核）、output 秒数范围或 null、evidence、tradeoff。timeline_check 逐段对照新导出，明确批准变更及其余问题。packaging 固定三项：行动收益、手机易读性、画面美感。每项分别填 status（已核、待核、须修）与 evidence。一次正常播放后，测试观众能否说出关键数值、动作和对象；没有真实受众结果时标明手机模拟或编辑判断。原改并排检查主体、层级、光色与品牌字幕节拍。单独复核行动提示的价值及其对画面和阅读的影响。

## 平台 UI 校样

每个实际版位与状态单独写 placements，记录 platform、placement、ui_state、source（版位实证或示意）、reference（相对 audit 的参考图）、reference_date、coverage_checked。将参考图裁切并对齐到**视频显示画布**。zones 按实际 UI 给出归一化框 x/y/w/h。tracks 覆盖关键文案、图标、状态变化和主体轮廓，记录 name、keys、end（秒），每个 key 有 time 和同样的框。动画用 linear 线性轨迹，阶跃用 hold；旋转、非线性运动增加关键帧，并回看极值、进出场与每次状态切换。用真实帧时码逐帧检查标注轨迹，报告提供首次相交时码、干净帧、带 UI 校样和当前帧试移坐标。覆盖全片后由审片者标记 coverage_checked。只有真实来源和已查范围均满足才能判通过。示意可用于压力测试，缺实际版位时在 pending_placements 写明缺哪种截图、状态和要验的元素。

示例（数值为夹具，不能当通用平台安全线）：

```json
{"platform":"测试平台","placement":"竖屏信息流","ui_state":"商品组件展开","source":"示意","reference":"preview.png","reference_date":"2026-11-20","coverage_checked":false,"zones":{"商品栏":{"x":0.0,"y":0.8,"w":1.0,"h":0.2}},"tracks":[{"name":"行动提示","keys":[{"time":1.0,"x":0.08,"y":0.76,"w":0.6,"h":0.08}],"end":2.5,"interpolation":"hold"}]}
```

## 标准交付

写 reviewer、review_mode、variance、next_edit；独立表、导出凭据分别填 blind_sheet、render_receipt，相对 audit 文件。分别列出分歧、关键退步、未验入口及下一轮，保留原始分与评级。

```sh
postscore revision-compare plan-v1/plan.json original.mp4 cut-v1/edited.mp4 after.json audit.json --output comparison-v1
python "<skill-dir>/scripts/check_report_contract.py" comparison-v1/comparison.html --revision-stage comparison --require-v06
```

分析和执行共用同一份剪前快照；单条 QC 只是复评附件。原片拆解主报告链接 plan.html；按方案修改后的主报告交付 comparison.html、comparison.json 和视频。内容过线也要检查事实、保护项、包装、版位碰撞及自评/盲审的过线分歧。缺平台数据标待核，盖住产品或误导观众的版本标须改。

新版 cut-plan-0.6 的 decisions 用首页问题 ID 关联 timeline 行号（从 0 起），每行记录实际采用的操作和理由；改观察时同步重算受影响的分数及建议。inputs 以名称为键写 path、role、sha256；uses 逐项写 asset、source 时段（静态资源可空）、output 时段。revision-render 中用 {asset:名称} 引用每个外部影音素材，导出前后复核指纹。placement_plan.elements 按元素名列必需的成片时段数组，校样逐一覆盖。独立评审跨线时以 observations 的 issue/time 匹配裁决；同时按有分差的维度以“评分分歧”为 time 逐一裁决。
新方案的 route 写现有素材剪辑、保留原版或最小增补。预估仍低于目标或首选需要增补时，在 pickups 中给 searched（查过的素材）、attempted（试过的剪法）、gap、minimum（最少新增什么）、destination（成片区间）和 acceptance。区分本次方案与达不到目标的补充备选。
