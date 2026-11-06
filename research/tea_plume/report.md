# 红茶吸收光谱与下沉羽流参照

## 1. 可见光吸收

**找到茶汤实测全谱，以下为读图近似；光程与稀释信息不完全，适合作谱形参照。**

Sentkowska & Pyrzynska (2022), *Does the Type Matter? Verification of Different Tea Types’ Potential in the Synthesis of SeNPs*, **Antioxidants 11, 2489**：[论文全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9774132/)，[DOI](https://doi.org/10.3390/antiox11122489)。数据取 **Figure 1 的 black 黑线**，是合成纳米颗粒前的红茶茶汤，不是图中 red 茶或 SeNPs。[光谱原图](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7dd1/9774132/3a9ecff1ead5/antioxidants-11-02489-g001.jpg)

| 波长 / nm | 吸光度 A，读图约值 |
|---:|---:|
| 400 | 0.34 |
| 450 | 0.15 |
| 500 | 0.07 |
| 550 | 0.04 |
| 600 | 约 0.01（0–0.02） |
| 650 | 约 0.01（0–0.02） |
| 700 | 约 0（0–0.02） |

读图不确定度约 **±0.01 A**；600–700 nm 接近基线及线宽，只能给上述范围，不能把尾部当精密测量。需要相对谱时用 **A(λ)/A(400)**。

**浓度：**§2.2，Basilur（斯里兰卡）研磨茶叶 **2 g / 100 mL 水，60°C、30 min，过滤**。20 g/L 是投叶量，溶解固形物浓度未报，Figure 1 未另说明稀释倍数。**光程：**§2.4 记载 Lambda 20、**1 cm 比色皿**，但该句直接描述 SeNP 合成过程的测量，未单独确认 Figure 1 也用此光程。因此不能据此给出可靠的、按浓度与光程标定的绝对吸收系数。

## 2. 扩散与密度

- **多酚的水中分子扩散：**Srinivas et al. (2011), *Binary diffusion coefficients of phenolic compounds in subcritical water using a chromatographic peak broadening technique*, [原论文](https://doi.org/10.1016/j.fluid.2010.12.003)。同作者 King & Srinivas 的公开实验说明 **AN26，Figure 2**，在 **298 K、无限稀释**读得 catechin hydrate **D≈2.2×10⁻¹⁰ m²/s**，epicatechin **≈2.0×10⁻¹⁰ m²/s**（读图约 ±0.2×10⁻¹⁰）。Taylor–Aris 法，介质为**水加 0.5% v/v 甲酸，pH 2.75–3.00**，并非中性纯水：[原作者实验图与条件 PDF](https://www.teledynelabs.com/en-us/resources/Documents/Application-Notes/Measurement-of-Binary-Diffusion-Coefficients-of-Compounds-at-Infinite-Dilution-in-Water-as-a-Function-of-Temperature-Using-Teledyne-ISCO-Syringe-Pumps.pdf)。未找到 theaflavin / thearubigin 在纯水中的可靠直接 D；茶叶内部浸提的“有效扩散系数”不能代替它。
- **浓茶与水密度差：未找到足以采用的可靠直接实测。**仅作量级估计：假设同温、无糖、溶解固形物 **c=5–20 g/L**、等效溶质密度 **1.5 g/mL**、体积可加，取水密度约 1000 kg/m³，则 **Δρ≈c(1−ρ水/ρ溶质)=1.7–6.7 kg/m³**（约 0.17–0.67%）。这是明确假设下的估计，浓度及溶质密度均非本次查到的茶汤实测；温差也会改变浮力方向。

## 3. 实拍照片（plume/，仅内部视觉参照）

共 **8 张 JPEG**，已逐张查看。保留来源文件，无放大、重绘或新增调色；04、05 从原报告附录直接提取内嵌 JPEG，**不是截图**。这里的“原图”指公开来源文件，未必是相机全分辨率文件。部分为花草茶或植物提取液，不能拿其颜色替代红茶光谱；单张照片也不提供速度或密度标定。

| 文件 | 拍摄内容与来源 |
|---|---|
| `01_botanical_tea_white_background.jpg` | **2048×2048**；白底透明杯，植物茶包下方金棕色团状下沉与卷曲细丝；Betta Botanicals 的水族植物茶，非已确认红茶。[来源页](https://bettabotanicals.com/blogs/bens-aquarium/can-i-use-brewed-tea-in-aquarium) · [原图](https://bettabotanicals.com/cdn/shop/files/Betta-Tea-Brown-Aquarium-Tannin-Extract.jpg) |
| `02_teabag_curling_filaments.jpg` | **1600×902**；白底，茶包下方棕色细流卷成涡头，水面有飞溅；Frekvence 1 配图，署名 Depositphotos，茶种未说明。[来源页](https://www.frekvence1.cz/clanky/zivotni-styl/cajovy-sacek-jako-zazrak-co-se-s-nimi-da-vsechno-delat-nejen-pro-krasu-a-zdravi.shtml) · [原图](https://m.actve.net/frekvence1/2023/05/caj-sacek-cajovy.jpg) |
| `03_backlit_glass_mug.jpg` | **3999×5999**；亮底玻璃杯，红色茶包浸出液与下方清水分界、卷曲云丝；HappyRichStudio / Shutterstock，茶种未说明。[来源页](https://snl.no/diffusjon) · [原图](https://media.snl.no/media/306723/tediffusjon.jpg) |
| `04_berry_tea_mushroom_plumes.jpg` | **734×550**；Wild Berry Zinger 花果茶包下方细丝、蘑菇头与卷涡。Dillon Thorse (2013), *Stalking the Predator*，**附录 Figure A-1 原始照片**；未采用其倒置、大幅改色的封面版。[来源 PDF](https://www.flowvis.org/media/2013spring/GetWet/Reports/Dillon_Thorse.pdf) |
| `05_hibiscus_surface_streams.jpg` | **1430×1073**；白底透明杯，浮在水面的洛神花向下释放细长色流。Daniel Ives (2009), *Tea Time: Flow Physics Involved in Brewing Tea*，约 85°C，**末页 Original Photograph**。[来源 PDF](https://www.flowvis.org/OldGalleries/2009/Get-Wet/Reports/Ives.pdf) |
| `06_cold_hot_tea_comparison.jpg` | **936×937**；左侧冷水中红色细丝下沉并在底部积聚，右侧热水已混匀；Mirjam Sophia Glessmer 实验照片。[来源页](https://mirjamglessmer.com/2021/08/30/molecular-diffusion-at-different-temperatures-involving-tea-bags-and-some-convection/) · [原图](https://mirjamglessmer.com/wp-content/uploads/2021/08/IMG_2048.jpg) |
| `07_cold_brew_carafe.jpg` | **723×722**；窗边透明冷泡壶，茶包下方淡色弯曲羽流，背景较杂、色流较弱；同作者现场照片。[来源页](https://mirjamglessmer.com/2021/08/30/molecular-diffusion-at-different-temperatures-involving-tea-bags-and-some-convection/) · [原图](https://mirjamglessmer.com/wp-content/uploads/2021/08/Screenshot-2021-08-30-at-10.11.31.jpg) |
| `08_herbal_tincture_in_water.jpg` | **956×1069**；透明杯中琥珀色植物酊剂团簇、卷曲下沉；**非茶，含酒精提取物**，只作形态补充。Neal’s Yard Remedies，图片标注 “Herbal tincture in water”。[来源页](https://www.nealsyardremedies.com/blogs/wellbeing/using-herbs-teas-versus-tinctures) · [原图](https://cdn.shopify.com/s/files/1/0628/9129/4940/t/10/assets/untitled-design-58-1678705388710.jpg?v=1678705389) |

检索日期：2026-11-06。
