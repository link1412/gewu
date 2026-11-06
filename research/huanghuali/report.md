# 黄花梨家具「鬼脸」纹：几何、光学与程序化渲染参考

检索与文件核验日期：2026-11-02。目标物种为降香黄檀 **Dalbergia odorifera**；器物目录中的“黄花梨”、相近黄檀和其他硬木，均另作标记。本文中的“实测”“文献模型”“推导”“试做建议”具有不同证据强度，建议参数不冒充物种常数。

## 结论与推荐路线

推荐采用 **三维主干/枝节骨架与生长场 + 独立的深色条带与导管 + 三维纤维反射 + 独立蜡面高光**。决定性依据是：专门的节疤程序模型能给出随锯切面变化的眼形和绕节生长纹；纤维高光需要三维方向，只有底色贴图或平面各向异性 GGX 会丢掉随视角改变的木材光彩。[Larsson 2022](https://doi.org/10.1145/3528223.3530081)、[Marschner 2005](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)

| 路线 | 优点与代价 | 本项目选择 |
|---|---|---|
| 照片底色 + 普通涂层 PBR | 最快接近一张正面照片；切面与光彩缺乏一致性 | 可作外观对照和颜色拟合起点 |
| 圆柱年轮 + 拉伸噪声 | 便于生成普通顺纹；缺少枝节拓扑，容易成为规则同心圆或“大理石” | 只用于无节区域的基础层 |
| 骨架生长场 + 细观结构 + 纤维 BRDF | 要处理枝节、形变导数和多项反射，但能保持切面和光照一致 | **推荐**；节疤取 Larsson，细观结构/方向场取 Liu，反射取 Marschner。均需针对黄花梨重新拟合颜色。[原始模型](https://www.ma-la.com/procedural_knots.html)、[细观模型](https://www.cs.cornell.edu/projects/wood/) |

可检查的后续渲染完成标准：① 鬼脸外圈与周围顺纹连续；② 正切、斜切及邻接面保持三维一致；③ 移动光源时出现有色纤维亮暗变化，同时保留独立的近无色表面灯光反射；④ 导管不会放大成橡木粗孔；⑤ 每个参数清楚标识是实测、代理还是美术拟合。**本次交付是研究与素材包，没有声称已完成黄花梨材质的渲染实现或实物标定。**

## 1. 鬼脸纹的成因、几何与尺度

### 1.1 “鬼脸”是外观名称，不是单一解剖结构

中国（海南）南海博物馆把鬼脸纹解释为枝节处的自然结节；一般木材的节是枝条在主干内留下的结构，邻近主干生长纹因之偏转。切面不同，同一个节可以表现成圆眼、椭圆、弯曲锥形以及带长尾的眼形。[博物馆纹理介绍](https://www.nanhaimuseum.org/n1/2021/0709/c418250-32153803-2.html)、[Larsson 2022 §1、Fig.2](https://www.ma-la.com/procedural_knots/Procedural_Knots_2022.pdf)

应区分以下结构，而不把所有花纹都解释为一个黑色节心：

| 外观 | 适合的几何解释 | 对建模的含义 |
|---|---|---|
| 单眼、套眼、长尾眼 | 枝节轴与锯切面的交会；主干纹带绕节偏转 | 主干场和分枝场要共同参与，中心与外围不能互不相干 |
| 双眼、多个眼与面具状组合 | 多个局部中心及其周围纹带的联合构图 | 由数个不完全对称的枝节/扰动共同控制，避免复制一个眼形图章 |
| 瘿木、密集涡纹、分叉羽状纹 | 瘿、局部异常生长、较大分叉的复杂结构 | 与普通单节分开参数化；Liu 明确将 knots、burls、crotch figure 分列。[Liu 2016 §7](https://www.cs.cornell.edu/projects/wood/simulating_the_structure_and_texture_of_solid_wood.pdf) |

行业文章还把某些小斑点、外伤和树瘤纳入“鬼脸”。这些名称覆盖不同现象，尚不足以给每种“脸”指定唯一生物成因；本文只把它们作为外观分类线索。[行业分类原页](https://m-news.artron.net/19700101/n808028.html) 其中“直径通常不超过 1 cm”的说法只针对该文自定义的一类小斑点，**不能作为所有鬼脸、节疤或整张面具的尺寸上限**。

“涡纹”也不应自动理解为数学上的螺旋涡流。实物经常是偏心闭合曲线、嵌套眼形与绕节条带，局部又连接到长顺纹。先满足这些连接关系，再加入不规则变化，比叠加旋转噪声更接近结构；这是依据节疤模型和本地照片作出的建模判断。[节疤结构模型](https://www.ma-la.com/procedural_knots.html)、[双眼照片来源](https://www.huitu.com/photo/show/20191214/212036778020.html)

### 1.2 可以直接使用的几何表达

**基本剖切关系（几何推导）：**把局部枝节近似成半径 `r` 的圆柱，轴向单位向量为 `a`，切面法线为 `n`。忽略锥度时，切出的椭圆短半轴约为 `r`，长半轴约为 `r / |n·a|`。枝轴接近垂直板面时近圆；接近平行板面时强烈拉长。真实枝节有弯曲、锥度、死亡与包覆，此公式只用于理解方向，不能在 `|n·a|→0` 时无限拉长。该推导与论文中切面改变节形的示例一致。[Larsson Fig.2](https://www.ma-la.com/procedural_knots/Procedural_Knots_2022.pdf)

**生长场：**Larsson 用主干和各枝节的骨架构建“材料何时长到此处”的三维标量场，再以平滑最小值合并，各等值面对应生长层；还专门处理死节与周围变形。源码中主干有 `t_s=d_s/r_s`，并通过 `power_smooth_min` 合并分枝场。它比在二维图上画同心环更适合家具倒角、曲面和多面切削。[论文 §4](https://doi.org/10.1145/3528223.3530081)、[已核查的 GLSL 原码](https://raw.githubusercontent.com/marialarsson/procedural_knots/main/setup/main.frag)、[本地副本](sources/knots-main.frag)

**纤维方向：**若 `q=f(p)` 把变形后的木材点映回未变形树空间，初始纤维沿 `u₀=(0,0,1)`，则

```text
u(p) = normalize(inverse(J_f(p)) · u₀)
```

这来自 Liu 的逆 Jacobian 向量场变换；只把同一个常量方向场换坐标采样，不会得到弯曲方向。要求局部映射可逆。在主干/枝节融合区需另外构造连续的纤维场：**不能直接把生长场梯度 ∇t 当纤维轴**，它指向生长层法向而非轴向。[Liu 2016 §4.5](https://www.cs.cornell.edu/projects/wood/simulating_the_structure_and_texture_of_solid_wood.pdf) 后一句是由标量场/方向场含义作出的推导。

### 1.3 解剖尺度：明确区分端面测量与纵面外观

| 项目 | 数据、样品与单位 | 渲染解释及出处 |
|---|---|---|
| 降香黄檀导管直径 | CITESwoodID 记录 `50–160–280 µm`（其范围/代表值格式），约 `0.05–0.28 mm` | 是横截面管孔尺度；纵切常成为细长断续沟纹。[物种原条目](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm) |
| 降香黄檀导管密度与组合 | `3–12 个/mm²`；常有 `2–3` 个径列复管孔，少数更长径列 | 是**端面计数密度**，不能直接拿来当纵面每平方毫米的独立坑数。[CITESwoodID](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm) |
| 导管内部 | 心材导管有沉积物；数据库未记载侵填体 | 不宜全部画成纯黑、空心、贯通的洞。[CITESwoodID](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm) |
| 生长轮边界 | 可明显，也可不明显/缺失；局部以边缘薄壁组织及少管孔暗带界定 | 因此深色条带不能全部强制“一条=一年”。[CITESwoodID](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm) |
| 降香黄檀射线宽度 | 薄壁组织带内，各产地平均值 `21.59–36.23 µm`；属产地均值范围，不是单根极值 | 比导管更细，适合作为近景微细结构。[黄向党等 2018，p.141](https://hndk.hainanu.edu.cn/cn/article/pdf/preview/10.15886/j.cnki.hdxbzkb.2018.0018.pdf) |
| 降香黄檀射线细胞数 | 同一研究以双列为主；高度约 `5–8` 个细胞 | 不应直接换算成毫米高；要有细胞尺寸才能换算。[黄向党等 2018，pp.142–144](https://hndk.hainanu.edu.cn/cn/article/pdf/preview/10.15886/j.cnki.hdxbzkb.2018.0018.pdf) |
| 同属纤维代理：D. assamica | 纤维长 `971.91±198.4 µm`、宽 `22.43±1.77 µm` | **非降香黄檀**；说明纤维约几十微米宽、近毫米长的尺度层级。[18 树种实测，Table 2](https://www.mdpi.com/1999-4907/14/12/2344) |
| 同属纤维代理：D. sissoo | 纤维长 `925–1287 µm`、直径 `19–23 µm`；导管分子长 `152–188 µm` | **非降香黄檀**；导管分子长度不等于整条导管或纵面可见沟纹长度。[原始研究摘要](https://doi.org/10.1007/s11676-014-0002-z) |

黄花梨是有导管的阔叶材；讨论 Marschner 的 fiber/tracheid 散射时，应采用“纤维细胞的方向性散射”作为机制代理，不宜把针叶材以管胞为主的解剖组成原样搬来。[物种解剖](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm)、[Marschner §2](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)

**年轮宽度有可用的物种证据，但要作换算。**梁建平等对南宁人工林的树干解析，在 p.525 §3.2 报告胸径连年增量：`14–28 年生约 0.4 cm/年`，`32–46 年生约 0.2–0.3 cm/年`。将直径增量除以二，可推得对应平均径向生长尺度约 `2 mm/年`、`1–1.5 mm/年`。这是**由直径增量换算的尺度**，不是逐环显微测量，更不是古家具老料的统一年轮宽度。[原文与 PDF](https://zlxb.zafu.edu.cn/article/doi/10.11833/j.issn.2095-0756.2015.04.005)、[本地 PDF](papers/odorifera-growth-2015.pdf)

据此，试做时可把约 `1–2 mm` 作为基础生长层径向间距的起点，再加入年际与周向变化；这属于上述人工林数据支持的**初始假设**。板面条带间距还受到切向位置和倾斜影响，不能用表面纹带的间距直接倒推出年轮宽度。[上述生长研究](https://zlxb.zafu.edu.cn/article/doi/10.11833/j.issn.2095-0756.2015.04.005)、[三维切面模型](https://www.cs.cornell.edu/projects/wood/)

没有找到可信的降香黄檀“鬼脸直径、眼距、涡纹节距”总体分布。建议由目标照片和器物尺寸拟合这些宏观参数，避免把行业审美描述当成生物统计。

### 1.4 深浅纹带与几何应相关，但不必同源

降香黄檀具有色条纹、带状/翼状/聚翼状薄壁组织与心材导管沉积；心材形成又涉及薄壁细胞中次生代谢物的积累。因此程序中应保留独立的颜色/吸收调制，而不是仅靠早晚材周期产生全部黑线。[CITES 解剖条目](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm)、[降香黄檀心材形成原始研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC10644609/)

这不等于已经证明“每条黑线都是某一种提取物”。适宜做法是让颜色条带、导管与纤维方向共同随结构形变，但分别调节浓淡、频率、断续和对比；对特定黑带的化学归因，现有证据不足。

## 2. 反射光谱、颜色与蜡后光泽

### 2.1 降香黄檀实测颜色：粉末，不是家具板面

He 等（2023）测量经鉴定的降香黄檀心材药材：`40 目`粉末，每批约 `10 g`，HunterLab UltraScan VIS、`D65`、`SCE`（排除镜面分量），每批三次。符合标准的 `54 批`统计如下；没有蜡层，也没有径切/弦切板面条件。[§4.4、Table 1](https://doi.org/10.3390/molecules28227635)、[本地论文](papers/optics-he2023-dalbergia-color.pdf)

| 量 | 最小—最大 | 均值 ± 标准差 | 数据出处 |
|---|---:|---:|---|
| L* | 38.98—52.91 | 44.59 ± 3.29 | [He 2023 Table 1](https://doi.org/10.3390/molecules28227635) |
| a* | 5.93—12.84 | 9.71 ± 1.65 | [同表](https://doi.org/10.3390/molecules28227635) |
| b* | 3.83—16.88 | 9.44 ± 2.93 | [同表](https://doi.org/10.3390/molecules28227635) |

该组数值约束的是特定粉末样品。**不能直接填入 sRGB、线性 baseColor，也不能由三个 Lab 值唯一反推光谱。**器物照片中常见金黄、琥珀、红褐和深色纹带，但照片受照明、白平衡、老化及表面处理影响；本报告不把照片取色伪装为反射率。[原测量条件](https://doi.org/10.3390/molecules28227635)、[器物照片例](https://www.christies.com/lot/lot-6130033)

### 2.2 同属黄檀的可见—近红外实测曲线

Chen 等（2024）研究十种黄檀，包括 D. latifolia、D. oliveri、D. retusa 等，**不含 D. odorifera**。气干样品含水率 `11%–11.5%`，打磨横切面，`350 W` 卤素灯、`45°` 照明，白板标称反射率 `99.9%`；范围 `383–2386 nm`，Vis 与 NIR 采样间隔分别 `1.4 nm` 和 `6.2 nm`。[§2、Table 2](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1413215/full)、[本地论文](papers/optics-chen2024-dalbergia-spectra.pdf)

![十种黄檀的 Vis/NIR 原始图，左图包括可见波段](img/optics-dalbergia-visnir-spectra-1.jpg)

图源：[Figure 3](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1413215/full)。本地文件从论文内嵌图提取。左侧可见段可用于同属曲线形状比较；右侧部分 NIR 曲线超过 `1`，不可在未核清校正/尺度前直接当作绝对能量反射率。该文是光谱分类实验，不是黄花梨蜡面 BRDF 数据集。

随文未找到公开的逐波长反射率 CSV；数据声明是可向作者获取，补充材料主要为分类参数。[数据声明](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1413215/full)

### 2.3 可见谱的另一组代理：热带硬木，注意纵轴为 K/S

Jurczyková 等（2023）测实木对照组与热处理组：Konica Minolta CM-5，`360–740 nm`、`10 nm` 分辨率、`3 mm` 测量斑、`D65/2°`、**SCI（包含镜面分量）**，每组四谱平均。Figure 5 给出由反射率变换的 Kubelka–Munk `K/S`。[§2.3.1、Figure 5](https://doi.org/10.3390/polym15194000)、[本地论文](papers/optics-jurczykova2023-tropical-spectra.pdf)

![六种热带硬木的可见谱变换 K/S，含未处理对照](img/optics-tropical-visible-spectra-figure5.png)

图源：[原文 Figure 5](https://doi.org/10.3390/polym15194000)。先选 `Ref.` 未热处理曲线，再数字化。若 `q=K/S=(1−R)²/(2R)`，反算为：

```text
R = 1 + q − sqrt(q² + 2q)
```

公式是上述定义的代数反解。`K/S` 不能直接填入反射率槽；图上读点只能标注为近似重建，本次没有捏造原始 R 数表。SCI 总反射数据与 SCE 色度、或着色器的纯漫射 albedo 也不能无条件互换。[测量定义](https://doi.org/10.3390/polym15194000)

该文未热处理实木对照的色度可作为不同色调代理：

| 代理材 | L* | a* | b* | 出处与适用性 |
|---|---:|---:|---:|---|
| Padouk，Pterocarpus soyauxii | 39.45 ± 0.81 | 29.00 ± 0.73 | 30.57 ± 1.35 | [Table 2](https://doi.org/10.3390/polym15194000)；非降香黄檀、非蜡面 |
| Merbau，Intsia spp. | 39.29 ± 3.26 | 13.54 ± 0.91 | 23.50 ± 4.55 | [Table 2](https://doi.org/10.3390/polym15194000)；同上 |
| Teak，Tectona grandis | 40.38 ± 1.17 | 14.77 ± 0.23 | 30.19 ± 0.39 | [Table 2](https://doi.org/10.3390/polym15194000)；同上 |

### 2.4 打蜡后的显色和光泽：工艺决定结果

**较贴近传统热蜡的代理：黑胡桃。**Zhang 与 Song（2024）使用蜂蜡与虫白蜡的天然热蜡；未加填料的 `NW` 条件，Lab 从裸材 `(45.4, 5.4, 8.3)` 变为 `(36.8, 9.7, 15.3)`，表现为变深、偏红黄。该结果来自黑胡桃，不能当作黄花梨固定的色差倍率。[Table 2、方法](https://doi.org/10.3390/f15122262)、[本地论文](papers/optics-zhang2024-hotwax-mcc.pdf)

![黑胡桃裸材、天然热蜡及不同填料处理的外观与光泽](img/optics-hotwax-appearance-gloss-figure4.png)

图源：[Figure 4](https://doi.org/10.3390/f15122262)。`NW` 才是未加填料天然热蜡；其他组不是普通蜡面。光泽按 ASTM D523 在 `60°` 测量，数值主要以箱线图呈现，本文不把估读位置写成精确实测表。它也说明蜡层微观结构能改变光泽，不能一概宣称“打蜡一定得到镜面”。

**另一个可复现的蜡膜尺度：**Liu 等（2022）在欧洲枫与胡桃上将蜂蜡或虫白蜡按 `50 g/250 mL` 白电油配制，五层、每层约 `25 g/m²`、间隔 `24 h`，最后毡盘抛光，得到约 **20 µm** 顶层蜡膜。这只代表该配方与流程，不是黄花梨家具的通用蜡厚。[§2.1](https://doi.org/10.3390/coatings12111689)、[本地论文](papers/optics-liu2022-beeswax-chinese-wax.pdf)

补充的数值实例为白橡刷涂蜡油混合物实验；其期刊来源较弱、工艺也不等于传统热蜡，应低权重使用：

| 白橡 `60°` 光泽，GU | 裸材 | 1 层 | 2 层 | 3 层 | 出处 |
|---|---:|---:|---:|---:|---|
| 横纹 ⊥ | 2.38 | 3.83 | 3.12 | 4.78 | [Ayata 2024 Table 9](https://crimsonpublishers.com/mcda/pdf/MCDA.000840.pdf) |
| 顺纹 ∥ | 2.63 | 3.53 | 3.64 | 5.44 | [同表](https://crimsonpublishers.com/mcda/pdf/MCDA.000840.pdf) |

实验用了中性天然/合成蜡油、`30%` 干残留；按 ISO 2813 测量。[原始方法](https://crimsonpublishers.com/mcda/pdf/MCDA.000840.pdf) **GU 是相对光泽标度，不是反射率百分数，也不能直接除以一百变成 roughness。**该 PDF 地址下载时返回 HTML，未保留为伪 PDF。

## 3. 木材各向异性高光：Marschner 2005 与可迁移参数

### 3.1 两种高光要分开

Marschner 等测的是带透明饰面的胡桃、卷曲枫与交错纹 padauk，未测降香黄檀或蜡面。论文观察到近无色的表面高光与有色的次表面纤维高光；后者由三维纤维轴决定，局部轴可以倾入/倾出板面，形成随视角/照明移动的光彩。[论文 §2–4、Fig.6/9](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)、[本地 PDF](papers/optics-marschner2005-finished-wood.pdf)

将细胞壁近似为折射率 **1.55** 的介质，令 `u` 为纤维轴，`s(vi)`、`s(vr)` 为折射后的入、出射方向（沿论文约定），方向性反射满足：

```text
u · s(vr) = −u · s(vi)
```

这是绕纤维轴的一组锥向反射方向，不等同于把平面内 anisotropic tangent 旋转一下。`1.55` 是论文的细胞壁近似值，不是测得的黄花梨蜡层 IOR。[§2.2](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)

### 3.2 模型公式和参数语义

沿用原文符号：

```text
fr = fs + (1−Fi)(1−Fr) [ρd + ff]
ff = kf · g(β, ψh) / cos²(ψd/2)
ψi = asin(s(vi)·u), ψr = asin(s(vr)·u)
ψh = ψr + ψi,      ψd = ψr − ψi
g(β,x) = exp(−x²/(2β²)) / (β sqrt(2π))
```

`fs` 是表面高光；`ρd` 为原文定义的漫射项；`kf` 为有色纤维项强度；`β` 为纤维锥展宽；`Fi/Fr` 是表面界面 Fresnel。`ρd` 不应未经核对就当作现代引擎的 albedo/π。论文自身称该模型为物理启发的现象模型，并未严格处理全部辐射度量。[§4](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)

### 3.3 官方资产中实际存在的参数

[作者项目页](https://www.cs.cornell.edu/~srm/publications/SG05-wood.html) 提供 [测量纹理与 RenderMan shader 数据包](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz)。本地已保存[原包](papers/optics-marschner2005-data.tgz)与[解包目录](papers/optics-marschner2005-data/)，其中有 diffuse/fiber/axis/beta 的线性 TIFF 和 [woodreflectance.sl](papers/optics-marschner2005-data/supplemental_0142/woodreflectance.sl)。这是作者公开实现；未找到包内独立开源许可证，不能称为 MIT/BSD 代码。

| 参数/资产 | 核查值 | 含义与出处 |
|---|---|---|
| `eta` 默认 | `1.5` | finish IOR；不是细胞壁 `1.55`。[作者代码](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| `beta` 默认 | `0.1745 rad ≈ 10°` | 纤维反射展宽。[作者代码](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| `cmaple`、`walnut1` β 纹理 | `10294/65535 ≈ 0.157076 rad ≈ 9°` | 本次读取原 TIFF 的结果；非黄花梨测量。[原 TIFF 包](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| `walnut2`、`padauk` 非零 β | `11438/65535 ≈ 0.174533 rad ≈ 10°` | padauk 零边界不当作有效 β。[原 TIFF 包](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| 表面 `roughness` 默认 | `0.2` | shader 用 `pow(N·H,1/roughness)`，相应指数为 `5`；**不是 GGX α**。[作者代码](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| fiber 图解码 | 线性值乘 `20` | 文件存储时有缩放；不是 `[0,1]` albedo。[作者代码注释与实现](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| axis 图解码 | `2*rgb−1` 后换基、归一化 | 纹理分支的 y 分量还取负号；移植需核对坐标系。[作者代码](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |

**复现陷阱：**官方 shader 第 194 行用 `β·exp(−(ψh/β)²/2)/sqrt(2π)`；论文写归一化 Gaussian，数学上应除以 `β`。两者幅度相差 `β²`。若复刻原资产，先维持原代码的幅度约定；若改为归一化形式，应重新拟合 `kf`，不能混用参数。[本地源码](papers/optics-marschner2005-data/supplemental_0142/woodreflectance.sl)、[论文定义](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf) 另外，注释说 `eta=0` 代表无涂层，实际折射分支检查 `eta != 1`；按代码关闭折射应使用 `eta=1`。

### 3.4 黄花梨试做参数与校准方法

| 控制量 | 建议起点/获取方法 | 证据级别 |
|---|---|---|
| 基础生长层径向间距 | 约 `1–2 mm`，局部不均匀；不得把所有黑纹锁在轮界 | 由降香黄檀人工林径增量换算的起点，见[§1.3 原文](https://zlxb.zafu.edu.cn/article/doi/10.11833/j.issn.2095-0756.2015.04.005) |
| 导管端面直径 | 在 `0.05–0.28 mm` 范围内变化 | 物种数据库，见[CITES](https://www.delta-intkey.com/citeswood/en/www/fabfaodo.htm)；纵面由三维管结构切出 |
| 鬼脸中心、眼距、影响范围 | 按选定器物照片拟合，避免统一重复 | 无可信总体统计；属于美术参数 |
| finish IOR | 先用 `1.5` 代理；`F0=((η−1)/(η+1))²=0.04` | 作者硬木代码起点与 Fresnel 公式推导；**非黄花梨蜡实测**。[作者资产](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz) |
| fiber β | 先用 `9–10°`；强度另外拟合 | 作者代理硬木资产；见上表，**非物种常数** |
| 漫射与纤维颜色 | 分开拟合；黑带也不必一概没有纤维反射 | 模型结构依据 [Marschner](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)，颜色由目标样品决定 |
| 表面粗糙度/蜡厚 | 不给统一 GGX 数；用灯具反射宽度拟合，厚度仅在显式涂层模型里使用 | 蜡工艺数据不能直接决定 roughness；[蜡膜实验](https://doi.org/10.3390/coatings12111689)仅提供一个约 `20 µm` 工艺实例 |

建议固定曝光与白平衡，先用柔光观察颜色和条带，再移动小光源检查有色高光，最后用大面积白灯校准表面高光宽度。鬼脸周围的三维轴 `u` 必须随结构变化，不能只改 tangent 的平面旋转。普通 PBR 可作为快速代理，但它不具备完整纤维锥机制。[模型依据](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)

## 4. 可复用程序化模型与源码

| 资源 | 已核实的内容 | 对本目标的用途与限制 |
|---|---|---|
| **Larsson 等，2022，Procedural Texturing of Solid Wood with Knots** | [项目](https://www.ma-la.com/procedural_knots.html)、[论文](https://doi.org/10.1145/3528223.3530081)、[GitHub](https://github.com/marialarsson/procedural_knots)；PyOpenGL + GLSL，MIT。[本地许可](sources/knots-LICENSE.txt)、[本地 shader](sources/knots-main.frag) | **节疤首选**：主干/枝节生长场、平滑合并、死节。论文示例主要是松/云杉等，不自带黄花梨颜色、孔隙和 BRDF。不能把其针叶材预设直接当黄花梨 |
| **Liu、Dong、Hašan、Marschner，2016，Simulating the Structure and Texture of Solid Wood** | [作者项目](https://www.cs.cornell.edu/projects/wood/)、[本地论文](papers/solid-wood-2016.pdf)；三维年轮、颜色、导管、射线、形变和纤维方向；有补充视频 | **微细结构与方向场首选**。原文结尾将节疤、瘿、分叉列为后续工作，不能当现成鬼脸生成器。本次项目页未发现完整可下载源码，不能标为已开源 |
| Liu、Marschner、Dye，2015，Procedural Wood Textures | [arXiv](https://arxiv.org/abs/1511.04224)、[本地预印本](papers/procedural-wood-2015.pdf) | 更早的完整程序化木纹论述；有三维、随机访问、模块化设计。与 2016 作者和版本不同，不能混作同一论文 |
| **Marschner 等，2005，Measuring and Modeling the Appearance of Finished Wood** | [作者页](https://www.cs.cornell.edu/~srm/publications/SG05-wood.html)、[数据包](papers/optics-marschner2005-data.tgz)、[本地 shader](papers/optics-marschner2005-data/supplemental_0142/woodreflectance.sl) | **反射首选**：可迁移公式、参数贴图和作者 RenderMan 实现。不是纹理几何生成器；老式 shader 需要移植，下载公开不代表独立开源授权 |
| clarkx/ProceduralWood | [仓库](https://github.com/clarkx/ProceduralWood)、[GPL-3.0 许可](https://github.com/clarkx/ProceduralWood/blob/master/LICENSE)、[Blend 文件](https://github.com/clarkx/ProceduralWood/blob/master/WoodProceduralTexture5.blend) | 快速 Blender 节点参考，有轮、条纹、孔隙、bump 等控制；未证明具有枝节生长拓扑或三维纤维 BRDF，不能当学术模型等价替代。未在本次运行 Blender 验证兼容性 |
| Nindel 等，Automatic inference of a anatomically meaningful solid wood texture from a single photograph | [arXiv 记录](https://arxiv.org/abs/2302.01820)、[本地当前修订 PDF](papers/wood-inference-2025.pdf)；从曲线 Gabor 检测与相位损失匹配生长轮 | 适合从照片初始化结构与形变；不能从单张普通照片唯一识别三维纤维轴或完整 BRDF。本次未确认现成可运行公开仓库；初稿发表于 2023，所下载版本为 2025 修订 |

**推荐组合的边界：**Larsson 的融合生长场与 Liu 的可逆形变场并不是插入两段代码便天然兼容；要明确共享的树空间、比例和分枝坐标架，并单独验证融合区纤维连续性。模型中保留以下输出即可让几何和光学有共同依据：

```text
growth_time / ring_phase
streak_or_absorption_mask
vessel_mask / pore_height
fiber_axis_3D
diffuse_color, fiber_color, fiber_beta
finish_IOR, finish_roughness
```

此接口是本报告的整合建议，不是文献现成 API。先做一个单节、再做双节、最后加导管与蜡层；使用跨切面和移动光源检验结构，避免只对一张正面图调得像。

## 5. 高清照片与本地外观参考

### 5.1 原图尺寸、看什么、不能据此推断什么

下表尺寸为**本次解码本地文件实际读取**。拍卖行/展览名称是来源的材质定名，不等于本次做过显微或 DNA 树种鉴定。拍摄光照和饰面工艺不详，均不用于绝对色度或粗糙度测量。

| 本地图片 | 实际像素 | 来源与用途 |
|---|---:|---|
| [方角柜](img/bonhams-cabinet.jpg) | 2313 × 2880 | [Bonhams 原文](https://bonhams.shorthandstories.com/collecting-101-huanghuali-chinese-furniture/)；推荐主要家具参照：门板中的眼形、长纹和局部偏转；放大左门下部观察 |
| [成对圆角柜](img/bonhams-cabinets.jpg) | 3427 × 2880 | [同一原文](https://bonhams.shorthandstories.com/collecting-101-huanghuali-chinese-furniture/)；红褐色、素面板的整体分布与纹带疏密；不是微距孔隙测量图 |
| [黄花梨笔筒](img/bonhams-brushpot.jpg) | 2746 × 2880 | [同一原文](https://bonhams.shorthandstories.com/collecting-101-huanghuali-chinese-furniture/)；整器物图，适合看弯曲表面上的纹理，不应误称板面微距 |
| [黄花梨桌](img/bonhams-table.jpg) | 3451 × 2880 | [同一原文](https://bonhams.shorthandstories.com/collecting-101-huanghuali-chinese-furniture/)；整体颜色与细腻度补充，**不是鬼脸特写** |
| [“黄花梨鬼脸纹”展陈](img/ghostface-museum-display.jpg) | 1170 × 1560 | [新湖南展览报道](https://m.voc.com.cn/xhn/news/202311/18911159.html)；标签和长板整体构图可核对，现场照明强，细节分辨率有限 |
| [双眼近景，有水印预览](img/huitu-ghostface-preview.jpg) | 900 × 600 | [摄影师天崖图客/汇图原页](https://www.huitu.com/photo/show/20191214/212036778020.html)；**最直观的双眼与外圈连续形状参照**。页面标称付费原图为 `5760 × 3840`，本地仅为公开预览，未购买或声称已取得原图 |
| [鬼脸近景 1](img/ghostface-sohu-01.jpg) | 487 × 493 | [原文](https://www.sohu.com/a/430166865_414800)；单眼与白色灯具反射可见；来源较弱，只作形状参照，非高清 |
| [鬼脸近景 2](img/ghostface-sohu-02.jpg) | 560 × 562 | [原文](https://www.sohu.com/a/500140779_121124711)；多眼组合与外围顺纹；非高清、未独立鉴定 |
| [黄花梨方盒](img/huanghuali-box-detail.jpg) | 600 × 800 | [Ben Janssens 器物原页](https://www.benjanssens.com/portfolio/huanghuali-square-box/)明确指出盒盖的 ghost face；适合观察小器物构图，非高清 |

![双眼形状公开预览，保留原水印](img/huitu-ghostface-preview.jpg)

图源：[汇图摄影原页](https://www.huitu.com/photo/show/20191214/212036778020.html)。重点看两眼并非完全镜像，外圈长纹与周围顺纹相接，黑带宽度和对比有变化。该图颜色很浓，不能当色卡。

![家具尺度的纹理分布](img/bonhams-cabinet.jpg)

图源：[Bonhams](https://bonhams.shorthandstories.com/collecting-101-huanghuali-chinese-furniture/)。放大原文件查看纹理；整块门板中的鬼脸占比较小，适合纠正把家具做成满版巨大面具的倾向。

### 5.2 额外的高价值在线原图入口与实际限制

- [Christie's，成对方角柜，lot 6130033](https://www.christies.com/lot/lot-6130033)：目录明确说明门板和可拆背板有丰富 ghost-face knots，是很贴题的家具参考。器物页可读，但本次图片 CDN 请求失败；没有用缩略图冒充下载成功。
- [Christie's，18 世纪笔筒，lot 5623516](https://www.christies.com/en/lot/lot-5623516)：目录明确写有 ghost-face inclusions，适合与家具面板对照；同样未能从其 CDN 稳定下载原图。
- [汇图摄影原图入口](https://www.huitu.com/photo/show/20191214/212036778020.html)：明确标称 `5760 × 3840` 的鬼脸近景，若需要逐根纹理的更高清参照，这是比继续放大低清转载更直接的来源；本次只下载无需登录的水印预览。

**已获得的是高清器物照片 + 明确鬼脸的中低清近景 + 高清鬼脸原图入口。未获得无水印的 5K 鬼脸微距原图。**此处如实区分；普通器物的 3K 文件不自动等于鬼脸局部也有 3K 细节。图片仅作外观参照，保留水印和来源，不作授权不限的素材库声明。

## 6. 论文与资产索引、验证和待补数据

### 6.1 已下载论文

| 本地文件 | 原始来源 |
|---|---|
| [Marschner 2005](papers/optics-marschner2005-finished-wood.pdf) | [Cornell 作者 PDF](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf) |
| [Liu 2015](papers/procedural-wood-2015.pdf) | [arXiv](https://arxiv.org/abs/1511.04224) |
| [Liu 2016](papers/solid-wood-2016.pdf) | [Cornell 作者页](https://www.cs.cornell.edu/projects/wood/) |
| [Larsson 2022](papers/procedural-knots-2022.pdf) | [作者 PDF](https://www.ma-la.com/procedural_knots/Procedural_Knots_2022.pdf) |
| [Nindel 等，2025 修订版](papers/wood-inference-2025.pdf) | [arXiv 2302.01820](https://arxiv.org/abs/2302.01820) |
| [降香黄檀生长，2015](papers/odorifera-growth-2015.pdf) | [浙江农林大学学报](https://zlxb.zafu.edu.cn/article/doi/10.11833/j.issn.2095-0756.2015.04.005) |
| [He 2023，降香黄檀颜色](papers/optics-he2023-dalbergia-color.pdf) | [Molecules](https://doi.org/10.3390/molecules28227635) |
| [Chen 2024，十种黄檀光谱](papers/optics-chen2024-dalbergia-spectra.pdf) | [Frontiers in Plant Science](https://doi.org/10.3389/fpls.2024.1413215) |
| [Jurczyková 2023，热带实木可见谱](papers/optics-jurczykova2023-tropical-spectra.pdf) | [Polymers](https://doi.org/10.3390/polym15194000) |
| [Liu 2022，蜂蜡与虫白蜡](papers/optics-liu2022-beeswax-chinese-wax.pdf) | [Coatings](https://doi.org/10.3390/coatings12111689) |
| [Zhang/Song 2024，天然热蜡](papers/optics-zhang2024-hotwax-mcc.pdf) | [Forests](https://doi.org/10.3390/f15122262) |

下载未成功的附加解剖材料：[2018 木射线研究](https://hndk.hainanu.edu.cn/cn/article/pdf/preview/10.15886/j.cnki.hdxbzkb.2018.0018.pdf)在线内容可查，本次直接下载返回非 PDF；[2012 越南香枝木比较解剖论文](https://cdn.sciengine.com/doi/pdf/30350788B75A4385BDF6407A20F82C21)连接失败，未把搜索片段中容易混淆物种的纤维数值作为降香黄檀数据。CITES 解剖图下载返回 403，未伪造本地图。

### 6.2 文件与来源核验

- 下载记录含原 URL、文件大小、SHA-256：[通用清单](sources/downloads.json)、[光学论文与提图清单](sources/optics-downloads.json)。[最终文件核验](sources/verification.json)记录 11 篇 PDF、共 149 页及 12 张图片的实际尺寸；所有 PDF 可解析、报告本地链接无缺失。照片已解码并查看内容，图表已检查纵轴与图例。全文数据引用按物种与测量条件区分。
- [安全下载脚本](scripts/download_assets.py)只接收显式 HTTP(S) URL，初始与重定向 URL 均检查，不接受含地址分隔符的链接。
- 官方 shader 已阅读，β TIFF 已读取；未运行旧 RenderMan、PyOpenGL 或 Blender 材质。研究资料的核验不等于它们已在目标渲染器运行通过。

### 6.3 真正剩下的标定缺口

尚未找到公开、可直接下载的 **同一块降香黄檀家具板面在明确打磨、蜡配方、厚度和抛光条件下的可见绝对 R(λ) + 多角度 BRDF + 三维纤维方向**整套数据。这里的检索未发现，不代表证明其不存在。

若要求物理标定而非外观近似，优先对目标板面浅区、深色条带与鬼脸中心分别测可见反射谱，记录测量几何、SCI/SCE、含水率、砂纸与蜡工艺；再用多角度图像拟合 `u/β/kf`，用白色灯光反射拟合 finish。否则，本文推荐的组合能提供结构可信的研究起点，光谱与蜡后参数应始终标成代理或拟合值。
