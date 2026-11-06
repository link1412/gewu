# 摄影背景纸光泽 / BRDF：可核验结果

检索日期：2026-11-02。结论：没有找到 Savage、Colorama 或 BD seamless paper 的公开、可核验 GU / BRDF 实测；找到两组真实纸张的原始实测，可作为明确标注的代理，不能当成这些品牌的材料参数。

## 1. 品牌资料只支持材料描述，不能提供数值

Savage 官方 [Pure White #66](https://savageuniversal.com/us-en/pure-white-seamless-background-paper-107-w-x-36-l-sa-66-config/) 写 fine-tooth / non-reflective、163 g/m²；[White #50](https://savageuniversal.com/global/white-seamless-background-paper-107-w-x-36-l-sa-50-12/) 为 145 g/m²。页面均无 GU、BRDF、测量角度、纸厚或反射率。不能把 non-reflective 解释为零镜面反射或 Lambertian。另已下载 [Savage 2017 品牌目录](Savage_2017_catalogue.pdf)，p.4 同样仅描述 fine-tooth / non-reflective（并给145–180 GSM范围），无光泽仪或BRDF数值。

BD 的品牌目录（经销商镜像：[2018 colour chart](https://www.lecuit.lu/WebRoot/epagesES/Shops/Lecuit/672A/0C9D/1871/9A90/F499/0A0C/05B9/659D/BD_2018_colour_chart_50_colours__5_sizes.pdf)；[本地目录](BD_2018_backgrounds_catalogue.pdf)）与产品搜索仅提供 fine-tooth / non-reflective 描述，未找到仪器值；Colorama 相同方向的检索也未取得可追溯的 GU / BRDF。这里的“未找到”只是本次检索结果，不宣称厂商内部没有数据。

## 2. 最接近目标的可见光纸张角分布：Schramm 1995

原始来源：Morgan Thomas Schramm，1995，*Light Scattering Simulation Using Complex Surface Microstructure Models*，University of Oregon，M.S. thesis。[学校原始 PDF](https://www.cs.uoregon.edu/Reports/MS-199508-Schramm.pdf)。本地：[PDF](Schramm_1995_paper_BRDF_thesis.pdf)。文内页码比 PDF 文件页序少 10（例如 p.85 是 PDF 第 95 页）。

### 原文样品与条件

| 项 | 原文内容与定位 |
|---|---|
| Mountie Matte | Unisource Worldwide 提供，机造，60 g/m²；漂白磨木浆，碳酸钙/黏土涂层，聚苯乙烯黏结剂、碱性施胶；白、光滑、略有光泽。pp.82–83。纸厚未报。**非摄影背景纸；名称 Matte 不等于无镜面峰。** |
| Hand Formed | Potlatch Industries, Cloquet MN 手抄；97% 未漂白针叶木浆（Jack Pine、Red Pine）+ 3% 阔叶浆（Minnesota Aspen）；无填料、涂层、施胶；较粗、略黄、外观漫反射。p.83。厚度及克重未报。 |
| 测量 | 670 nm 激光，S 偏振；入射角相对样品法线；在垂直纸面的半圆内扫描出射角 −90° 至约 +80°；未印纸还旋转 90° 测各向异性。p.84；仪器口径、角步长、测量不确定度未报。 |

### 从原始实测曲线读数（**本报告人工读图，非原文数表**）

角度保留原图符号；峰位置和幅度均为约数，不能当精密数字化数据。BRDF 单位 sr⁻¹，不是总镜面能量或百分反射率。

| 样品 / 原图 | 入射角 | 可检查的曲线量级 | 来源图页 / 本地图 |
|---|---:|---|---|
| 未印 Mountie Matte | 0° | 大多数出射方向约 0.25–0.35 sr⁻¹，法线附近有约 0.4 sr⁻¹ 局部峰；零角附近有明显凹口，来源未在所核读页说明其性质，不据此推断材料特性 | Fig.26a, p.85；[原页](Schramm_1995_p85.png) |
| 未印 Mountie Matte | 45° | 反射方向宽峰约 0.75 sr⁻¹（出射约 −50°）；法线附近约 0.27 sr⁻¹ | Fig.26c, p.85；同上 |
| 未印 Mountie Matte | 75° | 出射约 −70°的峰约 3.0 sr⁻¹；法线附近约 0.2 sr⁻¹ | Fig.26d, p.85；同上；亦 Fig.37a, p.102 |
| 未印 Hand Formed | −45° | 法线附近约 0.15–0.2 sr⁻¹；出射角约 +75°至+85°时约 0.45–0.5 sr⁻¹ | Fig.27a, p.86；[原页](Schramm_1995_p86.png) |
| 未印 Hand Formed | −75° | 法线附近约 0.1–0.2 sr⁻¹；朝反射半空间掠射出射时陡升，未印（粗线）极大约 3.5 sr⁻¹；印黑曲线也升至相近量级，细线极大接近 3.8 sr⁻¹（原图横轴符号/排列见原图；不据此定精确峰角） | Fig.27b, p.86；同上；亦 [Fig.37, p.102](Schramm_1995_p102.png) |
| 未印 Mountie Matte，机器/横向 | 75° | 机器方向峰约 3.0 sr⁻¹；横向峰约 1.3 sr⁻¹，峰宽不同 | Fig.32, p.94；[原页](Schramm_1995_p94.png) |

**推论**：真实无涂纸也会随角度明显增亮；给背景纸设全角度纯 Lambertian 缺少实测支持。但上述峰值只在单色、S 偏振和这两张纸上成立，不能直接用于未知彩色摄影背景纸，更不能将 670 nm 峰值套作全可见光、非偏振数据。页 84 的原文说主要镜面峰在镜面方向附近；表内只读图量级，不自行把峰偏移归因于材料。

## 3. 精确数表：涂层黑纸的 60° GU 与 BRDF 峰宽（非掠射、非背景纸）

原始来源：A. M. Rabal、G. Ged、G. Obein，2019，*What is the true width and height of the specular peak according the level of gloss?*，*Proceedings of 29th CIE Session*，pp.615–621，DOI [10.25039/x46.2019.OP88](https://doi.org/10.25039/x46.2019.OP88)。[CIE 原始 PDF](https://files.cie.co.at/x046_2019/x046-OP88.pdf)，[本地 PDF](Rabal_2019_NCS_paper_BRDF_gloss.pdf)，[原始 Table 3 页图](Rabal_2019_p619_table3.png)。封面说明未经 CIE 同行评审。

样品为 NCS 黑色涂层纸，厚度、克重未报。Table 1（p.616）给的是**标称** 60° GU，不要称为作者另测的 GU。BRDF 由作者用 ConDOR 实测：200 W QTH 灯、V(λ) 滤光、10 mm 光束，入射天顶角 30° / 方位角 180°，入射面内记录，Lorentzian 插值取得峰与 FWHM（pp.617–619）。

| 样品 | 标称 60° GU | 作者给出的 BRDF 最大值 sr⁻¹ | FWHM（°） | 角分辨率（°） |
|---|---:|---:|---:|---:|
| NCS1 | 2 | 未见峰；未给曲线 | 未给 | 未给 |
| NCS2 | 6 | 0.266 | 25.9 | 0.15 |
| NCS3 | 12 | 0.771 | 12.2 | 0.15 |
| NCS4 | 30 | 2.22 | 7.3 | 0.15 |
| NCS5 | 50 | 7.82 | 4.1 | 0.15 |
| NCS6 | 75 | 32.2 | 2.36 | 0.06 |
| NCS7 | 95 | 428 | 0.49 | 0.03 |

定位：NCS1 为 p.618 正文；其余为 p.619 Table 3。**原文内部不一致**：Fig.5 的 NCS2 图标为“4 gu”，NCS4 为“40 gu”；Table 1 和 Table 3 则一致为 6 / 30。这里忠实抄表，不消除此差异；精确拟合前应进一步核对作者数据。

这组数适合说明“哑光涂层纸可以有很宽、很低的镜面瓣”，不构成 Savage / Colorama / BD 的参数，也不回答 75–85° 掠射入射下的峰。

## 4. 单值 GU 的边界及额外下载

[Rhopoint 官方解释](https://www.rhopointamericas.com/faqs/how-is-gloss-measured/)：GU 相对于抛光黑玻璃校准，各角度分别定义，不能把 GU 当入射能量百分比。[TAPPI T480 官方范围](https://imisrise.tappi.org/TAPPI/Products/01/T/0104T480.aspx)：纸张通常采用 75°（相对纸面 15°）方法。60° / 75° / 85°值不能直接互换；单个 GU 也无法唯一确定渲染器 roughness、F0、完整 BRDF。

额外本地材料：

- [Arney et al. 2006，Color Properties of Specular Reflections](Arney_2006_Color_properties_specular_reflections.pdf)，*J. Imaging Sci. Technol.* 50(3):228–232，[原始出版 PDF](https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/jist/50/3/art00002)。未涂、压光纸的 Fig.4 为 20° 固定镜面角、偏振分离的相对角分布，非掠射也非绝对 GU，故未列作主数值。
- [Canon 2024 Matte Coated Paper 90gsm](Canon_2024_Matte_Coated_Paper_90gsm_specs.pdf)：厂商给 127 µm、90 g/m²，Gloss (60°) <5，但同栏写 TAPPI T480（常见几何为75°），存在方法/角度不一致，不能在未澄清前充作精确60°实测。来源：[Canon官方规格PDF](https://s7d1.scene7.com/is/content/canon/MDS-Matte-Coated-Paper-90gsmpdf)。
- [Sönmez & Arslan 2021](pjct_2021_0014_paper_gloss.pdf)，*Polish Journal of Chemical Technology* 23(2):35–40，DOI 10.2478/pjct-2021-0014。170 g/m² matte/gloss coated 数字印刷纸，60° BYK / ISO2813；未提供厚度，GU在印刷/上光研究图中，不是摄影背景纸，未拿来填品牌空缺。

## 5. 供主报告采用的建议

可诚实交付：**品牌背景纸的数值仍受阻；但已有原始实测支持“纸的掠射增强及方向性”，并有其他涂层纸的 GU/BRDF 数表。** 当前渲染只能把这些作为代理校准/敏感性参考。要锁定实际背景，需取得具体纸色/批次样本，至少测60°与85° GU并记录纸纹方向；若目的是拟合镜面瓣，则应测多个入射角下的角分布。此为测量方案建议，非本次已完成测量。


