# 封面、前三秒与镜头取舍 · 0.5

从原视频执行 `postscore brief input.mp4 --output notes.json`。填完八个环节、十维内容分、封面图与本页的 criteria 后，执行 `postscore review input.mp4 --preset short_social --editorial notes.json --json --html --output-dir review`。审片人对画面事实负责。评分器复算分项、检查矛盾、汇总发布阻碍。纯技术检查直接用 review。历史稿保留原分和原 schema。

## 先确认要观众记住什么

goal 写商业目标，criteria.primary_task 写影片要介绍或证明什么，secondary_angle 写辅助切口，reveal_order 写对象首次出现和后续展示的顺序。先确定观看入口、受众和主动作。围绕主任务登记有独特价值的镜头，包括产品体量、结构或材质、品牌、使用过程、可信结果与动态收束。生活方式片按其真实叙事资产登记。

## 封面

cover_source.independent 可填有独立封面、无独立封面或待核。用户确认没有独立封面，显示 N/A。仅收到 MP4，填待核。cover_source.displayed 写独立封面、平台选帧或待核，并以发布设置或列表截屏说明来源。正式设计稿尚无发布凭据时，covers.role 填独立封面。已知平台实际使用的图填发布封面，即使它就是首帧，也须有实际设置的证据。首帧、候选仅在各自栏评分。零分是已核的实得分。十维内容用已证实的入口表达与正文证据，避免因同一缺失重复扣分。

每张图的 previews 用与 covers 完全相同的名称。source 写来源或帧时码，size 写实际检查的缩略宽度和版位，subject 填正确、错误或缺失、待核，benefit 填可辨、不清、待核，topic 写题目是否具体、真实且有区别。传播和美学分别评分，各 50。缩至 180px 核对产品、点击收益、标题新意和层级；再检查实际版位裁切。产品认错或利益不可辨会淘汰，保留自然光色等确实成立的分项。首帧得分只用当帧能见的信息；后文兑现单列，不能补首帧的识别分。

弱或缺封面时，cover_plans 至少两种动机。每个包含 motive/source_frame/headline/crop/focus/placement/rationale/failure。做封面优化时用 cover_variants.py 交可编辑输入、A/B 成图和手机预览，标明实显或模拟。打开输出目录 preview.html 可对照 180px 模拟列表卡片。variants 的 layout 可选 photo（原帧满版）或 panel（独立文字区），focus_x/focus_y 与 text_x/text_y 均为 0–1 的相对位置，source_crop 可按左、上、右、下相对边界裁掉烧录字幕，motive 写点击理由。既有方案继续可渲染。现有素材能支持哪种主张、哪项缩小后会读不清，写清验收与淘汰条件。

## 前三秒

hook 用“主体与动作、受众相关、继续观看理由、前三秒可信线索”四个键，每项写 score 和 evidence（源秒数与当时可见或可听的证据）。满分依次为 4、4、5、4。先分别打分再相加写入十维首项。高分档从 14/17 起，继续观看理由至少 4、可信线索至少 3，并在 payoff 写明正文兑现的时码。它是编辑量表锚点，线上效果单用同版位实测。一般痛点问句即使受众清楚，也应说清矛盾是否可见、答案是否已被猜到。

综合拆解给首选和备选。弱钩子须在 openings 中完整给出两种观看动机；强钩子可把原剪法作为对照。每种写 motive、beats（按 0–1、1–2、2–3 秒顺序的三个对象，各含 subject/picture/audio/caption）与 next_shot。首选保护原有正式亮相与递进。提前揭示若能靠画面、字幕或声音交代清楚，再看静音是否也能认出对象。identity.sound_on 和 muted 分别选清楚、误认、待核，写 evidence 和 fix。

## 分轨保护、功能状态与交付

assets 每项写 name/source/value/picture/display/graphics/sound/output/reason/loss。画面可保留、微调、替换、删除；注明源与成片时段、取舍、字幕能否单修。loss 取保留价值、有据取舍、无据丢失。确实不适用时填 no_assets_reason。剪前剪辑单 protect 逐名称承接资产；时间线每段填 screen（可注明无屏显），其余轨继续按全片方案填写。不能以技术扣分或修字幕省事为由直接删除好镜头。

displays 每项填 time/action/expected/observed/reference/timing_reference/status/timing/fix。参考样张只证明数字字形；用同型号同模式连续实拍核复位时刻。保留各组零值、单位、图标、透视、亮度及运动；原片信息不足时提出最小补拍单。机器无屏或本片无相关状态，填 no_display_reason。产品状态错误、应归零却擦空、主体误认、价值镜头无据丢失，均进入发布前须改。

首页列内容、技术、封面来源、四项钩子与全部阻碍。标准 HTML 模板的 cover_status、release_status 直接取评分器，hook_marks 写四个实得分，用“ / ”相连。执行 check_report_contract.py --require-current-rubric --require-v05。成对复评保留两位评审原始分数。盲审 observations 与复评 disputes 逐项写 time、issue、evidence、decision（须修／待核／已裁决）。有分歧时逐镜裁决。新版盲审表另填 hook 的四项与 payoff，评分器核对其合计。两版均使用同版规则重新评分，历史自评和旧盲审单独标记。缺点击或留存数据单列待核。
