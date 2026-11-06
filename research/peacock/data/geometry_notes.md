# 蓝孔雀尾上覆羽眼斑几何与真实照片证据

本文件供 report.md 汇总。区分作者实测、作者定性观察、本次按比例尺读图。真实“尾羽眼斑”属于 train 的尾上覆羽，不是飞行用 rectrix。

## 直接可用的已发表几何

| 参数 | 数值 / 事实 | 证据等级、部位 | 原始来源与定位 |
|---|---|---|---|
| 羽小枝细胞 / 节段长度 | 20–30 µm | 作者 SEM 观察；2002 样本是蓝色体羽和黄色尾上覆羽，非眼斑四环的系统采样 | Yoshioka & Kinoshita, Forma 17 (2002) 169–181，p.170 实验取样，p.171 Fig.1，p.172 §3.1；[PDF](../papers/Yoshioka_Kinoshita_2002_Forma.pdf)，[期刊页](https://forma.katachi-jp.com/abstract/1702/17020169.html) |
| 羽小枝形状 | 长轴弯曲；从根部有轻微扭转；连续细胞表面呈鞍形，横截面为新月形 | 作者定性观察；未给曲率半径或总扭角 | 同上 p.172 §3.1、Fig.1B/C；不要自行填一个“实测曲率半径” |
| 眼斑微结构朝向 | R1 紫黑中心的远端细胞强烈侧倾、接近垂直羽片平面；R2–R6 中/远端细胞大致平行羽片平面；R1 根部细胞较平、呈褐色素色 | 直接蓝孔雀尾上覆羽显微观察；不是仅靠吸收解释黑中心 | Freyer & Stavenga (2020), Faraday Discuss. 223,49–62，p.53 Fig.1d–j；p.59–60 Discussion；[PDF](../papers/optics_Freyer_Stavenga_2020_tail.pdf)，[出版页](https://pubs.rsc.org/en/content/articlehtml/2020/fd/d0fd00033g) |
| 眼斑填充与互锁 | R2 羽小枝密集、邻羽枝的羽小枝相互重叠；R3–R6 较松疏；眼斑存在互锁羽小枝和微钩，外侧松散羽枝间隔较大 | 真实 P. cristatus 观察 | Freyer2020 p.53 Fig.1c/d 和 p.60；Dakin et al. (2016), PLOS ONE 11:e0152759，p.17 §3.7 和 p.18 Fig.8F/G；[PDF](../papers/geom_Dakin_2016_biomechanics.pdf)，[出版页](https://doi.org/10.1371/journal.pone.0152759) |
| 青铜色眼斑部分平均直径 | 40.5 mm | Dakin 作者用于视频空间标定的群体平均值；是整体直径，不是青铜环宽 | Dakin2016 p.8 §2.5；没有在该句报告该均值的 SD 或 n |

## 补充直接测量：2024 本科荣誉论文

Noe Oberholtzer Hess & Natalia Dushkina, *Mechanisms and Morphology: An Analysis of Structural Coloration in Peacock Feathers*，Millersville University（2024）。这是学校公开的一手 SEM 研究，**非同行评审论文**。文件 `papers/geom_Oberholtzer_2024_undergraduate_thesis.pdf`；[学校原始 PDF](https://millersville.tind.io/record/109962/files/Oberholtzer_2024_Physics_thesis.pdf)。p.10 Fig.5 明确写 Pavo cristatus，表1 在同页：

| 取样部位 | 节段长，µm，mean ± SD | 羽小枝宽，µm，mean ± SD |
|---|---:|---:|
| 眼斑深蓝 | 25.2 ± 3.26 | 34.5 ± 5.33 |
| 眼斑金色 | 29.4 ± 3.22 | 46.7 ± 2.25 |
| 主轴附近的大羽枝（表中 Main Stem，正文说 purple sample） | 28.6 ± 1.62 | 60.3 ± 3.46 |

作者说明前两种颜色取自同一根羽枝；此处没有给样本数。第三行不能冒充眼斑铜环。p.11 说明羽枝长为厘米量级、羽小枝约 1 mm；这是量级描述，没有分颜色误差条。p.10 Fig.5 比例尺分别为 1 mm / 200 µm / 20 µm，截面是弯曲薄片而非圆柱。应以此作构型支持，不宜用该论文的简化光学解释代替 Freyer2020 的复折射率模型。

## 为渲染提供的单样本读图估计（非原论文参数表）

原图：`photos/Freyer_2020_Fig1_cristatus_train_macro_micro_CC-BY-NC-3.0.jpg`，971×1155，直接提取自 PDF page6 (= 期刊 p.53) 的原始嵌入 JPEG，未调色/增强。Fig.1a 比例尺为 20 mm；黑线端点约 (291,638) 到 (408,638)，117 px = 20 mm，5.85 px/mm。取图中眼斑右侧固定水平截线 y=420：

| 色区 | 手工像素边界 x | 该水平截线上投影宽 |
|---|---|---:|
| R2 蓝绿 | 282–307 | 约 4.3 mm |
| R3 褐 / 青铜 | 307–331 | 约 4.1 mm |
| R4 绿黄 | 331–347 | 约 2.7 mm |
| R5 紫 | 347–359 | 约 2.1 mm |

每个色界约 ±3 px；综合宽度误差建议按约 ±1 mm 对待。**是这一个样本的这条截线，不是各色环的普适宽度，也不是沿色界法线的精确厚度**；环在上、下、左、右明显不等宽，外圈 R6 与松散羽枝混合，没有清晰可定义外界。1–2 cm 画面确实能同时跨越数条色带。CSV `data/geometry_figure_estimates.csv` 保存坐标、单位与证据类别，`scripts/measure_geometry_figure.py` 可复现算术。

同图1b 中两条可辨羽枝的投影方向，相对局部垂直羽轴约 47° 和 50°（±5°，手工选取局部线段），不能当作全部羽枝的固定夹角。在 b 图 5 mm 比例尺下，局部羽枝之间沿羽轴的节距约亚毫米，图像足以校准渲染纹理密度，但此处未拟合一个跨部位统一节距。本次没有找到足以直接确立蓝孔雀眼斑羽枝截面宽/厚、全羽小枝节距、三维扭角及曲率半径的同行评审参数表；这些不要伪装成已测量数据。更可靠的建模是按照片布置弯曲羽枝/羽小枝和局部法线，以实测细胞长宽约束细部。

## 照片用途和比例尺

详见 `data/photo_sources.csv`。优先看真实 P. cristatus 的 Freyer2020 Fig.1：a 是完整眼斑、b/c/d 是羽枝及边缘、e–j 是各色细胞真显微照片，原图含 20 mm / 5 mm / 1 mm / 50 µm 比例尺。另存 a 和 c/d 原样裁切，比例尺仍在；这些是同一组实验照片，不是额外个体。

Dakin2016 Fig.8F/G 是真实眼斑 SEM，1 mm 和 300 µm 标尺，可核查互锁和微钩，但不能作色彩真值。Mister rf 2023 Commons 照片是高分辨率真实拍摄的眼斑，3375×2594；作者声明焦点堆栈和去背景，无比例尺、无标准光源或反射率标定，物种在图片页未明确，故仅作外观和构图参考，不能代替蓝孔雀参数测量。
