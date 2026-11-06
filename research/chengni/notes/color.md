# 色谱与色度：可用证据和替代数据

## 结论和证据边界

本轮针对“澄泥砚／鳝鱼黄＋光谱／色度／颜色分析”以及英文 Chengni inkstone 的公开检索，没有找到可核验的**澄泥砚鳝鱼黄可见反射光谱、CIELAB 表或光谱原始文件**。这表示本轮未发现，不能据此断言不存在。故宫的[澄泥风字砚](https://www.dpm.org.cn/collection/studie/230397.html)给出“澄泥质，鳝鱼黄色”的实物定名，但没有仪器色度；照片不能直接提供材质反射率。

建议暂以 **SLUM 黄／灰陶砖 B014** 的实测光谱作为可追溯的黄色烧成陶质基线，同时保留红陶 B008、B013、R001 和褐陶 R002 作邻近颜色比较。**这些均为替代品，绝非鳝鱼黄的测量结果或传统色标准**。B014 是风化、带尘陶砖，黄色与灰斑可能包含表面沉积和风化的影响，不能从本数据反推澄泥的原料比例、铁价态或烧成制度。[SLUM 数据集](https://zenodo.org/records/4263842)、[作者论文 Table C.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005)。

另须避开同名术语混淆：故宫上述页面的自动关联词条“鳝鱼黄”解释的是黄绿结晶**釉**；该词条没有证明这方澄泥砚施该釉，不能把该段铁镁结晶釉机理套到澄泥胎色。

## 主要原始来源与样品

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

## 光谱的测量条件

原始短波测量为 SVC HR-1024，名义覆盖 350–2500 nm，4°视场，镜头离靶 350 mm、观测斑约 25 mm；使用两盏 300 W 灯，垂直观测，Spectralon 白板校准。每样品取两处、各五次，共十次。作者按白板光谱校正绝对反射率，再平滑、平均；拼接后保留 988 波段。它是**固定几何、介于双锥与半球—锥形之间的反射观测，不是完整 BRDF，也不是真正半球反射率**。[论文 §3.1.1、§3.2.1](https://doi.org/10.1016/j.isprsjprs.2014.05.005)

本地 CSV 实际首尾波长为 **348.1–2505.8 nm**，共有 **988 行 × 74 个样品列**，反射率用**百分数**表达；渲染中用无量纲反射率时必须除以 100。[原始 CSV](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)；数目及范围由本地解析复核。

## 可直接使用的可见反射率

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

## 派生 D65／2° 色度与渲染色

下表**是本报告计算结果**，不是论文作者直接报告的 Lab。以反射率 R(λ) 乘 [CIE 官方 D65](https://www.cie.co.at/datatable/cie-standard-illuminant-d65) 和 [CIE 1931 2° 标准观察者](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer)，把原谱线性插值到 360–830 nm、1 nm 网格后求和；以同区间理想白漫反射体 Y=1 归一化 XYZ，按 [CIE CIELAB 定义](https://cie.co.at/eilvterm/17-23-076)转换 Lab，并按 [ICC sRGB 说明](https://registry.color.org/rgb-registry/files/sRGB.pdf)转换线性 RGB 与带传递函数的 8 bit sRGB。没有曝光调节或颜色匹配到砚石照片。来源为[SLUM 原谱](https://zenodo.org/records/4263842/files/LUMA_SLUM_SW.csv?download=1)，计算可由 `python3 scripts/colorimetry.py`（需 NumPy）复现。

| 替代样品 | 派生 L* | a* | b* | 线性 sRGB（0–1） | 显示用 sRGB，8 bit / HEX |
|---|---:|---:|---:|---|---|
| B014 | 66.70 | 1.85 | 20.54 | (0.45315, 0.35103, 0.20710) | (179, 160, 126) / `#B3A07E` |
| B008 | 58.55 | 15.24 | 19.68 | (0.44401, 0.22432, 0.14760) | (178, 130, 107) / `#B2826B` |
| B013 | 53.00 | 10.01 | 13.97 | (0.31387, 0.18728, 0.13588) | (152, 120, 103) / `#987867` |
| R002 | 35.17 | 4.15 | 8.58 | (0.11336, 0.08026, 0.05996) | (95, 80, 69) / `#5F5045` |
| R001 | 48.58 | 18.39 | 19.22 | (0.32565, 0.13557, 0.08835) | (155, 103, 84) / `#9B6754` |

派生数据保存在 `data/color_derived_D65_2deg.csv`，保留 XYZ 与更多小数仅为复现；表中两位小数不代表测量准确度为 ±0.01。固定观测几何、风化状态和样品不均匀性远比计算舍入更重要。`#B3A07E` 可作 RGB 工作流的**替代色起点**；要忠实复原某方鳝鱼黄，仍需对该砚实物测量。PBR 中同时添加独立镜面层时还须避免把当前几何下包含的反射与镜面高光重复计入；本谱不能单独给出 Fresnel、光泽或微表面 roughness。

## 校验与文件

- SLUM SW CSV：1,241,561 bytes；MD5 `3c828f525b12c7bcbdc2476a056328f4`，与[Zenodo 公布值](https://zenodo.org/records/4263842)一致。
- SLUM 手册：18,243,243 bytes；MD5 `f4cae8bb5269a8ad713f1d76ce8eaba8`，与[Zenodo 公布值](https://zenodo.org/records/4263842)一致。
- [CIE 2° CSV](https://files.cie.co.at/Publications-datasets/CIE_xyz_1931_2deg.csv)：本地 `data/color_CIE_xyz_1931_2deg.csv`，MD5 `17cca777db64b17170f06f67ce9d3ab7`，与 CIE 公布值一致。
- [D65 CSV](https://files.cie.co.at/Publications-datasets/CIE_std_illum_D65.csv)：本地 `data/color_CIE_std_illum_D65.csv`，MD5 `03d4eb9b837c60671627c946fb534deb`，与 CIE 公布值一致。
- 两份 PDF 已确认 `%PDF` 文件头，并用 PDF 解析器打开，论文 21 页（含仓储封面）、手册 78 页；样品图已实际查看。


