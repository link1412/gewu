# 逐镜说明

全片 34 镜,33.12 秒,828 帧,1920×1080,25 fps。片序以 `v2/cut.json` 为准。做法和替代品来自各脚本开头的说明和 `v2/SHOTS.md`、`v2/IMAGERY.md`。怎么渲染、和片子比的结果见 [`RENDER.md`](RENDER.md)。

| # | 镜 | 字幕 | 秒 | 脚本 |
|---|---|---|---|---|
| 01 | [墨晕](#01-墨晕) |  | 1.4 | `s38_richu.py` |
| 02 | [曜变](#02-曜变) |  | 1.52 | `s02_yaobian.py` |
| 03 | [印泥](#03-印泥) |  | 0.52 | `s05_yinni.py` |
| 04 | [钧窑](#04-钧窑) |  | 0.44 | `s06_junyao.py` |
| 05 | [磁青](#05-磁青) |  | 0.56 | `s07_cijing.py` |
| 06 | [银杏](#06-银杏) |  | 1.64 | `s09_ginkgo.py` |
| 07 | [剔红](#07-剔红) |  | 1.0 | `s61_tihong.py` |
| 08 | [豇豆红](#08-豇豆红) |  | 0.72 | `s11_jiangdou.py` |
| 09 | [苏绣](#09-苏绣) |  | 1.16 | `s59_suxiu.py` |
| 10 | [走马灯](#10-走马灯) |  | 1.2 | `s54_zoumadeng.py` |
| 11 | [折扇](#11-折扇) | 苟日新 | 0.88 | `s15_zheshan.py` |
| 12 | [荔枝](#12-荔枝) | 苟日新 | 0.72 | `s16_lizhi_v1.py` |
| 13 | [点翠](#13-点翠) | 苟日新 | 0.8 | `s55_diancui.py` |
| 14 | [打铁花](#14-打铁花) | 苟日新 | 1.0 | `s14_datiehua.py` |
| 15 | [油纸伞](#15-油纸伞) | 日日新 | 0.96 | `s66_xieyang.py` |
| 16 | [螺钿](#16-螺钿) | 日日新 | 1.08 | `s46_luopan.py` |
| 17 | [红灯笼](#17-红灯笼) | 日日新 | 0.52 | `s20_denglong.py` |
| 18 | [剪纸](#18-剪纸) | 日日新 | 0.4 | `s24_jianzhi.py` |
| 19 | [南红](#19-南红) | 又日新 | 1.36 | `s63_nanhong.py` |
| 20 | [金箔](#20-金箔) | 又日新 | 0.36 | `s27_jinbo.py` |
| 21 | [德化白瓷](#21-德化白瓷) | 又日新 | 0.52 | `s28_dehua.py` |
| 22 | [荷花](#22-荷花) | 又日新 | 1.64 | `s39_cand.py` |
| 23 | [螺钿竹](#23-螺钿竹) | 又日新 | 0.44 | `s19_luodian.py` |
| 24 | [狂草](#24-狂草) | 又日新 | 0.44 | `s35_kuangcao.py` |
| 25 | [一滴](#25-一滴) | 又日新 | 1.44 | `s76_yidi.py` |
| 26 | [油纸伞·黑](#26-油纸伞黑) | 又日新 | 0.96 | `s73_heisan.py` |
| 27 | [孔雀羽](#27-孔雀羽) | 又日新 | 1.28 | `s45_kongque.py` |
| 28 | [南珠](#28-南珠) | 又日新 | 1.08 | `s36_nanzhu.py` |
| 29 | [黄花梨](#29-黄花梨) | 又日新 | 0.52 | `s30_huali.py` |
| 30 | [青花](#30-青花) | 又日新 | 0.52 | `s50_qinghua.py` |
| 31 | [金鱼](#31-金鱼) | 又日新 | 0.56 | `s37_jinyu.py` |
| 32 | [珐琅](#32-珐琅) | 又日新 | 0.4 | `s49_falang_v1.py` |
| 33 | [木炭](#33-木炭) | 又日新 | 1.44 | `s69_mutan_raw.py` |
| 34 | [日出](#34-日出) |  | 3.64 | `s38_richu.py` |

## 01 墨晕

不用 Blender:numpy 的灯箱模型,光 = 柔和灯位 × 宣纸与墨层的透过率,灯从纸后升起。笔触用到达时间(速度场上的最短路径)生成,不解流体;颜料向前沿变薄并留潮线,碳滞后。走墨用 Lucas-Washburn 的 sqrt(t) 读同一到达时间场,干墨有光泽。与 s38 同一脚本的 shot1,31 帧。

**解算:** 笔触到达时间(速度场最短路径),Lucas-Washburn sqrt(t),numpy,CPU;不是流体解算。

**替代品和估值:** 尺度是估的;偏水彩,太阳像白球。

**脚本:** [`s38_richu.py`](../v2/stills/s38_richu.py)。

## 02 曜变

12.2 cm 碗(博物馆记录,截面是估的)。两层带间隙:烧成面用 Principled Thin Film,逐顶点膜厚(nm),膜 IOR 2.5 取磁铁矿 2.4 与赤铁矿 2.9 之间的估值;其上玻璃皮只有 Fresnel 反射,带缓波、环纹和划痕。反射的房间是 `yohen.paint_room` 自绘。运动是转台 5° 加 2% 推近,Cycles 384 spp。

**替代品和估值:** Metallic 基底 0.6 是替代品;cov 岛状覆盖代替破碎的膜;薄膜下的暗漫射色是替代品(真实的蓝有弱角度依赖的散射部分);膜厚色带是从 Airy 图表选的观感,不是测量;玻璃皮不折射。

**脚本:** [`s02_yaobian.py`](../v2/stills/s02_yaobian.py)、[`yohen.py`](../v2/stills/yohen.py)、[`yohen_shader_v1.py`](../v2/stills/yohen_shader_v1.py)、[`glaze_shader_v1.py`](../v2/stills/glaze_shader_v1.py)。

## 03 印泥

高度场按历史生成:骨匙刮痕、幂律碎屑、印章压痕,叠 0.05–0.15 mm 的艾绒纤维和油。颜色目标用实测 sRGB。final 320 spp。片里是静帧。

**替代品和估值:** 尺度是估的。

**脚本:** [`s05_yinni.py`](../v2/stills/s05_yinni.py)。

## 04 钧窑

釉是闭合壳的真实介质加内部薄片(sigma 估值,0.9 mm 处光学深度约 1)。蚯蚓走泥纹由 `s06_flow.py` 的润滑薄膜解算生成(固定网格 1 mm = 10 px,numpy),痕宽按李媛等 2013 的 1.0–1.6 mm;气泡按 Wang 2024 小于 100 µm。运动是脚本里 MOVE 写的慢转,Cycles final 640 spp。

**解算:** 润滑薄膜 h_t + div q = 0,q = C h^3 (S e_v − γ∇b − κ∇h),每步毛细流平,速率 h^3 k^4(Orchard),numpy,CPU。

**替代品和估值:** sigma 是估的;弱点:高光边缘像雾,紫区直纹。

**脚本:** [`s06_junyao.py`](../v2/stills/s06_junyao.py)、[`s06_flow.py`](../v2/stills/s06_flow.py)、[`glazekit.py`](../v2/stills/glazekit.py)、[`s52_shader.py`](../v2/stills/s52_shader.py)。

## 05 磁青

《心经》经文核对 CBETA T08n0251,字形以 cwTeX Q Kai ZH Medium(SIL OFL 1.1)为骨架,逐字加手写扰动;颜料厚度写进网格高度,纸是弯曲的圆柱面。Cycles,final 320 spp。静帧,cut.json 标 still、push 0,没有运动。

**替代品和估值:** 字形来自字体,扰动是手写规则;行距等尺度是估的。

**脚本:** [`s07_cijing.py`](../v2/stills/s07_cijing.py)。

## 06 银杏

一片银杏叶的网格,逐点着色(`s09_shader.py`,Schlick Fresnel 手写)。运动版 `s09_ginkgo.py`:叶瓣的鼓胀是选定的函数,不是解算(解算的抖动被否决),用子曝光做运动模糊。final 384 spp,36 帧。不再裂开,同一叶点缺口宽度只变 .58 px。

**替代品和估值:** 叶瓣运动是手写函数,不是风的解算。

**脚本:** [`s09_ginkgo.py`](../v2/stills/s09_ginkgo.py)、[`s09_leaf.py`](../v2/stills/s09_leaf.py)、[`s09_yinxing.py`](../v2/stills/s09_yinxing.py)、[`s09_shader.py`](../v2/stills/s09_shader.py)。

## 07 剔红

26 cm 盘(估),雕刻深 8 mm(估),漆层 0.12 mm 一层,颜色是刀深的函数。Principled 的 coat 是替代品;花样是我们自己的,与 Met DT2677 比过。运动是 looks.json 的 spin 11°。final 256 spp。

**替代品和估值:** Principled coat 代替漆层;花样不是文物;盘径、刻深是估的。

**脚本:** [`s61_tihong.py`](../v2/stills/s61_tihong.py)。

## 08 豇豆红

参照 Met 66.206.17 和 CMA 1942.673。闭合釉壳加铜红薄片,厚度 .5–.7 mm 取路辰等 2016(代码写作 Lu 2016)的总釉厚作代理;房间用 `yohen.paint_room`。final 512 spp。片里是静帧。

**替代品和估值:** sigma 是估的;釉厚是总釉厚的代理。

**脚本:** [`s11_jiangdou.py`](../v2/stills/s11_jiangdou.py)、[`glaze_shader_v1.py`](../v2/stills/glaze_shader_v1.py)、[`yohen.py`](../v2/stills/yohen.py)。

## 09 苏绣

针级高度场,长短针,22 个色阶,线径 .022 cm。线的金属度 .35 和 THREAD_GLOW 是替代品,底布自发光也是替代品。运动是 looks.json 里 window 和 rake 灯的变化,不动相机。final 320 spp。

**替代品和估值:** 线是高度场,不是几何;METAL .35 与 THREAD_GLOW 是替代品;底布自发光是替代品。

**脚本:** [`s59_suxiu.py`](../v2/stills/s59_suxiu.py)、[`s59_silk.py`](../v2/stills/s59_silk.py)。

## 10 走马灯

火焰在轴上,一圈剪纸在 Cycles 里真实光追出影子打到灯罩上。纸的前向散射是逐顶点算的 Henyey-Greenstein。10 个相位循环成 zoetrope,约 170 转/分,不加运动模糊。30 帧 take,final 256 spp。

**替代品和估值:** 环境自发光 amb 是替代品;转速和快门是选的;HG 只按顶点算。

**脚本:** [`s54_zoumadeng.py`](../v2/stills/s54_zoumadeng.py)。

## 11 折扇

扇骨是绕销轴的刚体,解算动力学(弹簧导向边骨、纸张绷紧传递、阻力、尖端阻尼振子);纸按不可伸长折叠算折深,f² = (2 sin(d0/2))² + a0²。金箔片是实体,光透过纸。子曝光(OPEN_PX=3)做运动模糊,final 448 spp。慢放 1。

**解算:** 扇骨动力学(`s15_open.py`):绕销刚体、导向弹簧、纸张拉紧、阻力、尖端阻尼振子,numpy,CPU。

**替代品和估值:** ARG 全部是估的,动作看图判断,没有看过实拍;扇面鼓起 billow 是代替气压的函数;未解算:纸自身动力学、气流、褶间接触。

**脚本:** [`s15_zheshan.py`](../v2/stills/s15_zheshan.py)、[`s15_open.py`](../v2/stills/s15_open.py)、[`s21_lib.py`](../v2/stills/s21_lib.py)、[`translib.py`](../v2/stills/translib.py)。

## 12 荔枝

黑底单颗荔枝的静帧,cut.json 标 still、push 0。果皮是球面上抖动点的 Voronoi:大小不一的革质片,每片鼓起,偏心一个小硬刺,片内浅裂,片间深沟。片与片的红不同,沟里偏黄,刺尖发黑,一层蜡。水珠是真折射的球冠。弧比标准弯(矢高约 .19,标准 .08):.08 时画面只有 1.2 cm 宽,认不出是荔枝。final 448 spp。

**替代品和估值:** 尺寸是估的,果径约 3.4 cm;片里是静帧。

**脚本:** [`s16_lizhi_v1.py`](../v2/stills/s16_lizhi_v1.py)。同目录的 `s16_lizhi.py` 是后来的树上一串,不进片。

## 13 点翠

微距:羽枝浮雕加珠串金属丝。羽枝间距 .0158 cm 量自 CMA 文物图;羽枝宽 40–70 µm 等文献值来自 调研。`diancui_shader.py` 是色带查表(lam_eff),明确不是结构色物理。运动是 looks.json 的 window 和 rake 灯光变化。final 320 spp。

**替代品和估值:** 结构色是替代品:绸缎色瓣加宽色瓣;羽毛整体是替代品。

**脚本:** [`s55_diancui.py`](../v2/stills/s55_diancui.py)、[`diancui_shader.py`](../v2/stills/diancui_shader.py)。

## 14 打铁花

不用 Blender:numpy 粒子。35 mm f/1.4、对焦 4.8 m,每个样本按弥散圆算;火星按带阻力的 ODE 飞(终端速度 1–8 m/s);色相取 Planck,亮度用更缓的幂次替代;0.10 s 快门合帧;烟是整形噪声。24 帧。

**解算:** 火星带阻力 ODE,numpy,CPU;不是流体。

**替代品和估值:** 亮度不是 Planck 的,是缓和的幂次;烟是噪声;尺度和数量是估的。

**脚本:** [`s14_datiehua.py`](../v2/stills/s14_datiehua.py)。

## 15 油纸伞

运行 `s21_youzhisan.py` 的源码(去掉最后一行),换数字:离轴 55°,伞转动,吸收按 s65 调到 (217,42,34) 色。有自己的 MOVE。take 40 spp、快门 .5(`s66_xieyang.py:52` 的预览配置,终版采样数没查到)。

**替代品和估值:** 尺度和吸收是估的。

**脚本:** [`s66_xieyang.py`](../v2/stills/s66_xieyang.py)、[`s21_youzhisan.py`](../v2/stills/s21_youzhisan.py)、[`s21_lib.py`](../v2/stills/s21_lib.py)、[`translib.py`](../v2/stills/translib.py)。

## 16 螺钿

薄螺钿喜鹊和梅花,每片一个倾角 (tx, ty),`nacre_shader.py` 每点一层薄膜干涉(真正的 Bragg 堆带更窄,这是挑颜色的替代)。looks.json spin 14°、key 灯 70,27 帧。final 384 spp。画是我们自己的。

**替代品和估值:** 干涉用一层薄膜代表多层;画面不是文物。

**脚本:** [`s46_luopan.py`](../v2/stills/s46_luopan.py)、[`nacre_shader.py`](../v2/stills/nacre_shader.py)。

## 17 红灯笼

竹篾骨架是几何并投影;绸面 `s20_shader.py` 前向散射 cos^k,织纹放大到 .35 mm。final 384 spp。静帧,合片时慢推。

**替代品和估值:** 织纹尺度夸大;弧顶 x .41 偏左;织纹像木纹。

**脚本:** [`s20_denglong.py`](../v2/stills/s20_denglong.py)、[`s20_shader.py`](../v2/stills/s20_shader.py)。

## 18 剪纸

手写多边形剪纸,底布是逐线织物。运动是 `s24_wind.py` 的薄板解算(网格 .2 mm,约 580×260,numpy/scipy),变形栈进 Cycles,相机不动,只有纸动。片取第 11 帧起 9 帧。final 192 spp。

**解算:** Kirchhoff 板 ρ w_tt + c(gap) w_t + div div(D∇∇w) = p − ρg,半隐式,一次稀疏分解;可压缩空气不解,载荷 q = ½ρU²;numpy/scipy,CPU。

**替代品和估值:** D、面密度、风速、阵风、挤压膜全是估的;未解算:气流、自接触、折痕软线、布的运动。

**脚本:** [`s24_jianzhi.py`](../v2/stills/s24_jianzhi.py)、[`s24_wind.py`](../v2/stills/s24_wind.py)。

## 19 南红

一串南红珠。`s63_chain.run_settle` 是准静态的链沉降(numpy,定种子);每颗珠子 rigid_take 真实运动模糊,随机游走 SSS;石纹用视差替代。片取第 4 帧起 34 帧,慢放 1。final 候选写 `take_cand`。

**解算:** 串珠线单向弹性 + 接触冲量(恢复、Coulomb 摩擦),`run_settle` 准静态进片,`run_zip` 等没进片;numpy,CPU。

**替代品和估值:** 石纹视差是替代品;灯光来自恢复的 17:15 版 frame012_final。

**脚本:** [`s63_nanhong.py`](../v2/stills/s63_nanhong.py)、[`s63_chain.py`](../v2/stills/s63_chain.py)。

## 20 金箔

皱纹是线条,缎面材质,撕裂边。8 帧 take,只有边缘动。final 220 spp。

**替代品和估值:** 动的只有边缘。

**脚本:** [`s27_jinbo.py`](../v2/stills/s27_jinbo.py)。

## 21 德化白瓷

闭合介质壳 1.5 cm 散射;衣褶是高度场分层,带串珠;`s28_shader.py` 画的是凹处积釉。looks.json 的 window 70 和 key 23 灯,key 扫过。final 384 spp。

**替代品和估值:** 积釉是画的。

**脚本:** [`s28_dehua.py`](../v2/stills/s28_dehua.py)、[`s28_shader.py`](../v2/stills/s28_shader.py)。

## 22 荷花

花瓣网格,开放由 `s39_wind.py` 的函数 ramp 给出(估值,不解算),子曝光运动模糊。`deliver` 写到 `take_cand` 再改名。final 448 spp,36 帧。花瓣慢慢舒展。

**替代品和估值:** 开放 ramp 是估的,不是解算。

**脚本:** [`s39_cand.py`](../v2/stills/s39_cand.py)、[`s39_petal.py`](../v2/stills/s39_petal.py)、[`s39_wind.py`](../v2/stills/s39_wind.py)、[`s39_hehua.py`](../v2/stills/s39_hehua.py)。

## 23 螺钿竹

每片叶是独立壳,V 字切口。薄膜干涉在 numpy 里对金属基底算三个波长,结果写进逐顶点。静帧,cut 标 still、push 0。final 256 spp。

**替代品和估值:** 三波长代替光谱。

**脚本:** [`s19_luodian.py`](../v2/stills/s19_luodian.py)。

## 24 狂草

按 (s, o) 的笔毛轨迹画飞白;纸有帘纹,带金片。final 256 spp。不是真实的字。合片用静帧做慢推。

**替代品和估值:** 字形是示意,不是真实文字。

**脚本:** [`s35_kuangcao.py`](../v2/stills/s35_kuangcao.py)。

## 25 一滴

墨滴的 3D Boussinesq 伪谱解算(`s68_flow.Flow`,自由滑移箱,粒子携带)。不路径追踪:自写合成器按视线吸收(Beer-Lambert),48 个深度层分别离焦,4.8 亿粒子。放慢 4 倍,快门是两个位置平均;画面倒置。NVIDIA RTX 5090 上 396 s 加 80 s 启动。

**解算:** 3D Boussinesq 伪谱,sin/cos 级数,自由滑移,SSP-RK3,2/3 去混叠,积分因子处理黏性,粒子 Heun 平流,torch GPU。

**替代品和估值:** 墨滴故意做大;只有吸收,没有散射;快门只用两个位置平均;Apple Metal 上没验证。

**脚本:** [`s76_yidi.py`](../v2/stills/s76_yidi.py)、[`s68_flow.py`](../v2/stills/s68_flow.py)。

## 26 油纸伞黑

用 v1 的相机数字,s21 的纸,`rain()` 画雨痕;去掉了伞边线、撑杆和伞轴。背景约 1/255。静帧,不动(still,push 0)。final 512 spp。盲审 65 分。

**替代品和估值:** 雨痕是函数;省掉的结构是构图选择。

**脚本:** [`s73_heisan.py`](../v2/stills/s73_heisan.py)、[`s21_lib.py`](../v2/stills/s21_lib.py)、[`translib.py`](../v2/stills/translib.py)。

## 27 孔雀羽

每根羽枝和羽小枝都是几何(羽小枝间距 .014 cm,5 个刻面)。`s45_flick.py` 解悬臂链(弯曲隐式、二次阻力显式,空气是模型)。`s45_shader.py` 是带 Bragg 样角度偏移的彩色粗糙镜,不是光子晶体。相机不动,单向轻风。final 256 spp。

**解算:** 羽枝悬臂链:弯曲隐式、二次阻力显式、空气模型,numpy,CPU。

**替代品和估值:** 结构色是替代品;EI、质量、Cd、风都是估的;未解算:羽枝互碰、羽轴弯曲、气流。

**脚本:** [`s45_kongque.py`](../v2/stills/s45_kongque.py)、[`s45_flick.py`](../v2/stills/s45_flick.py)、[`s45_shader.py`](../v2/stills/s45_shader.py)。

## 28 南珠

珠层用传递矩阵算 `stack_lut`(n 1.68/1.50,25 nm,60 周期,300–420 nm),Wyman 拟合转 RGB,涂层 n 1.6,RGB 瓣宽 620:540:460,加 Subsurface 体,窗环境 numpy 生成,40 µm 生长线进法线。层效果是相加的,不是真分层。慢转 ~2.8 px/帧。final 384 spp。

**解算:** 多层膜传递矩阵(LUT),numpy,CPU。

**替代品和估值:** 层是相加的;晕彩来自带色的灯;放大略有水波感。

**脚本:** [`s36_nanzhu.py`](../v2/stills/s36_nanzhu.py)、[`pearl_shader.py`](../v2/stills/pearl_shader.py)。

## 29 黄花梨

年轮是水平集,带结疤,导管随之走,加 coat。静帧,cut 标 still、push 0。final 320 spp。

**替代品和估值:** 木纹是水平集的函数,不是生长模拟。

**脚本:** [`s30_huali.py`](../v2/stills/s30_huali.py)。

## 30 青花

闭合釉壳(`s50_shader.py` 两面相同的 Fresnel),气泡是球体,钴料是薄片;`room()` 房间,`mirror_to()` 把窗影放到想要的釉面位置。厚度约真实的 2 倍,不折射。spin −6°。final 640 spp,默认写 cand.*。

**替代品和估值:** 釉厚约 2 倍;不折射;积釉压平是替代品;颜色目标测过,但渲出来偏亮。

**脚本:** [`s50_qinghua.py`](../v2/stills/s50_qinghua.py)、[`s50_shader.py`](../v2/stills/s50_shader.py)。

## 31 金鱼

鳍条是分叉射线,膜内色素;`s37_shader.py` 按光程着色。`pose(m, t)` 是手写动作,`--take` 出帧。final 384 spp。片用 13 帧。

**替代品和估值:** 动作是手写函数。

**脚本:** [`s37_jinyu.py`](../v2/stills/s37_jinyu.py)、[`s37_shader.py`](../v2/stills/s37_shader.py)。

## 32 珐琅

`chanzhi_v1.py` 生成掐丝纹样,`falang_shader.py` 着色;透明珐琅用 Translucent 替代。第一版蓝盘。looks.json spin 9°,文档串写 .35°/帧 32 帧。final 160 spp。

**替代品和估值:** Translucent 替代透明珐琅;鲤鱼、花卉、卷草已作废。

**脚本:** [`s49_falang_v1.py`](../v2/stills/s49_falang_v1.py)、[`chanzhi_v1.py`](../v2/stills/chanzhi_v1.py)、[`falang_shader.py`](../v2/stills/falang_shader.py)。

## 33 木炭

72 块炭用 Bullet(凸包)倒成一堆,再手摆 4 块。形状是隐函数加 surface nets(torch),裂纹是 AT1 相场(两代,GPU)。发光由表面能量平衡算温度,emission 不走光源采样;只有发光随时间变(emit_stack)。Cycles 384 spp,36 帧 1080p。

**解算:** AT1 相场裂纹(各向异性结构张量、两代、Zhang-Suen 细化),torch GPU;表面能量平衡 T、T_f,Newton 解 T_f,余弦光线穿占据格一次,torch GPU;Bullet 堆叠(`s69_pile_bpy.py`,Blender 内)。

**替代品和估值:** PRESETS 全是看图估的;ρ、c、δ、k、Q、E/R、T_k、h 都是估值;木炭用的是最早的造型。

**脚本:** [`s69_mutan_raw.py`](../v2/stills/s69_mutan_raw.py)、[`s69_shell.py`](../v2/stills/s69_shell.py)、[`s69_crack.py`](../v2/stills/s69_crack.py)、[`s69_pile_bpy.py`](../v2/stills/s69_pile_bpy.py)、[`s69_heat.py`](../v2/stills/s69_heat.py)、[`s69_shader.py`](../v2/stills/s69_shader.py)。

## 34 日出

与 s01 同一灯箱模型:宣纸水墨,灯从地平线后升起,就是日出。numpy,不用 Blender。136 帧写入 `take_final`,片取第 8 帧起 128 帧,慢放 .7143。`apex.json` 给片尾字定位。

**解算:** 笔触到达时间、Lucas-Washburn sqrt(t),numpy,CPU;不是流体解算。

**替代品和估值:** 尺度是估的;偏水彩,太阳像白球。

**脚本:** [`s38_richu.py`](../v2/stills/s38_richu.py)。

