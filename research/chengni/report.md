# 鳝鱼黄澄泥砚砚池：材质与外观参照报告

检索与下载日期：2026-11-02。用途：为砚池及邻近研墨面建立可追溯的渲染参照；本次交付为资料研究，未对实物进行测量，也未制作最终渲染。

## 1. 推荐方向与证据边界

推荐以**细密烧结陶胎的黄褐漫反射底色、精磨造成的柔和反光、按具体工艺添加的蜡处理层**构建干态材质；水、墨迹和仿古装饰分别控制。决定性依据是：馆方将澄泥砚归为陶砚，非遗资料记载澄滤和煅烧，工艺专利明确记录烧后水磨、部分配方浸蜡；照片也显示研墨面与外壁处理存在明显差异。[故宫释义](https://www.dpm.org.cn/lemmas/239833.html)、[非遗项目](https://www.ihchina.cn/project_details/14559/)、[烧后水磨工艺](https://patents.google.com/patent/CN110467433A/zh)、[浸蜡工艺](https://patents.google.com/patent/CN101302097A/zh)、[实物多视图](https://www.lempertz.com/en/catalogues/lot/1249-1/84-a-highly-important-imperial-chengni-tiger-shaped-inkstone-qianlong-period-cyclically-dated-wuxu-1778.html)。这是建模推断，不是文献中的完整光学模型。

证据分为四层，下面均显式区分：

| 标记 | 含义 | 本次可取得的内容 |
|---|---|---|
| 直接资料 | 对象确属澄泥砚 | 馆藏与非遗描述、工艺申报、实物照片 |
| 替代实测 | 对象为其他烧结黏土/陶 | 陶砖/陶瓦光谱、造型黏土的粗糙度与光泽 |
| 派生计算 | 从公开实测数据计算 | 指定光源和观察者下的色度、显示用RGB |
| 建模建议 | 作者提出的起点 | 分层方式、参数试配与对照方法，不冒充实测 |

**尚未找到公开、可核验的鳝鱼黄澄泥砚本体可见反射光谱、标准色度、Ra/Sa、GU、折射率或BRDF实测。** 因而本报告不能给出“鳝鱼黄唯一标准色”或“澄泥砚统一roughness”。传统品色名不是一个已知的光谱标准；绛州非遗条目列鳝鱼黄、绿豆砂、玫瑰紫、朱砂红，但没有色度坐标。[非遗官方条目](https://www.ihchina.cn/project_details/14559/)

## 2. 材料、工艺和烧成

### 2.1 澄泥砚的材料身份

故宫将其说明为细泥澄滤、去渣沉淀，加固剂制坯后煅烧的陶砚；不同产地包括绛州、虢州、山东柘沟、滹沱河等，不能默认矿物组成一致。绛州非遗资料指出使用汾河沉积泥，成品坚实、莹润、触感细腻；这些是定性描述，并非孔隙率或光学检测值。[故宫《澄泥砚》](https://www.dpm.org.cn/lemmas/239833.html)、[绛州非遗项目](https://www.ihchina.cn/project_details/14559/)

### 2.2 可量化的工序实例

以下数据各属一套流程，**不能拼成一种通用古法**。专利是申请人的配方与方法披露，不等同于第三方复现实验或馆藏实物检测。

| 对象/证据 | 原料及处理 | 烧成或时间 | 适用边界与出处 |
|---|---|---|---|
| 当代绛州，2023年传承人采访 | 澄清过滤4–5遍；包膜静置6个月；成形后阴干3个月 | 全流程约一年；温度、气氛和坯体位置影响颜色 | 采访记述，没有粒径和气氛监测原始记录。[中国非遗网转载原文](https://www.ihchina.cn/project_details/27252.html) |
| 现代改进工艺，CN110467433A，2019 | 古汾河沉积泥配其他黏土；球磨、150目筛除≥106 μm颗粒 | 电窑：室温→300°C 6 h；→900°C 15 h；→1050°C 5 h；保温5 h，自然冷却 | 不是鳝鱼黄专用配方。烧后800目水磨1–2次、1200目2–3次。[说明书步骤六、十五、十六](https://patents.google.com/patent/CN110467433A/zh) |
| 鳝鱼黄目标配方，CN102432271A，2012 | 五台县滹沱河古沉泥；成坯置耐火盒，小米糠完全埋住 | 980–1050°C，烧72 h | 有明确色名目标，但无成品光谱、Lab和独立验证；不能作为绛州唯一烧法。[权利要求1–2](https://patents.google.com/patent/CN102432271A/zh) |
| 早期复原配方，CN85104538A，1986 | 选定沉积泥，另见下表 | 900–950°C，80–100 h；出窑趁热注蜂蜡防渗 | 属该申请的方法实例，不是全部澄泥砚的烧成范围。[原料及烧制段](https://patents.google.com/patent/CN85104538A/zh) |

### 2.3 成分：能给什么，不能给什么

CN85104538A列出所选原料的氧化物质量百分数要求如下。这是**选泥指标**，没有证据表明它就是本项目鳝鱼黄实物的成品分析；不能直接当烧后物相比例、颜料配比或着色相含量。[专利原文](https://patents.google.com/patent/CN85104538A/zh)、[本地扫描PDF](papers/craft_CN85104538A.pdf)

| 成分 | 原料质量分数 | 来源 |
|---|---:|---|
| SiO₂ | 60.86% | [CN85104538A](https://patents.google.com/patent/CN85104538A/zh) |
| Al₂O₃ | 18.08% | [同上](https://patents.google.com/patent/CN85104538A/zh) |
| Fe₂O₃ | 5.99% | [同上](https://patents.google.com/patent/CN85104538A/zh) |
| CaO | 7.85% | [同上](https://patents.google.com/patent/CN85104538A/zh) |
| MgO | 3.09% | [同上](https://patents.google.com/patent/CN85104538A/zh) |
| K₂O | 微量 | [同上](https://patents.google.com/patent/CN85104538A/zh) |

原文另有一项0.84%的化学式尚未可靠辨明，未猜写；上表不是完整归一化分析。现有资料不足以把鳝鱼黄唯一归因于某一种铁矿物或某个含量。故宫藏品页自动关联的“鳝鱼黄”术语解释涉及**陶瓷结晶釉**，不能据此推断澄泥砚胎色机理。[相关馆藏页，正文与关联术语需区分](https://www.dpm.org.cn/collection/studie/230397.html)

## 3. 颜色与反射光谱

### 3.1 原始来源与替代样品

Kotthaus、Smith、Wooster、Grimmond 的 *Derivation of an urban materials spectral library through emittance and reflectance spectroscopy*，ISPRS Journal of Photogrammetry and Remote Sensing 94 (2014), 194–212，DOI：[10.1016/j.isprsjprs.2014.05.005](https://doi.org/10.1016/j.isprsjprs.2014.05.005)。[机构仓储 PDF](https://centaur.reading.ac.uk/36997/1/IJPRS_Kotthaus_2014_albedo_emissivity.pdf)已下载到 `papers/color_Kotthaus_2014.pdf`。

其原始数据由研究者发表于 [Zenodo / SLUM，DOI 10.5281/zenodo.4263842](https://zenodo.org/records/4263842)。[SW 原始 CSV](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)存为 `data/color_LUMA_SLUM_SW.csv`；[带样品照片和曲线的手册](https://zenodo.org/records/4263842/files/2013_LUMA_SLUM.pdf?download=1)存为 `papers/color_2013_LUMA_SLUM.pdf`。

| 样品 | 作者标注的材质／颜色／状态 | 替代用途 | 来源 |
|---|---|---|---|
| B014 | Ceramic brick / Brick clay；Yellow/grey；Weathered, dusty | 主要黄灰陶质光谱基线；不能复制其砖粒孔洞来代替细泥砚面 | [论文 Table C.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005)；[手册 p.47](https://zenodo.org/records/4263842/files/2013_LUMA_SLUM.pdf?download=1) |
| B008 | Ceramic brick / Brick clay；Light red；New | 浅红烧结黏土参照，非鳝鱼黄 | [论文 Table C.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005) |
| B013 | Ceramic brick / Brick clay；Red；Weathered | 较暗红褐胎色参照 | [论文 Table C.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005) |
| R002 | Ceramic roofing tile；Brown；New | 深褐陶质颜色参照；不能假定其表面与蜡面澄泥相同 | [论文 Table C.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005)；[手册 p.53](https://zenodo.org/records/4263842/files/2013_LUMA_SLUM.pdf?download=1) |
| R001 | Ceramic roofing tile；Red；New | 红陶对照 | [论文 Table C.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005) |

作者没有提供这些建筑陶样品的烧成温度、窑气氛、原料 XRF 或矿物相信息，故只能证明它们是实测陶质参照，不能声称与绛州澄泥成分相同。B014 原图已从手册 p.47 无损提取为 `img/color_SLUM_B014_0.png`（516 × 404 px）；R002 图为 `img/color_SLUM_R002_0.png`（440 × 460 px）。这两张是**替代样品照片，不是澄泥砚照片**。[手册](https://zenodo.org/records/4263842/files/2013_LUMA_SLUM.pdf?download=1)

### 3.2 测量条件

原始短波测量为 SVC HR-1024，名义覆盖 350–2500 nm，4°视场，镜头离靶 350 mm、观测斑约 25 mm；使用两盏 300 W 灯，垂直观测，Spectralon 白板校准。每样品取两处、各五次，共十次。作者按白板光谱校正绝对反射率，再平滑、平均；拼接后保留 988 波段。它是**固定几何、介于双锥与半球—锥形之间的反射观测，不是完整 BRDF，也不是真正半球反射率**。[论文 §3.1.1、§3.2.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005)

本地 CSV 实际首尾波长为 **348.1–2505.8 nm**，共有 **988 行 × 74 个样品列**，反射率用**百分数**表达；渲染中用无量纲反射率时必须除以 100。[原始 CSV](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)；数目及范围由本地解析复核。

### 3.3 可见反射率数据

下表为原始 CSV 在指定波长作**线性插值**后的值，单位 **%**；不是从照片采色，不是从论文图像读数。完整插值表 `data/color_visible_10nm.csv` 覆盖 360–830 nm、间隔 10 nm；原始不等间隔数据仍保留。每个数字均来自同一[原始测量 CSV](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)。

| 波长 nm | B014 黄灰陶砖 | B008 浅红陶砖 | B013 红陶砖 | R002 褐陶瓦 | R001 红陶瓦 |
|---:|---:|---:|---:|---:|---:|
| 400 | 17.94 | 14.47 | 12.48 | 5.73 | 9.51 |
| 450 | 21.42 | 15.86 | 14.36 | 6.24 | 9.64 |
| 500 | 28.26 | 17.92 | 15.90 | 6.90 | 10.45 |
| 550 | 36.26 | 22.90 | 19.02 | 8.27 | 13.91 |
| 600 | 41.27 | 37.08 | 27.07 | 10.00 | 26.04 |
| 650 | 43.90 | 42.53 | 30.62 | 11.37 | 31.86 |
| 700 | 45.51 | 46.60 | 33.26 | 12.95 | 36.49 |

### 3.4 派生色度

下表**是本报告计算结果**，不是论文作者直接报告的 Lab。以反射率 R(λ) 乘 [CIE 官方 D65](https://www.cie.co.at/datatable/cie-standard-illuminant-d65) 和 [CIE 1931 2° 标准观察者](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer)，把原谱线性插值到 360–830 nm、1 nm 网格后求和；以同区间理想白漫反射体 Y=1 归一化 XYZ，按 [CIE CIELAB 定义](https://cie.co.at/eilvterm/17-23-076)转换 Lab，并按 [ICC sRGB 说明](https://registry.color.org/rgb-registry/files/sRGB.pdf)转换线性 RGB 与带传递函数的 8 bit sRGB。没有曝光调节或颜色匹配到砚石照片。来源为[SLUM 原谱](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)，计算可由 `python3 scripts/colorimetry.py`（需 NumPy）复现。

| 替代样品 | 派生 L* | a* | b* | 线性 sRGB（0–1） | 显示用 sRGB，8 bit / HEX |
|---|---:|---:|---:|---|---|
| B014 | 66.70 | 1.85 | 20.54 | (0.45315, 0.35103, 0.20710) | (179, 160, 126) / `#B3A07E` |
| B008 | 58.55 | 15.24 | 19.68 | (0.44401, 0.22432, 0.14760) | (178, 130, 107) / `#B2826B` |
| B013 | 53.00 | 10.01 | 13.97 | (0.31387, 0.18728, 0.13588) | (152, 120, 103) / `#987867` |
| R002 | 35.17 | 4.15 | 8.58 | (0.11336, 0.08026, 0.05996) | (95, 80, 69) / `#5F5045` |
| R001 | 48.58 | 18.39 | 19.22 | (0.32565, 0.13557, 0.08835) | (155, 103, 84) / `#9B6754` |

派生数据保存在 `data/color_derived_D65_2deg.csv`，保留 XYZ 与更多小数仅为复现；表中两位小数不代表测量准确度为 ±0.01。固定观测几何、风化状态和样品不均匀性远比计算舍入更重要。`#B3A07E` 可作 RGB 工作流的**替代色起点**；要忠实复原某方鳝鱼黄，仍需对该砚实物测量。PBR 中同时添加独立镜面层时还须避免把当前几何下包含的反射与镜面高光重复计入；本谱不能单独给出 Fresnel、光泽或微表面 roughness。

## 4. 粗糙度、光泽与蜡面

### 4.1 能用于约束外观的无釉陶实测

Hur等（2026）的实验比较同一市售造型黏土的素烧、磨削、抛光与上釉状态。材料含砂较高、素烧850°C；上釉对照另经1250°C复烧。**它比澄滤细泥更粗，下面数值是替代样品数据，不是澄泥砚砚池的允许范围。**[论文官网](https://www.jkspe.or.kr/journal/view.php?number=7316)、[DOI](https://doi.org/10.7736/JKSPE.026.00056)、[本地全文](papers/surface_Hur_2026_unglazed_clay_polishing.pdf)

| 表面工序 | Ra，μm，图6所示轮廓 | 60°光泽，GU，图7均值±标准差 | 数据出处 |
|---|---:|---:|---|
| 素烧原面 | 8.015 | 1.91±0.07 | [PDF第5页，印刷页1031，图6–7](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf) |
| 磨削 | 5.327 | 4.03±1.21 | [同图](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf) |
| SiC逐级湿抛至2000目 | 3.060 | 7.11±0.99 | [同图；工序在PDF第4页表2](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf) |
| 上釉并复烧 | 1.143 | 53.31±14.58 | [同图](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf) |

测量使用SJ-310接触式轮廓仪和YG60S光泽计；光泽按ISO 2813、60°测量，文中说明5个独立试片各重复8次。粗糙度参考ISO 4288，但未列具体截止长度；图6前三种轮廓约12 mm、釉面对照约4 mm，因此Ra按图示值引用，不能误称为同带宽的群体均值。上釉对照同时改变烧成制度，仅用于外观对比。[PDF第4–5页](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf)

### 4.2 澄泥砚蜡处理的直接工艺证据

CN101302097A对一类黄河澄泥制品规定石蜡75–90%、蜂蜡10–25%，70–100°C浸泡15–20 min，随后1200–1500#水砂纸打磨抛光。此处按权利要求7–8引用；实施段另有不一致比例，不据其反推膜厚。该配方使用矿物/陶瓷色料，也说明不能概括所有澄泥砚均无添加。[专利权利要求](https://patents.google.com/patent/CN101302097A/zh)、[本地PDF](papers/craft_CN101302097A.pdf)

砂纸目数不等于成品Ra，浸蜡时间也不等于表面存在某个固定厚度的均匀蜡膜；本次未取得目标实物的蜡膜厚度、蜡量、IOR或光泽增量实测。不能仅凭照片高光判断器物一定上过蜡。[所据工艺原文](https://patents.google.com/patent/CN101302097A/zh)、[实物参照页](https://www.lempertz.com/en/catalogues/lot/1249-1/84-a-highly-important-imperial-chengni-tiger-shaped-inkstone-qianlong-period-cyclically-dated-wuxu-1778.html)

### 4.3 陶面涂蜡的实验机制参照

Rueff等（2021）用自然黏土、相当于黏土质量25%的小于1 mm碳酸盐料，750°C烧4 h；将熔融蜂蜡涂到预热的已烧陶片。共焦测量面积25 mm²、分辨率2 μm，并用小波幅值SMa分析，**不是一组可直接移植的Ra数据**。图4–5显示涂层减弱凸起，压光后加涂层的表面更平整。论文将蜂蜡/乳/橄榄油处理组的水接触角概述为50–70°，未处理组为0–30°；这是多个处理的分组描述，不是澄泥砚或蜂蜡单组精确测量。[论文DOI](https://doi.org/10.1016/j.jasrep.2021.103021)、[作者稿PDF第4–10页](https://hal.science/hal-03468734/document)、[本地19页作者稿](papers/surface_Rueff_2021_reading_ceramic_surfaces.pdf)

该实验支持“表面处理可改变微地形与润湿性”的机制；不能据此假定澄泥砚接触角、GU或蜡膜参数相同。压光、烧后磨光、涂蜡是不同操作，建模时也应分别考虑。

### 4.4 三种“粗糙/光滑”量不要混用

- **Ra（μm）**是测线高度偏差的算术平均，受测量尺度与滤波影响；它不包含唯一的微面斜率分布。[本次轮廓测量方法](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf)
- **GU**是规定角度、孔径下相对于黑玻璃标准的光泽量；BYK说明标准折射率1.567、赋值100 GU。GU不是反射率百分数，曲面的仪器几何也有限制。[BYK白皮书第5页](https://media.byk-instruments.com/shop/Misc/Whitepaper/White_Paper_Gloss_Measurement_EN_20221114.pdf)
- **渲染器roughness**是微表面模型参数。Blender将其定义为镜面反射/透射的微表面粗糙度；coat层可独立设roughness、IOR和normal。因此不能把3.060 μm直接填成0.306，也不能将7.11 GU换成roughness=0.9289。[Blender官方说明](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html)

检索到CN109020479A报告改性黄胶泥砚“光泽度/(%)”86.9–87.6，但没有角度、仪器、标准板或GU说明，而且不是鳝鱼黄。已保存供复核，**不采用为渲染定量输入**。[专利表1](https://patents.google.com/patent/CN109020479A/zh)、[本地PDF](papers/craft_CN109020479A.pdf)

## 5. 高清砚池与外观照片

已保存20个馆方/拍卖机构JPEG参考文件，其中含1张铭文拓片；另有2张替代陶材样品PNG。原始像素尺寸经解码确认，未放大、改色或锐化。下面是优先图，完整逐图原图URL、作品身份、尺寸和用途见[照片清单](notes/photos.md)；[文件校验清单](notes/photos_files.json)可核对SHA256。

| 优先图及本地文件 | 实际像素 | 用途与限制 | 来源 |
|---|---:|---|---|
| 清十八至十九世纪澄泥竹节砚，[正面](img/npm_chengni_1_1.jpg)、[另一面](img/npm_chengni_1_2.jpg) | 各1920×1440 | 黄褐/赭黄表面、密集暗斑、柔和反光；馆方没有将这件定名为鳝鱼黄 | [台北故宫“爱砚成痴”特展](https://theme.npm.edu.tw/exh112/Inkstones/ch/page-4-3.html) |
| 明澄泥风字砚，[砚面](img/dpm_ming_feng_17063.jpg)、[斜视](img/dpm_ming_feng_17062.jpg) | 830×1024、1024×798 | 馆方明确称“鳝鱼黄色”；照片却呈暗绿灰、研墨区较黑。保留这种差异，不能直接吸取RGB作标准色 | [北京故宫，新00135204](https://www.dpm.org.cn/collection/studie/230397.html) |
| 清乾隆戊戌（1778）仿古澄泥伏虎砚，[砚池俯视](img/lempertz_1249-84-A-highly-import-j.jpg) | **2807×4250** | 最清晰的砚池/研墨面参照；能见阴阳形储墨池、细凹点/划痕、平滑转角。器物属红褐色，不能当鳝鱼黄颜色样本 | [Lempertz拍卖1249，Lot 84](https://www.lempertz.com/en/catalogues/lot/1249-1/84-a-highly-important-imperial-chengni-tiger-shaped-inkstone-qianlong-period-cyclically-dated-wuxu-1778.html) |
| 同件伏虎砚，[开盖斜视](img/lempertz_1249-84-A-highly-import-b.jpg)、[外壁侧视](img/lempertz_1249-84-A-highly-import-e.jpg) | 3999×3333、4000×2868 | 用于池深、圆角与光泽区域差异；铜绿结壳及金斑属仿古装饰，不是自然胎色 | [同一拍卖原始说明](https://www.lempertz.com/en/catalogues/lot/1249-1/84-a-highly-important-imperial-chengni-tiger-shaped-inkstone-qianlong-period-cyclically-dated-wuxu-1778.html) |
| 明蕉叶澄泥砚，[斜视](img/npm_chengni_2_1.jpg)、[背面](img/npm_chengni_2_2.jpg) | 1920×1440、1920×2560 | 褐灰陶质、浅凹面、叶缘与叶脉雕刻辅助参考，不作黄色样本 | [台北故宫特展](https://theme.npm.edu.tw/exh112/Inkstones/ch/page-4-3.html) |

![黄褐澄泥竹节砚外观参照，未经校色，非鳝鱼黄实测](img/npm_chengni_1_1.jpg)

上图：黄褐外观方向。来源为[台北故宫特展原图](https://theme.npm.edu.tw/exh112/Inkstones/common/images/3/3-3/3-1-1.jpg)，图像观感不能替代光谱。

![红褐澄泥伏虎砚砚池高清参照，非鳝鱼黄样本](img/lempertz_1249-84-A-highly-import-j.jpg)

上图：砚池几何与表面细节。来源为[Lempertz官方原图](https://www.lempertz.com//lempertz_api/images/1249-84-A-highly-import-j.jpg)。照片内高光仅支持相对外观，不能测出Ra或证明有蜡。

历史研究还有直接的区域处理证据：赵丽红《清乾隆时期仿古砚制作初探》引用清宫档案，记乾隆四十二年有关石渠砚制作要求“将砚做青绿色，研墨处不必上色”。这一例子支持装饰区与研墨区分开处理，不能推出所有澄泥砚研墨区都无色层或无蜡。[故宫论文第177页，PDF第13页](https://img.dpm.org.cn/Uploads/File/2020/04/15/u5e96b75bae38e.pdf)、[本地全文](papers/craft_DPM_Qianlong_imitation_inkstone.pdf)

图片用于研究参照收集。所用故宫、特展与拍卖页面未据此确认开放再发行许可；不把数字典藏其他版本的CC声明套用到本批文件。未校色照片中的光源、相机处理、保存状态与墨污会影响颜色，故保持与第3节实测替代光谱独立。

## 6. 如何落实为渲染参照

以下是**建模建议，不是澄泥砚实测参数**：

1. 先确定一个干态样本方向：颜色以第3节黄灰/褐色陶实测为可追溯起点，形制与斑纹以第5节黄褐竹节砚为外观方向。主光谱样品有风化/灰尘，和鳝鱼黄并非一一对应，若需要更饱和的黄褐色，应将调整记录为美术修订。[实测替代资料见第3节；馆方照片](https://theme.npm.edu.tw/exh112/Inkstones/ch/page-4-3.html)
2. 底材先用非金属、不透明陶体模型；颜色斑驳与微小凹点分开控制。研墨面保持平整、细密，池壁和转角保留柔和过渡；高清伏虎砚能支持这些相对外观判断，无法支持具体凹点深度。[高清实物原图](https://www.lempertz.com//lempertz_api/images/1249-84-A-highly-import-j.jpg)
3. 镜面反射应主要反映光源颜色。若只做早期试配，可自拟底层IOR=1.5、roughness=0.35/0.50/0.65三档进行比较；**这些是测试假设，没有澄泥砚材料测量依据**。固定相机、光源尺寸、曝光及色彩管理后，观察宽高光和掠射反光，再选接近参考者。参数语义依据[Blender官方文档](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html)。
4. 有蜡的版本另加表层/处理遮罩；未掌握膜厚时，不以厚而透明的漆壳作为默认。水/墨使用独立的局部材质和几何，让干湿边界、积液与残墨不污染底色。分层选择依据是已存在的水磨/浸蜡工序和照片中的区域差异，具体权重、厚度、吸收系数仍待测。[浸蜡工艺](https://patents.google.com/patent/CN101302097A/zh)、[多视图实物](https://www.lempertz.com/en/catalogues/lot/1249-1/84-a-highly-important-imperial-chengni-tiger-shaped-inkstone-qianlong-period-cyclically-dated-wuxu-1778.html)

若后续能取得目标实物，最有价值的是同一干净区域的反射光谱（记录光源/观察者/几何、SCI或SCE、是否有蜡）、带尺度和滤波的Ra/Sa，以及固定光照下的多角度照片；先测同一器物的研墨面、池壁与装饰区，才能收紧本报告目前的替代范围。此为后续测量建议，本次并未执行。

## 7. 文件、核验与限制

已核验：**11份PDF均可解析**（不只检查扩展名）；**22张图均可解码**，关键砚池照片和论文数据图已实际查看；原始SLUM与CIE数据MD5匹配发布者值，色度脚本复现本报告表格。[SLUM校验来源](https://zenodo.org/records/4263842)、[CIE观察者数据](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer)、[CIE D65数据](https://www.cie.co.at/datatable/cie-standard-illuminant-d65)。本地完整文件大小、像素/页数与SHA256见[资产清单](data/asset_manifest.json)。

| PDF本地文件 | 内容与已核验页数 | 原始下载出处 |
|---|---|---|
| [color_Kotthaus_2014.pdf](papers/color_Kotthaus_2014.pdf) | 建筑材料光谱原始论文，21页（含仓储封面） | [Reading机构仓储](https://centaur.reading.ac.uk/36997/1/IJPRS_Kotthaus_2014_albedo_emissivity.pdf) |
| [color_2013_LUMA_SLUM.pdf](papers/color_2013_LUMA_SLUM.pdf) | 光谱/样品照片手册，78页 | [Zenodo原文件](https://zenodo.org/records/4263842/files/2013_LUMA_SLUM.pdf?download=1) |
| [craft_CN85104538A.pdf](papers/craft_CN85104538A.pdf) | 选泥成分与复原工艺专利，8页 | [原始PDF](https://patentimages.storage.googleapis.com/3f/1b/86/9bbb9870dd1c85/CN85104538A.pdf) |
| [craft_CN102432271A.pdf](papers/craft_CN102432271A.pdf) | 鳝鱼黄工艺专利，4页 | [原始PDF](https://patentimages.storage.googleapis.com/6f/60/6c/4ec373fe5c41b8/CN102432271A.pdf) |
| [craft_CN110467433A.pdf](papers/craft_CN110467433A.pdf) | 现代制备/水磨专利，11页 | [原始PDF](https://patentimages.storage.googleapis.com/cc/fb/84/cd956ec5e51dd8/CN110467433A.pdf) |
| [craft_CN101302097A.pdf](papers/craft_CN101302097A.pdf) | 浸蜡工艺专利，8页 | [原始PDF](https://patentimages.storage.googleapis.com/ff/36/15/5e35d8882d5545/CN101302097A.pdf) |
| [craft_CN109020479A.pdf](papers/craft_CN109020479A.pdf) | 改性黄胶泥砚，8页；光泽数据未采用 | [原始PDF](https://patentimages.storage.googleapis.com/ca/03/ec/d9ba37560f8353/CN109020479A.pdf) |
| [craft_DPM_Qianlong_imitation_inkstone.pdf](papers/craft_DPM_Qianlong_imitation_inkstone.pdf) | 故宫清代仿古砚研究，16页 | [故宫原始PDF](https://img.dpm.org.cn/Uploads/File/2020/04/15/u5e96b75bae38e.pdf) |
| [surface_Hur_2026_unglazed_clay_polishing.pdf](papers/surface_Hur_2026_unglazed_clay_polishing.pdf) | 无釉陶Ra/光泽实测，10页 | [期刊原始PDF](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf) |
| [surface_Rueff_2021_reading_ceramic_surfaces.pdf](papers/surface_Rueff_2021_reading_ceramic_surfaces.pdf) | 陶面处理与润湿性实验，19页作者稿 | [HAL作者稿](https://hal.science/hal-03468734/document) |
| [surface_BYK_gloss_measurement_2022.pdf](papers/surface_BYK_gloss_measurement_2022.pdf) | 光泽测量技术白皮书，10页 | [BYK原始PDF](https://media.byk-instruments.com/shop/Misc/Whitepaper/White_Paper_Gloss_Measurement_EN_20221114.pdf) |

数据文件：

- [原始SLUM光谱](data/color_LUMA_SLUM_SW.csv)：988波段，含全部74个样品；单位%。[来源](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)
- [360–830 nm、10 nm步长的插值表](data/color_visible_10nm.csv)：五种陶材，不代替原始不等间隔文件。
- [D65/2°派生XYZ、Lab、线性RGB及sRGB](data/color_derived_D65_2deg.csv)，[复现脚本](scripts/colorimetry.py)：执行 `python3 scripts/colorimetry.py`，需NumPy，不发网络请求。
- [CIE 1931 2°数据](data/color_CIE_xyz_1931_2deg.csv)、[D65数据](data/color_CIE_std_illum_D65.csv)：[CIE原始观察者文件](https://files.cie.co.at/Publications-datasets/CIE_xyz_1931_2deg.csv)、[原始D65文件](https://files.cie.co.at/Publications-datasets/CIE_std_illum_D65.csv)。
- 分项工作底稿：[工艺](notes/craft.md)、[颜色](notes/color.md)、[表面](notes/surface.md)、[逐图来源](notes/photos.md)。

未成功下载的补充来源：台北故宫数字典藏[褐黄澄泥砚15419](https://digitalarchive.npm.gov.tw/Collection/Detail/15419?dep=U)、[赭黄璧水砚3048](https://digitalarchive.npm.gov.tw/Collection/Detail/3048?dep=U)，以及[2023年月刊上篇](https://www.npm.gov.tw/NewChineseArtDownload.ashx?bid=4627)、[续篇](https://www.npm.gov.tw/NewChineseArtDownload.ashx?bid=4635)，直接访问发生TLS握手错误；没有将失败响应另存为图/PDF，也未计入交付数量。已下载的特展照片可用于本次外观工作。目标实物的直接光谱、标准粗糙度与蜡膜光学参数仍是资料缺口；第3–4节明确使用替代实测。

辅助下载器见[scripts/safe_fetch.py](scripts/safe_fetch.py)，逐次校验URL及重定向。
