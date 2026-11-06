# 技术栈

《格物》做过两代。**v2 是进片的方案**;v1 走物理建模,做了 6 天后放弃,片子没有用上,留在这里是因为里面的研究有价值。

**论文链接怎么读:** 技术栈里的链接标的是方法出自哪篇文献,不表示写代码时读过它。v2 的方法多凭记忆写,不少文献是整理时才配上的。谁读过、全文在不在手,以 [`docs/PAPERS.md`](PAPERS.md) 为准。

## 一览

| 环节 | 用的东西 | 代码 | 主要文献 |
|---|---|---|---|
| 几何和运动 | numpy 算逐顶点网格;隐函数加 surface nets;Bullet 堆叠 | `v2/kit.py`、`v2/stills/` | [surface nets](https://doi.org/10.1007/bfb0056277) |
| 材质 | Cycles 节点,参数从逐顶点属性读,不用贴图和照片;薄膜干涉、传递矩阵多层膜、随机游走 SSS、Henyey-Greenstein | `v2/stills/*_shader.py` | [Wyman 2013](https://jcgt.org/published/0002/02/01/)、[Henyey-Greenstein](https://doi.org/10.1086/144246) |
| 灯光 | numpy 生成的环境图和发光幕 | `v2/kit.py`、`v2/studio_bpy.py` | |
| 渲染 | [Blender](https://www.blender.org/) 5.2.1 Cycles 路径追踪;Apple Metal 和 NVIDIA OptiX(RTX 5090);[OIDN](https://www.openimagedenoise.org/) | `v2/studio_bpy.py` | |
| 解算 | 自写。[PyTorch](https://pytorch.org/) GPU:3D 伪谱 Boussinesq、AT1 相场断裂、表面能量平衡。numpy/scipy:润滑薄膜、Kirchhoff 板、悬臂链 | `v2/stills/s68_flow.py`、`s69_crack.py`、`s69_heat.py`、`s06_flow.py`、`s24_wind.py` | [Pham 2011](https://doi.org/10.1177/1056789510386852)、[SSP-RK3](https://doi.org/10.1016/0021-9991%2888%2990177-5)、[2/3 去混叠](https://doi.org/10.1175/1520-0469%281971%29028<1074:oteoai>2.0.co;2)、[Orchard](https://doi.org/10.1007/bf03184629) |
| 显影 | 自写暗房:Naka-Rushton 色调、Oklab 色度、halation、glare、胶片颗粒 | `v2/darkroom.py` | [Naka-Rushton](https://doi.org/10.1113/jphysiol.1966.sp008001)、[Oklab](https://bottosson.github.io/posts/oklab/) |
| 放慢 | [OpenCV](https://opencv.org/) DIS 光流补帧,没有学习模型 | `v2/tween.py` | [DIS](https://doi.org/10.1007/978-3-319-46493-0_29) |
| 合片和字幕 | Pillow 排字;[FFmpeg](https://ffmpeg.org/) libx264rgb 无损母版,再出 ProRes 和 H.264 | `v2/film.py`、`v2/cut.json` | |
| 配乐 | 代码写谱;[FluidSynth](https://www.fluidsynth.org/) 加 MuseScore General(MIT)采样,Keyscape 采样;自写混音 | `v2/music/` | |
| 校验 | 量构图的弧、找直线接缝、盲审 | `tools/arc.py`、`tools/seams.py`、`v2/BLIND0.md` | |
| 硬件 | Apple M1 Pro、M4 Pro(Metal);NVIDIA RTX 5090(OptiX) | | |
| 分工 | link1412 定方向和取舍;Claude Opus 5.5 写代码、做渲染 | | |
| v1(已放弃) | 打补丁的 [pbrt-v4](https://github.com/mmp/pbrt-v4)、Mie、TMM、PROSPECT-D、开裂力学、相机链 | `v1/` | 见下文 |

## 一条帧的路

```
numpy 算几何和运动 → scene.json + npy
  → Blender Cycles 路径追踪(逐镜 192–640 spp + OIDN)→ 线性浮点帧
  → 显影 develop():色差、曝光、暗角、halation、Naka-Rushton、颗粒
  → 需要放慢的镜头走 DIS 光流补帧
  → print_look():Oklab 色度和高光漂白、抬黑、胶片颗粒、字幕
  → film.py 按 cut.json 排片 → 无损母版 → ProRes、H.264
```

# v2:进片的方案

来源标记:**[码]** 代码里实现了;**[注]** 脚本注释声明的;**[文]** `v2/SHOTS.md`、`v2/IMAGERY.md`、`v2/music/README.md` 说的;**[记]** 制作时的记录,这里只转述。路径相对仓库根。成片 33.12 s,34 镜,828 帧,1920×1080,25 fps。逐镜的做法在 [`docs/FILM.md`](FILM.md)。

## 几何与场景

单位:1 unit = 1 cm。[码 `v2/studio_bpy.py`]

- **入口:** 每镜一个 `v2/stills/sNN_*.py`,用 numpy 算几何,写 scene.json 和数组,调 `kit.shoot(name, scene, q, develop, tag)`;Blender 用 `blender -b --factory-startup --python-exit-code 1 -P v2/studio_bpy.py -- scene.json` 跑。[码]
- **网格:** `grid_mesh` 是行×列×3 的逐顶点网格,属性逐顶点写入,没有贴图;`soup_mesh` 是三角汤。隐函数体(s69)用 surface nets。[码 `v2/studio_bpy.py`、`v2/stills/s69_shell.py`]
- **运动三类:** `spin`(刚体四元数关键帧)、`deform`(逐帧 npy,`extent` 双线性采样或 `vertex` 逐点)、`emit_stack`(只换发光)。相机路径在 `kit.camera_path`:dolly、truck、orbit、pivot、roll、rack、zoom、turntable、spin、lights。[码 `v2/kit.py`]
- **公共件:** `kit.fbm`(带限 FFT 噪声)、`warp`、`caps`、`rank`、`frame_camera`、`table_mesh`(linen/wood/paper/stone,AO 是画的)。[码 `v2/kit.py`]
- **最后一句话在 `v2/looks.json`:** `_dress` 用它覆盖脚本的相机、灯、天空和环境,sky 按曝光增益除。[码] 这造成 s55 的不一致,见「脚本和片子对不上」。
- 不进 Blender 的镜:s01、s38(numpy 灯箱)、s14(numpy 粒子)、s76(torch 解算加自写吸收合成器)。[码]

## 材质与着色

- **约定:** 着色器放在 `v2/stills/*_shader.py`,从逐顶点属性读参数;默认 `attr_material` 是 Principled。[码 `v2/studio_bpy.py`]
- **薄膜干涉:** s02 用 Principled Thin Film,逐顶点膜厚;s46 `nacre_shader.py` 每点一层膜;s19 在 numpy 里对金属基底算三个波长。[码]
- **多层膜:** s36 传递矩阵 `stack_lut`(n 1.68/1.50,25 nm,60 周期,300–420 nm),[Wyman 拟合](https://jcgt.org/published/0002/02/01/)转 RGB;系数凭记忆,注明没对原文。[注 `v2/stills/s36_nanzhu.py:12`]
- **结构色替代:** s45 `s45_shader.py`、s55 `diancui_shader.py` 都是带 [Bragg](https://doi.org/10.1098/rspa.1913.0040) 样角度偏移的彩色瓣,注释明写 SUBSTITUTE。[注]
- **釉:** 闭合壳加 Volume(s06、s11、s28、s50),两面相同的 Fresnel(`glaze_shader.py` 的 `skin_fresnel`、`s50_shader.py`):普通 Fresnel 从内侧看约 42° 全反射,挡住阴影光线出假暗带,德化修后亮度约 2 倍。[文 `v2/SHOTS.md:209`]
- **散射:** s54 灯纸逐顶点 [Henyey-Greenstein](https://doi.org/10.1086/144246);s20 绸面 cos^k 前向;s63 随机游走 SSS;s36 Subsurface 体。[码]
- **发光:** s69 由表面能量平衡出温度,`s69_shader.py` 关光源采样。[注]
- **手写 [Schlick](https://doi.org/10.1111/1467-8659.1330233):** s09 因为 Fresnel 节点按网格朝向取值。[码 `v2/stills/s09_shader.py:58`]

## 灯光与「摄影棚」

- **`gradient_light`:** 高斯发光幕,对相机隐藏,可关漫反射或光泽;另有 area、point、sun。[码 `v2/studio_bpy.py`]
- **`room_env`:** numpy 生成 2048×1024 等距柱面环境:天花板、墙、地面、带 2×3 窗棂的窗、灯带、摄影师阴影;作世界贴图,对相机不可见。[码 `v2/kit.py`]
- **`sky_mesh`:** 2400 cm 处的发光网格(sinh 间距,带杂色),给弧形天际线的镜头用。[码 `v2/kit.py`]
- **自绘房间:** `yohen.paint_room`(s02、s11);s50 `room()` 加 `mirror_to()` 把窗影放到想要的釉面位置。[码、文]
- **背景:** 有意义的才留,没意义的留摄影房间的灰黑。s73 背景约 1/255。[文]

## 渲染

- **渲染器:** Blender Cycles,路径追踪。版本是 Blender 5.2.1。
- **设备:** `gpu_api` 默认 METAL,NVIDIA 上 OPTIX。[码 `v2/studio_bpy.py`] 同场景 Metal 和 OptiX 均值差 .01 级,模糊后最大差 .5 级。[文]
- **参数:** 不开自适应;Blackman-Harris 1.3;bounces 8,漫反射 4、光泽 6、透射 12、体积 2、透明 16;clamp 直接 0、间接 20;OIDN RGB_ALBEDO_NORMAL ACCURATE,默认开;view Raw;输出 EXR 32 位,转 float16 npy。[码]
- **运动模糊:** 快门 .5,CENTER;persistent data。[码] 部分镜(s09、s15、s39、s45)用子曝光:多次渲移动网格再平均。[注]
- **DOF:** `aperture_mm` 换算 fstop = lens_mm / aperture_mm / 100,默认 9 片光圈,传感器 36 mm。[码]
- **采样:** kit 默认 preview 64、mid 128、final 384;分辨率 960×540、1280×720、2560×1440;take 1920×1080;check 960×540;预览 640×360。[码 `v2/kit.py`] 各镜 final 从 192(s24 风)到 640(s06、s50);见 `docs/FILM.md`。
- **分块:** 代码里没有设置 Cycles 的 tile,`tile` 的 grep 结果都是别的意思(`film.py` 的缩略图、s21 的裁切等);用的是 Cycles 默认,默认值没查。s76 的「分块」是粒子分块:平流 800 万一块,沉积 1600 万一块,不是渲染分块。[码 `v2/stills/s76_yidi.py`]
- **运动入口:** `GEWU_MOVE=check|preview|final`,默认多渲 3 帧(len+3);`fresh` 清旧帧,`GEWU_MOVE_RESUME=1` 保留;出 `ends.jpg`。[码 `v2/kit.py`]
- **失败重试:** 遇 GPU Hang / InnocentVictim 重试。[码]
  - Metal 上一次只跑一个 GPU 渲染,看到 WindowServer / panic 报告就杀任务。[码]

  - 32 GB 显存上同时最多两个 GPU 程序,解算要留 12 GB 给 Blender。[文]
- **环境变量:** `GEWU_BLENDER`、`GEWU_GPU_API`、`GEWU_CPU`、`GEWU_MOVE`、`GEWU_ENDS`。[码]

## 显影

`v2/darkroom.py`。帧是线性 float16。

`develop()` 顺序:[码]

1. 横向色差:R 缩放 1+ca,B 1−ca,默认 .0004,三次重映射。
2. 曝光 × 白平衡。
3. 暗角:1 − v·r²^1.3,默认 .25。
4. Halation:hi = max(x−.8, 0),上限 20,高斯 σ9·scale × .6 + σ32 × .4,乘 [1, .45, .2],强度 .05。
5. Glare:1/8 分辨率高斯 σ28 × .004。
6. 色调:[Naka-Rushton](https://doi.org/10.1113/jphysiol.1966.sp008001) x^c/(x^c+m),m = mid^c(1/mid − 1),c 1.25,mid .18,逐通道。
7. 饱和度(Rec.709 亮度),黑位。
8. sRGB 编码。
9. 捕获锐化:亮度上 unsharp σ.9 × .45。
10. `add_grain`:1.4 码值,高斯 σ.65,.75·每通道 + .25·均值,包络 sqrt(L)(1.15−L)·2 × 1.15。

`print_look()`(默认 glare .010、halation .07、chroma_knee .15、chroma_max .285、hue .05、floor (10, 11.5, 14)、shoulder .5):[码]

1. sRGB 解码。
2. 长尾 glare:1/8 分辨率 .45σ3 + .33σ12 + .22σ44。
3. Halation:hi = max(x−.45, 0),半分辨率 .65σ3 + .35σ11,乘 [1, .42, .14]。
4. 转 [Oklab](https://bottosson.github.io/posts/oklab/)(`darkroom.py:128`)。
5. 色相偏移:高斯在 H .45(+.8)、2.5(−.9)、−1.55(−1.0)× hue。
6. 色度:到 knee 前线性,之后指数滚降到 max。
7. 高光漂白:t = (L−.78)/.22,C × (1 − shoulder·t²)。
8. sRGB 编码。
9. 抬黑:(y^2.2 + f^2.2)^(1/2.2)。

`film_grain(amount, seed)`:σ.62,.62·每通道 + .38·均值,RGB [1, .95, 1.25],包络 1.3 + 2.6·sqrt(L)(1−L)·1.35。[码]

`v2/develop.py`:只重显影静帧,不重渲,不更新 develop.json。[码]

## 补帧放慢

`v2/tween.py`:OpenCV [DIS](https://doi.org/10.1007/978-3-319-46493-0_29)(`DISOPTICAL_FLOW_PRESET_MEDIUM`),没有学习模型。[码]

- 光流宽 960;灰度 1/2.2,按 99.8 分位缩放。
- 双向光流,两帧都 warp 到 t。
- 分歧 AGREE (.05, .14),在 σ1.5 高斯上量,分歧大退回较近的那帧。
- 混合 BLEND (.3, .7),smoothstep。
- 流场上采样,三次重映射。
- 再锐化:CRISP .45·min(t, 1−t)·(out − G σ.8)。
- 落在渲染帧上的位置不动。常数是估的。[注]

`slow` 见 `v2/cut.json`:s54、s15、s66、s63、s76、s73、s69_raw 为 1(等于 1 时 shown = len),s38 .7143。合片时 `shown = int((len−1)·slow + 1e-9) + 1`。[码 `v2/film.py`]

## 合片和字幕

`v2/film.py`,1920×1080×25,`v2/cut.json`(`shots` 进片,`bench` 备选)。[码]

- **取素材顺序:** `<src>_move_final/take.linear_###.npy` → `<src>_take_{final,mid,preview}/f###.png` → `<src>/{final,mid,preview}.linear.npy`;`still` 跳过前两个。
- **每帧:** develop(含 tween)→ 位移 → `print_look` → `film_grain`,seed = 100000+i;take 颗粒 .55。
- **静帧慢推:** PUSH .03/s,SLOW 1.15,绕 apex 做 warpAffine;`push 0` 不推。
- **字幕:** `text_mask` 4× Pillow,bloom .22σ3.5 + .12σ11;Songti.ttc idx 6,字号 74,CAPTION_Y .37;镜名字号 26,左上,不透明度 .88;字色按亮度 .62 自动选。
- **片尾:** "Claude Opus 5.5" Baskerville 72,从渲染帧 84 淡入 12 帧,跟 `apex.json` 上方 .19。
- **编码:** 默认 libx264 crf13、slow、tune grain、bt709、yuv420p;`--master` libx264rgb qp0 mkv;`--only`、`--sheet`。
- **交付:** `film_master_prores.mov`(`prores_ks -profile:v 5`,4444 XQ,PCM),`film_music.mp4`(H.264 CRF 10,AAC 320k),bt709,828 帧。PSNR Y 对母版:MOV 55.1 dB,MP4 50.9 dB。颜色标记和预览不同(19/20/21 对 14/17/14),原因没查。[记]
- **英文字幕版:** `python3 v2/film.py --master --en`。字幕一句话分三段:If truly new one day / new day after day / and new again,字体 Baskerville 62,角标换成英文名(`film.py` 的 `CAPTIONS_EN`、`NAMES_EN`)。字在颗粒之后才压上去,颗粒的种子是帧号,所以不用重渲。量过:对中文母版逐帧比较,除字幕带和角标外,828 帧差值都是 0。[码、量]
- **替代品:** Songti 代替宋刻本集字,Baskerville,没有 ✳。[文]

## 配乐

`v2/music/`。定稿 `mix_G_mit3.wav`,33.12 s。[文]

- **作曲:** `score.py`(A/B)→ `score_c..f.py` → `score_g.py`。G = F 加对位线和低音线。D 大调(写在 Eb,降半音发声),动机 A4 F#5 E5,半拍卡农;对位 D5 E5 F#5 E5 / F#5 A5 B5 A5 F#5 A5 D6;低音 D3 B2 A2 B2 / D3 B2 A2 F#2 A2 B2 A2。「Written, not heard.」[注 `v2/music/score_g.py`]
- **对原片的处理:** `follow()`(`score_e.py`)让每个八度频段的电平跟原片的响度曲线;不使用原片信号。节奏、形式、音量等来自对原片的测量,见 `README.md` 的量到的原曲一节。音符是自己的,旋律相似度未确认。[注、文]
- **采样:** MuseScore General 0.2 SF2(program 52 人声、49 弦乐,fluidsynth,`sf2.py`)。`voice_mit.py` 按 `voice_mit.json` 给每个人声音选录音和起点,再加一个静态滤波;滤波和切音增益是和放弃的 TimbresOfHeaven 版本量出来的,重跑不需要那个音色库。Keyscape Harmochord(Dronescape Deep、Ambient Reeds,`bank.py`;离线渲染工具碰付费库的内部格式,没有公开,这部分音色这里重现不了)。[文]
- **授权:** MuseScore General 是 MIT,版权和致谢原文在 `v2/music/NOTICE-MuseScore-General.md`。Keyscape 是付费音色库,条款没查。TimbresOfHeaven 只在放弃的版本里,它的条款原文在 `v2/music/README.md`。[文]
- **混音:** 自写 ensemble、room、wet、limiter。目标 −16.4 LUFS,−0.6 dBTP,用 ffmpeg `ebur128=peak=true` 量,迭代增益。[码 `v2/music/score.py`]
- **验证:** `verify.py`(爆音、DC、相位、音高和落点是否如写,和原曲旋律距离,librosa);`check.py`(对原曲的频段、L/R 相关、频谱图)。作者注明「我听不见声音」,这些只查错,不判好坏。[码、注]
- `bake.sh`:把音乐合进视频,画面只复制不重编码。[注]

## 硬件

| 机器 | 配置 | 用途 |
|---|---|---|
| Apple M1 Pro | 8 核,16 GB | 合片约 18 分钟 |
| Apple M4 Pro | 12 CPU,16 GPU,64 GB | Metal 渲染 |
| NVIDIA RTX 5090 | 32 GB,24 核,120 GB RAM,Ubuntu | OptiX 渲染、torch 解算 |

- **环境:** Python(numpy 2.4.4、scipy 1.17.1、cv2 5.0.0),torch 环境(重建步骤写的 torch 2.8.0、torchvision 0.23.0、cu128,numpy 2.3.3、scipy 1.18.1、opencv-python-headless 5.0.0.93;复测用 `requirements.txt` 的版本加 torch 2.8.0+cu128,Python 3.12.4,能跑通)。合片 venv Python 3.13,numpy 2.4.4,cv2 5.0.0,Pillow 12.1.1。
- **量到的:**
  - s02 37 帧:RTX 5090 275 s(7.4 s/帧),M4 Pro Metal 1121 s;GEWU_MOVE final Metal 31 s/帧。
  - s46 mid:RTX 5090 12 s,M4 Pro Metal 约 161 s。
  - s66 mid:M4 Pro Metal 19 s,RTX 5090 6 s。
  - s69 仅发光:5–10 s/帧,3400 万三角。
  - s76 片中参数:396 s 加 80 s 启动,4.8 亿粒子,48 层。s68_flow 约 20 GB。
  - s42 解算 111 s,27 帧 63 s。
- **帧大小:** 一帧 12.4 MB float16,gzip 5.7 MB;合片素材约 15 GB。

## 校验工具

- **`tools/arc.py`:** 量构图的弧:矢高、弧顶、落在弧上的列占比,对比原片。原片测得:矢高 .036–.201(中位 .079),弧顶 x .43–.55,y .46–.58。`--film` 跑全片。注释说天空不干净时读数差。[码]
- **`tools/seams.py`:** 找直线接缝:某行/列的跳变比邻行大 1.9 倍、连续覆盖超过 5%。用于矩形暗块。[码]
- **盲审 `v2/BLIND0.md`:** 一个模型混看 45 镜和 42 张真照片,我们平均实拍概率 20,无一到 60,真照片 96;美感约 2.8/5。上下文带了项目说明,不干净,不是摄影师。第二轮没做。真人摄影师没看过。[文]
- 另有逐镜 `ends.jpg` 看首尾,`sheet` 看全片。[码]

## 自写的解算器和物理模型

进片的:

- **`v2/stills/s68_flow.py`(s76 一滴):** 3D 不可压 Boussinesq,伪谱,自由滑移箱(sin/cos 级数),旋转形式,[SSP-RK3](https://doi.org/10.1016/0021-9991%2888%2990177-5),[2/3 去混叠](https://doi.org/10.1175/1520-0469%281971%29028<1074:oteoai>2.0.co;2),积分因子处理黏性;动力粒子沉积浮力,被动粒子在倍增网格每 K 步 Heun 平流。torch GPU,约 20 GB。进片。
- **`v2/stills/s69_crack.py`(木炭):** AT1 相场([Pham 等 2011](https://doi.org/10.1177/1056789510386852)),E = ∫ g(d)ψ⁺(ε(u)−ε0) + ψ⁻ + k/2|u|² + (3Gc/8)(d/l + l∇d·A∇d),g = (1−d)²,不可逆,shear lag L = √(E/k),正交各向异性结构张量 A,两代(粗冻进细),[Zhang-Suen](https://doi.org/10.1145/357994.358023) 细化。torch GPU。进片。
- **`v2/stills/s69_heat.py`(木炭):** 表皮温度 T 和膜温度 T_f;m dT/dt = q_ox − C(T−T_f) + 传导;C(T−T_f) = ε(σT_f⁴ − G) + h(T_f − T_gas);余弦加权光线穿占据网格一次算 G;q = Q·access·(1−b)·gust/(1+exp(E/R(1/T−1/T_k))),Newton 解 T_f。torch GPU。进片。
- **`v2/stills/s69_shell.py`、`s69_pile_bpy.py`:** 隐函数 + [surface nets](https://doi.org/10.1007/bfb0056277)(torch);Bullet 凸包堆叠(Blender 内)。进片。
- **`v2/stills/s06_flow.py`(钧窑):** 润滑薄膜 h_t + div q = 0,q = C h³(S e_v − γ∇b − κ∇h),毛细流平 h³k⁴([Orchard](https://doi.org/10.1007/bf03184629));固定网格,flow map,numpy CPU。进片。
- **`v2/stills/s24_wind.py`(剪纸):** [Kirchhoff 板](https://doi.org/10.1515/crll.1850.40.51),半隐式,一次稀疏分解,网格 .2 mm 约 580×260;空气不解,给载荷 ½ρU² 和挤压膜;每帧最小二乘补不可伸长。numpy/scipy CPU。进片。
- **`v2/stills/s15_open.py`(折扇):** 绕销刚体,导向弹簧,纸绷紧传递,阻力,尖端阻尼振子;纸不可伸长的闭式折深。numpy CPU。进片。
- **`v2/stills/s45_flick.py`(孔雀羽):** 悬臂链,弯曲隐式,二次阻力显式,空气是模型。numpy CPU。进片。
- **`v2/stills/s63_chain.py`(南红):** 线单向弹性,接触冲量(恢复、Coulomb)。片里只用 `run_settle` 的准静态沉降,`run_zip` 等弃用。numpy CPU。
- **`v2/stills/s38_richu.py`(s01、s38):** 笔触到达时间(速度场最短路径),[Lucas](https://doi.org/10.1007/bf01461107)-[Washburn](https://doi.org/10.1103/physrev.17.273) sqrt(t);不是流体。numpy CPU。进片。
- **`v2/stills/s14_datiehua.py`:** 火星带阻力 ODE,逐样本弥散圆。numpy。进片。
- **`v2/stills/s36_nanzhu.py`:** 传递矩阵 LUT。numpy。进片。

没进片的:

- **`v2/stills/s42_fire.py`:** 3D 浮力反应流,谱投影,限幅 [MacCormack](https://doi.org/10.2514/6.1969-354),浮力 g(1−300/T),膨胀,弱[涡量约束](https://doi.org/10.1145/383259.383260),体积罚,一步化学,碳烟,[Planck](https://doi.org/10.1002/andp.19013090310) 光线步进。网格 .4 cm。torch GPU。没进片。火形像蘑菇云,`nu=1.5` 是看图调的。
- **`v2/stills/s70_flow.py`:** 基于 s68,Brinkman 罚函数([Angot 等 1999](https://doi.org/10.1007/s002110050401)、[Kolomenskiy & Schneider 2009](https://doi.org/10.1016/j.jcp.2009.04.026))无穷阻力极限(掩膜 + 再投影),旋转、源;粒子龄期 σ² = 2Dt。torch GPU。没进片,茶镜搁置。
- **`v2/stills/s74_flow.py`、`s74_steam.py`:** 薄膜 h_t + div(h³/(3μ)(G − g_n∇h)) = 0,显式迎风,半拉格朗日;流函数运动学蒸汽。汤圆搁置,`s74_flow` 已不用。
- **`v2/stills/s43_heye.py`、`s58_heye.py`、`s64_heye.py`:** Young-Laplace 从冠顶积分(Bashforth-Adams);s64 光子前向追踪焦散,numpy。没进片。
- **`v2/stills/s27_float.py`:** 薄壳能量,[L-BFGS-B](https://doi.org/10.1137/0916069)(scipy),[Johnson-Christy](https://doi.org/10.1103/physrevb.6.4370) n、k,Airy 透射。没进片,在可清名单。
- **`v2/stills/s67_mutan.py`:** Planck 积 CIE(Wyman),Kirchhoff 发射率。没进片。
- **`v2/stills/s68_comp.py`:** 粒子折射(Newton 解 Snell),逐波段吸收。没进片。
- **`v2/stills/s06_copper.py`:** 半拉格朗日加扩散。没进片,`_poly` 有 GaussianBlur 用在 (n,2) 数组上的 bug 记录。
- **`v2/stills/s69_air.py`:** 热扰动,不在管线。
- **`v2/stills/s39_wind.py`、`s09_ginkgo.py`:** 不是解算,是选定的 ramp 和函数;进片。

## 复现

每镜的渲染命令在 `v2/render_film.py`,和片子逐镜比的结果、还没解决的问题在 [`docs/RENDER.md`](RENDER.md)。

## 全片已知问题

[记]

- spin 的首尾帧没有外侧关键帧,运动模糊只有一半(Laplacian 方差首尾 30.7/35.6,中间 17–21)。放映能否看出没验证。
- 矩形暗块:s16 候选 x 1664–2560、y 32–160 暗约 11%,落在 128 px 网格。原因是假设(只算部分样本却按全数归一)。
- 重渲时旧帧混入(蓝苏绣前 24 帧是绿的):现在默认 `fresh`,扫过 13 镜 `_move_final` 没混,PNG take 没扫。
- 每镜一道弧可能让人看出套路(假设)。
- s01、s38 偏水彩,太阳像白球(作者判断)。

## 替代品和没做的

[记,细节在各脚本开头]

- s46 干涉用一层薄膜代表多层,画是自己的。
- s02 的色是色带或薄膜,加漫射替代。
- s36 晕彩来自带色的灯。
- s45 的结构色;s55 的羽毛。
- s54 环境自发光、转速和快门。
- s59 的线是高度场,带少量自发光。
- 字幕字体 Songti 代替宋刻本集字;片尾 Baskerville;没有 ✳。
- 第二轮盲审没做;真人摄影师没看过。
- 没进片的方向:窑火、茶(s70、s71、s72)、糖葫芦(s75)、汤圆(s74)。

非论文来源(`docs/PAPERS.md` 不收):CBETA T08n0251(s07)、ISO 3103 与 GB/T 23776(s72)、Inaba 影像、Met 和 CMA 文物图、Franz van Duns 2021 和 DSM4694 2024 的照片致谢。

# v1:放弃的方案

这一节没带前缀的路径都在 `v1/` 下(`research/` 除外)。标记沿用项目文档:[M] 量的、[I] 查到的、[D] 推的、[F] 拟合的、[A] 假设。数字都来自项目文档,这次没有重跑。放弃的理由在这一节最后。

### 分层

材质 → 工艺 → 器物 → 光学 → 运动(`v1/docs/layers.md`,`v1/DESIGN.md` §0)。

- 材质、物体、光学、运动四层,再加工艺层:现实世界的物体都是由真实存在的东西制造出来的,skill 也因此更通用。
- 每个参数记 `{值, 单位, 范围, 出处, 标记}`。
- 材质卡:按真照片的比例尺(px/mm)和光拍一张,并排放,量 `tools/detail.py` 的各尺度能量和颜色。
- 旧是过程结果,不是旋钮,不是所有东西都需要做旧。审美旋钮只留在光学层。
- 配方工具 `tools/build.py` 把各层拼成器物。

### pbrt-v4 补丁

`v1/patches/pbrt-v4-gewu.patch`,1721 行,基于上游 b4ce968。改了 `base/bxdf.h`、`base/material.h`、`base/texture.h`、`bsdf.h`、`bxdfs.cpp/h`、`cpu/integrators.cpp/h`、`film.cpp/h`、`lights.h`、`materials.cpp/h`、`textures.cpp/h`。

#### 原始传感器 RGB

`Film "rgb" "bool rawsensor" true`:`film.cpp` 把 `outputRGBFromSensorRGB` 设成单位矩阵,输出未转色的传感器 RGB,交给 `tools/camera.py`。

#### 折射光源连接(RNEE)

`Material "dielectric" "bool refractivenee" true` 加 `Integrator "volpath" "bool refractivenee" true`。文档 `v1/docs/rnee.md`。

- 动机:釉里的点做 NEE 时,影子射线碰到釉面就停,直接光全靠路径碰巧打中。实测 480×320,volpath 1024 spp 噪声 35%,bdpt 256 spp 噪声 49%。
- 界面处理:反射走微表面,透射当 delta,按宏观法线的菲涅耳选。
- 连接:在面光源上采 z,解 x→y→z 的折射点 y。`SolveRefraction` 在切平面上用斯涅尔定律做一元牛顿加区间保护,探测射线落回真实釉面,最多 16 步,在 y 的法线上验到 1e-3。
- 估计量:`f·|cos|·T_F·(η_x/η_z)²·Le·透射率 ÷ (p(z)/J)`。
- Jacobian J 用重新追踪做差分,h = 3e-4 rad。切平面的解析 J 在 R20 mm、深 1.2 mm 时低 4–5%,R5、深 1 mm 时低 13–16%,所以弃用。
- 不重复计算:靠 `rneeState` 状态划分加已验证的求解器。不用 MIS(试过,慢 48%,噪声 15.4% 对 15.7%)。
- 限制:只支持面光源,球形光源报错;一次只过一个折射界面;BSSRDF 不连。
- 修正:方向归一化(带吸收的薄膜才看得出,钴带暗 1.6–4 倍);零方向崩溃。

验证在 `v1/tests/rnee/`(`scenes.py`、`compare.py`),240×160。下表抄自 `v1/docs/rnee.md:76`,参考和其余几行不在同一台机器上渲:

| 场景 | 方法 | spp | 时间 | 逐像素噪声 | 均值 / 参考 | 块 z(均值,rms) |
|---|---|---|---|---|---|---|
| 釉板加 3 裂 | 路径追踪(参考) | 2×4096 | 80 s | 13.5% | 参考 | |
| | 路径追踪 | 256 | 7.1 s | 53.7% | 1.0018 | −0.02, 1.02 |
| | RNEE | 256 | 12.4 s | 15.7% | 1.0006 | +0.00, 1.03 |
| 圆柱 R5 加 1 裂 | 路径追踪(参考) | 2×4096 | 24 s | 9.8% | 参考 | |
| | 路径追踪 | 256 | 2.6 s | 35.3% | 1.0028 | −0.10, 1.14 |
| | RNEE | 256 | 3.9 s | 24.1% | 1.0017 | −0.06, 1.07 |

效率提高:釉板 6.7 倍;圆柱 1.4 倍,因为圆柱有一半的面上灯在当地地平线以下,光是在釉里绕过来的,连接帮不上。

#### 相干薄膜(为曜变)

`Material "thinfilm"`(`ThinFilmBxDF`):GGX 微表面,菲涅耳换成单层 Airy 公式 `ThinFilmR`,逐波长算,可选漫射底。参数 `filmeta`、`filmk`、`eta`、`k`、`thickness`(nm,可贴图)、`roughness`、`reflectance`。缺 `filmeta`、`eta`、`thickness` 就报错。

验证在 `v1/tests/yohen/`:

- 对 `tools/tmm.py`(特征矩阵和 Rouard 两种写法互差 1e-15)的色带 ΔE 中位 0.12–0.29,p95 ≤ 0.87,最大 1.72。
- 膜厚为 0 时与 `conductor` 逐位相同。
- 粗糙膜对 GGX 积分的 tmm 差 ≤ 0.04%;漫射底 ≤ 0.05%。
- `tests/rnee` 的结果逐位不变。

#### 浓度到光谱族的贴图

`Texture "spectrum" "familymap"`(`FamilyMapSpectrumTexture`):读 npz 的 `lambda_nm, c, R`,按浓度图在光谱族里插值。用于青花的钴浓度和银杏的叶脉。验证 `v1/tests/textures/`、`v1/tests/qinghua/check_coat.py`。

#### 带吸收的薄板

`thindielectric` 加 `"transmittance"`。文档 `v1/docs/coats.md`。验证 `v1/tests/qinghua/`:对一维解析解,pbrt 大多 0.98–1.01,钴 c3 的 R 为 1.04。

#### 其他

`textures` 部分还加了 imagemap 的 filter、encoding 参数。层用三角形不用 bilinear patch,因为后者的求交会拒绝近距离。

### 其他渲染器

**Cycles**(Blender 5.2.1,Apple Metal):

- `tools/rgbscene.py` 把 pbrt 子集场景的光谱投到 5D Mark IV 的三个通道。光源精确;反射率和介质按「传感器 × 主光」加权,一次反弹精确。`tools/cycles_scene.py` 搭节点渲染。pbrt 是左手系,Blender 右手系,要翻转。
- 速度(第 6 镜 t6):960×540、64 spp,pbrt CPU 约 40 s,Cycles GPU 5.1 s;1080p、256 spp 加 OIDN 46.7 s。三通道均值比 0.995、0.996、0.996,同噪声快约 30 倍。釉 2 mm 的光谱损失差 1.8%。
- 花青素的吸收太陡,不能按通道平均:`objects/lychee/run.py` 在写完 `scene.cycles.json` 后,按反照率匹配换掉 σa(`docs/materials/lychee.md` 第 65 行起)。
- `nacreinlay`、`barbule` 两种材质只在 Cycles 里,查表实现。
- `docs/slab.md` 记的三个坑:Cycles 只在水密网格里填介质,开口时釉面暗 12–24%;Glossy 默认颜色是 0.8 灰,薄膜会变暗;法线朝向要修,补丁 `patches/cycles-orient-normals.patch` 打在 `tools/cycles_scene.py` 上(不是 Cycles 源码),vfilm 对 pbrt 的比值从 0.65–0.81 到 0.999–1.000。
- Cycles 的 Principled Thin Film 没有 k,对 tmm 的 ΔE 中位 1.81,p95 4.35(高对比时)。

**`tools/slab.py`**:MCML 风格的蒙特卡罗参照([Wang, Jacques & Zheng 1995](https://doi.org/10.1016/0169-2607%2895%2901640-f);GGX 按 [Heitz 2018](https://jcgt.org/published/0007/04/01/) 可见法线采样)。光滑六变体与 pbrt 差 0.6% 内。发现路径上限 64 会丢光,汝釉暗 22%;改成 g×0.6、上限 128。

**Mitsuba**:没用过。`DESIGN.md`、`docs/layers.md` 只提到「以后可以试可微渲染(Mitsuba 3,从 3.9 起有 Metal 后端 [查到,没试])」。

**WebGPU**:查过(`research/webgpu-pt/`),没有替换。

**guofeng 引擎**(另一个项目,MoXi 格子玻尔兹曼):`DESIGN.md` 列入计划。第 1/38 镜实际用自写的 `shots/01-38-ink/sim.py` 和 `optics.py`,numpy 做 Kubelka-Munk,不路径追踪。

### 材质的物理模型

| 材质 | 目录 | 模型 | 取值和对照 |
|---|---|---|---|
| 官窑 | `materials/guan_glaze`,`docs/materials/guan_glaze.md` | 散射釉介质加胎;裂缝是真几何(空气膜、腐蚀沟道、沉积填充);RNEE。釉吸收由 `glaze_fit` 从实测反射谱反解 | 灰散射 2.5/mm,α 0.0307,对 Met 48503 32.23 px/mm。三态(刚出窑、传世、出土)在 `states.json`;线色由 `fillsolve`、`heirsolve` 解 |
| 汝窑 | `materials/ru_glaze` | 铁吸收(Volotinen 2008 分峰);Appen 折射率;Mie(`tools/mie.py`)算液滴、钙长石、气泡三种散射体,加 Percus-Yevick 结构因子;`slab` 拟合 | 对 [Shi 2020](https://doi.org/10.1016/j.ceramint.2020.06.139) R1、R2 的 Lab 拟体积分数 [F]。结论 [D]:白来自钙长石,35 nm、Δn 0.02 的液滴在 10% 体积下 σs 只有 0.004/mm。钙长石针宽 800 nm 是最大假设 |
| 青花 | `materials/qinghua` | 透明釉加钴吸收层(τ = c·κ(λ))加朗伯胎;真几何 coat,全反射回收;一维 stack 精确 | [Thiemsorn 2007](https://doi.org/10.1299/jmmp.1.508) 钠钙玻璃 Co5 矢量读图,595 nm κ 0.588 per g/m²。康熙伴生吸收是 [F] 替身,不是铁。对 [Hsieh 2023](https://doi.org/10.1186/s40494-023-00953-0) FORS 弱检验 |
| 朱漆 | `materials/cinnabar_lacquer` | 不透明漫射底 Kubelka-Munk R∞(K/S 加 2·a漆/S);介电面;Saunderson 修正由真几何产生 | a漆 [Oyabu & Asami 1987](https://doi.org/10.4011/shikizai1937.60.94),S 150/mm [F],朱砂 R(λ) [Reichert 2025](https://doi.org/10.1007/s00216-025-05948-3) 减黑,n 1.52,α 0.0054([Hou 2025](https://doi.org/10.3390/polym17111481) 的 90 GU 经 `tools/gloss.py`) |
| 鎏金 | `materials/gilt_copper`,`docs/metals.md` | pbrt `conductor` 的 metal-Au 代用 [A];Cu₂O 膜用 Airy 公式算法向反射 | α 0.02 [F];层厚只记范围。对 Cleveland 1970.149.1,ΔE*ab 约 13,原因没分开(`docs/materials/gilt_copper.md:197`) |
| 胭脂红 | `materials/yanzhi` | 金 n,k([McPeak 2015](https://doi.org/10.1021/ph5004237))加 Kreibig 尺寸修正(A 0.25,[Berciaud 2005](https://doi.org/10.1021/nl050062t))加 Mie 20 nm 得 κ(λ);铅玻璃 Appen;一维 stack | 金 0.56 g/m² [F]。对 Met 1971.180.248,第一轮 pbrt 正面 ΔE00 3.5/4.0,六区 4.8;加工艺层和相机链后六区 6.32,正面 L* 28.8 对 19.3 太亮,根因没找到(工作记录) |
| 银杏 | `materials/yinxing`,`objects/yinxing/leaf.py` | PROSPECT-D(`prospect.py`,N 层板,tests 五项过);`familymap` 叶脉谱族;`diffusetransmission`;`senescence.py` | `fit_spectra` 对 [Morimoto 2022](https://doi.org/10.1364/oe.441063);LOTUS 做 R→T 检验;正光 ΔE76 2.23,背光 13.7 |
| 荔枝 | `materials/lychee`,`objects/lychee` | 分层介质:果肉散射介质(μs′ ∝ λ⁻¹,g 0.7)、水吸收([Pope & Fry](https://doi.org/10.1364/ao.36.008710),Segelstein)、花青素形状(PROSPECT-D);起点 Kubelka-Munk 加 Saunderson(`fit_card`)和 [Jensen 2001](https://doi.org/10.1145/383259.383319) 偶极 R_d;再用渲染修正 | 果肉 n 1.3627;修正系数果皮约 (1.48, 1.00, 0.87) |
| 曜变 | `objects/yohen_inaba`,`docs/materials/yohen.md` | 补丁的 `thinfilm`;斑点从 1955 图版分割,378 个斑核 | 膜参数是占位 [A];机理未定,列五个候选;未完成 |
| 珍珠层、螺钿 | `shots/19-luodian/nacre.py`、`nacre.json` | 无序文石和有机层的多层特征矩阵(波动光学);每层厚度单独抽样,对列平均 \|r\|²;顶面分开算;查表进 Cycles | n 1.63 [A],有机层 n 1.43、25 nm [A],片厚 σ 50 nm([Salman 2021](https://doi.org/10.1073/pnas.2023623118))。第 19 镜 r1 的画面不成立 |
| 孔雀羽 | `shots/17-peacock/barbule.py` | [Freyer & Stavenga 2020](https://doi.org/10.1039/d0fd00033g) 有效介质多层 TMM,n_eff=(Σf nʷ)^(1/w),w_TE 2.5,w_TM −1.5;查表 | 倾角按 [Yoshioka & Kinoshita 2002](https://forma.katachi-jp.com/abstract/1702/17020169.html) θ0 15° |
| 墨和宣纸 | `shots/01-38-ink` | Richards 方程算水,深床过滤算炭([Iwasaki 1937](https://doi.org/10.1002/j.1551-8833.1937.tb14014.x),两粒级);`paper.py` 撒纤维;Kubelka-Munk 背光渲染 | 湿纸 S 0.156 倍 [D];MAC 7.5;细粒级 AAE 对原片拟成 4.07 [F],超出黑碳范围。第 38 镜和第 1 镜是同一张图的机位运动 |

`tools/mie.py`(714 行):BHMIE,改了 Lentz 起点和小 x 的对数导数;Percus-Yevick 结构因子;对 Bohren & Huffman 样例和 MIEV0 的 15 例校验。文档 `docs/mie.md`。

### 工艺模拟

`crafts/` 下每个目录解一件事,文档在 `docs/crafts/`。

- **crackle**(`crackle.py`,641 行):逐条开裂([Bohn 2005](https://doi.org/10.1103/physreve.71.046215))。通道裂判据 G = Zσ²e/E′ ≥ Γ([Hutchinson & Suo](https://doi.org/10.1016/s0065-2156%2808%2970164-9))。剪滞决定间距,两代裂纹对应金丝铁线([Li 2001](https://doi.org/10.1557/mrs2001.16))。转向 a* = (2/3) h `d/dn[ln e − ln Γ]`,见 [Cotterell & Rice](https://doi.org/10.1007/bf00012619)。韧性随机场 [F],在保角图上模拟。`network.py`、`straight.py` 量网的统计;`faces.py` 出裂面网格,倾角取 [Yang 2012](https://doi.org/10.5772/31213)。
- **glazeflow**(`flow.py`):润滑理论([Schwartz & Weidner 1995](https://doi.org/10.1007/bf00046385)),de/dt + (1/r) d(rq)/ds = 0,有限体积。TODO 记录检查没过(正弦流平高 6%,球面散开 5e-3),没用上。
- **carving**(`carve.py`):高度场 SDF → 刀形 → 多级浮雕 → 漆层按深度露色。`test_carve` 对闭式解。
- **painting**(`paint.py`):勾线、分水、烧成,参数全 [A],输出钴浓度 c(x,y)。
- **deposition**:裂缝填充 erfc(depth/L),加 Hapke 混合 USGS 替代谱。
- **wear**:灰度开闭运算加球形结构元。
- **weathering**:只模拟表皮粗糙度 `skin_alpha`(依据 [Han 2023](https://doi.org/10.1016/j.culher.2023.08.010) 摘要的定性结论,值 [F]);发白和颜料变暗没做。
- 还有 **dust**、**duanwen**、**cutting**。`docs/crafts/life.md` 是生命类工艺的计划。

### 相机链

`tools/camera.py`:原始 RGB → 衍射(艾里斑,N(1+m))→ 电子数泊松加读出噪声(5D IV 满阱 67871 e⁻,ISO 100 读出 11.5 e⁻,Photons to Photos,Bill Claff)→ 白平衡 → 24 色卡矩阵(ΔE 均值 1.44)→ 色调 → sRGB → 4:2:0 → x264,按原片同参数分段。

### 光学层

`optics/`:`rigs/*.json` 五套灯,`backdrops.json`,`framing.py` 按弧解机位。灯组(lightgroup)一次渲出多层 EXR,线性混合,先混后用 OIDN 降噪。测试在 `tests/optics/`。

### 盲审和对照工具

- `tools/blind.py`:照片和渲染随机 A/B,答案另放。
- 胭脂红、银杏各三轮,每轮两个模型当评委,**六轮全被认出**。评委说的破绽:胭脂红内壁反光对称、红太匀太干净;银杏斑点像泊松、叶脉等宽、背景纯白。教训:r1 把裁图原件放在评委能列的目录,评委从文件大小认出了答案,之后原件放到别处。
- `DESIGN.md` §6 计划过人类盲测(n ≥ 20,正确率 ≤ 60%)和取证统计(Lyu & Farid 等)。只有设计,没查到实现。
- 对照:`tools/compare.py`、`tools/shotcheck.py`(一镜 5–10 s)、`tools/lightfit.py`(NNLS 拟灯,约 1 s)、`tools/detail.py`、`tools/sharpness.py`、`tools/flow.py`、`tools/spec_measure.py`(出 `spec/shots.json`)、`tools/film.py`、`tools/shotkit.py`、`tools/kit_bpy.py`、`tools/gloss.py`。
- 测试目录:`tests/` 下 camera、carving、lathe、lightfit、metals、mie、nacre、optics、qinghua、rnee、slab、textures、yinxing、yohen。

### 硬件

- Apple M1 Pro,8 核,16 GB。
- Apple M4 Pro,12 核 CPU,16 核 GPU,64 GB。

- 量过的速度:960×540、512 spp,GPU 7 s,4 线程 CPU 66 s。pbrt 1080p 一帧 2.8 h(第 6 镜)。

### 为什么放弃,换成 v2

1. 投入和露脸时间不相称:34 个短镜头平均只露 0.37 s,材质卡、pbrt 补丁、TMM、Mie、蒙特卡罗参照在片子里都没用上。
2. 数字验收和观感脱节:±3 码的拟灯总能过;第 6、19、17、27 镜数字过了但看着不对;`lightfit` 把主光拟成 0(`v1/docs/skill-notes.md` 第 160 条)。汝窑笔洗(`v1/objects/ru_washer`)看着假。
3. 不是所有帧都要物理建模,有些用着色器就能达标。

v2 的做法:不做逐帧配色对应,不拟数字(±3 码、拟光、shotcheck 全停),判断只有一条:放到 100% 还像不像真东西。v1 的参数和出处仍被 v2 引用。

