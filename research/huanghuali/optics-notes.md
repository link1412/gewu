# 木材光学研究笔记（供 report.md 整合）

下文把 **D. odorifera 实测**、**其他硬木实测**、**作者实现参数**、**本项目建模建议**分开；没有把近似材种、粉末颜色或文献示意谱冒充黄花梨打蜡家具的实测 BRDF。检索日期：2026-11-02。

## 1. 黄花梨颜色：有数值，但测的是心材粉末

He 等（2023）对鉴定为降香黄檀的心材药材进行色度测量：40 目粉末，每批约 10 g，HunterLab UltraScan VIS、D65、SCE（排除镜面分量），每批三次；下表是符合标准的 54 批样品统计。它约束该物种心材色域，却不是家具径切/弦切面，更没有蜡层。出处：[原文 §4.4 与 Table 1](https://doi.org/10.3390/molecules28227635)；本地 [PDF](papers/optics-he2023-dalbergia-color.pdf)。

| 色度量 | 最小—最大 | 均值 ± 标准差 | 适用性 |
|---|---:|---:|---|
| L* | 38.98—52.91 | 44.59 ± 3.29 | 降香黄檀心材粉末，非板面 |
| a* | 5.93—12.84 | 9.71 ± 1.65 | 同上 |
| b* | 3.83—16.88 | 9.44 ± 2.93 | 同上 |

表内每个数值均出自 [He 2023 Table 1](https://doi.org/10.3390/molecules28227635)。**不要将均值直接当 sRGB 或 linear base color**；也不能由三个 Lab 数唯一恢复反射光谱。这组低 b* 数值不支持把所有黄花梨一概设成高饱和橙黄。

## 2. 可见反射光谱：近缘黄檀与热带硬木

### 2.1 黄檀属实测光谱（无降香黄檀）

Chen 等（2024）公开十种黄檀的平均 Vis/NIR 曲线，样品含气干、打磨横切面；含水率 11%—11.5%，光源 350 W 卤素灯，45°照明，白板标称反射率 99.9%；波段 383—2386 nm，Vis 采样 1.4 nm、NIR 6.2 nm。Table 2 包含 D. latifolia、D. oliveri、D. retusa 等，**不含 D. odorifera**。Figure 3 给出可见段曲线，但不是黄花梨打蜡面，也不是角度分辨 BRDF。出处：[原文 §2、Table 2、Figure 3](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1413215/full)；本地 [PDF](papers/optics-chen2024-dalbergia-spectra.pdf)。

谱图原图已从 PDF 无重采样提取：[Figure 3（2536 × 1095）](img/optics-dalbergia-visnir-spectra-1.jpg)。左图是可见/近红外起始段反射曲线。右图部分曲线超过 1，提示不宜将整图无审查地视为满足能量界限的绝对表面反射谱。

其数据声明仅称可由作者提供，未发现随文公开的波长—反射率 CSV；附表是分类器参数。故可作为同属曲线形状参照，不能宣称已获得黄花梨绝对光谱。出处：[数据与补充材料声明](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1413215/full#h9)。

### 2.2 可读的 360—740 nm 实木谱：注意图纵轴是 K/S

Jurczyková 等（2023）在未改性对照与热处理硬木上测得可见漫反射谱：Konica Minolta CM-5，360—740 nm，10 nm 分辨率，3 mm 测量斑，D65/2°、**SCI（包含镜面分量）**，每组四个谱的平均。Figure 5 把原始 R 转为 Kubelka–Munk 的 `q = K/S = (1−R)²/(2R)`；图中的 K/S 不是反射率。出处：[§2.3.1、Figure 5](https://doi.org/10.3390/polym15194000)；本地 [PDF](papers/optics-jurczykova2023-tropical-spectra.pdf)。

原图已从 PDF 提取并按原次序拼回六条图像带：[Figure 5（2374 × 2427）](img/optics-tropical-visible-spectra-figure5.png)；图内容未重绘。若后续数字化该图，必须使用反算 `R = 1 + q − sqrt(q² + 2q)`，并标成“读图近似”；不能把它当作新的实测 CSV。本文没有提供完整可下载逐波长原始 R 数表。本次未伪造反射率采样点。

未热处理对照的实木色度如下，可用于不同色调的代理材对照；每项为 Table 2 原值，均非降香黄檀，也非蜡面：[Table 2](https://doi.org/10.3390/polym15194000)。

| 物种/材料 | L* | a* | b* |
|---|---:|---:|---:|
| Padouk，Pterocarpus soyauxii | 39.45 ± 0.81 | 29.00 ± 0.73 | 30.57 ± 1.35 |
| Merbau，Intsia spp. | 39.29 ± 3.26 | 13.54 ± 0.91 | 23.50 ± 4.55 |
| Teak，Tectona grandis | 40.38 ± 1.17 | 14.77 ± 0.23 | 30.19 ± 0.39 |

## 3. 蜡层：必须区分涂刷蜡油与传统热蜡

**可直接引用的 GU 数表，适用性有限。** Ayata 与 Ayata（2024）用 80/100/120 目打磨白橡木，刷 1/2/3 层中性天然/合成蜡油混合物（30% 干残留）；按 ISO 2813 测顺纹/横纹光泽。它说明蜡面可能仍很哑光，不能代替抛光黄花梨的测量。出处：[方法、Table 9](https://crimsonpublishers.com/mcda/pdf/MCDA.000840.pdf)；PDF 直链下载返回防护 HTML，未将其伪装为本地论文文件，表值依据可读的出版商原文。

| 60°光泽（GU） | 未涂 | 1 层 | 2 层 | 3 层 |
|---|---:|---:|---:|---:|
| 横纹 ⊥ | 2.38 | 3.83 | 3.12 | 4.78 |
| 顺纹 ∥ | 2.63 | 3.53 | 3.64 | 5.44 |

每个 GU 数据均出自 [Table 9](https://crimsonpublishers.com/mcda/pdf/MCDA.000840.pdf)，并非百分比反射率，更不能把 5.44 GU 当作 roughness=0.0544。该刊来源仅作补充，优先用以下更贴近热蜡工艺的研究确定定性趋势。

Zhang 与 Song（2024）的黑胡桃天然热蜡是蜂蜡与虫白蜡的混合物；未填充 NW 的 Lab 从 `(45.4,5.4,8.3)` 变为 `(36.8,9.7,15.3)`，即变深、偏红黄；其 60°光泽用 ASTM D523 测量，但数值主要在 Figure 4c 箱线图中，未给原始数字表。适合作为“热蜡显色、粗糙蜡层降低光泽”的代理证据，不能由此设定唯一黄花梨参数。原图：[热蜡表面照片与光泽图（1553 × 1417，原图两带拼接）](img/optics-hotwax-appearance-gloss-figure4.png)。出处：[§2、Table 2、Figure 4](https://doi.org/10.3390/f15122262)；本地 [PDF](papers/optics-zhang2024-hotwax-mcc.pdf)。

另一个可复现涂层尺度：Liu 等（2022）在欧洲枫/胡桃上将蜂蜡或虫白蜡以 50 g/250 mL 白电油配制，五层、每层约 25 g/m²、间隔 24 h，最后毡盘抛光，得到约 **20 µm** 顶层蜡膜。它是该配方的实测工艺尺度，不是所有传统黄花梨家具的固定蜡厚。出处：[§2.1](https://doi.org/10.3390/coatings12111689)；本地 [PDF](papers/optics-liu2022-beeswax-chinese-wax.pdf)。

## 4. Marschner 2005：鬼脸不能只靠二维各向异性高光

Marschner 等在胡桃、卷曲枫、交错纹非洲 padauk 的透明清漆/亮漆面上测得：白色表面高光之外，还存在**有色的次表面纤维高光**，其锥轴沿三维木纤维方向，可倾入/倾出表面；节旁随视角发生亮暗反转。黄花梨可采用这个机制，但论文未测 D. odorifera 或蜡面。出处：[论文 §2—4、Fig.6/9](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)；本地 [PDF](papers/optics-marschner2005-finished-wood.pdf)。

论文把细胞壁近似为 IOR **1.55** 的均匀介质；三维轴 `u`、折射后的入/出射方向 `s(vi), s(vr)` 应满足：

`u · s(vr) = −u · s(vi)`。

这不是将 anisotropic GGX 的 tangent 在平面内转一转就能重现的现象。该式及 1.55 均见 [§2.2](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)。

论文的组成及定义为（沿用原文符号，不将 ρd 自动改写成现代材质的 albedo）：

`fr = fs + (1−Fi)(1−Fr) [ρd + ff]`

`ff = kf g(β,ψh) / cos²(ψd/2)`

`ψi = asin(s(vi)·u), ψr = asin(s(vr)·u), ψh = ψr+ψi, ψd=ψr−ψi`

其中 `g` 是标准差 β 的零均值归一化 Gaussian。`fs` 是表面介质高光，`ρd` 是漫射项，`kf` 是有色纤维项。论文明确该模型为物理启发的现象模型，并不精确处理全部辐射度量。出处：[§4](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)。

### 4.1 官方代码与纹理真的可以下载

[作者项目页](https://www.cs.cornell.edu/~srm/publications/SG05-wood.html) 提供 [20 MB 数据包](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz)，含 diffuse/fiber/axis/beta 四类 **16-bit linear TIFF** 与 `woodreflectance.sl`；已下载并解包到 [papers/optics-marschner2005-data/](papers/optics-marschner2005-data/)。这是可读、可迁移的作者源码，但包内未发现独立开源许可证，不应将“可下载”写作 MIT/BSD 授权。

以下为本次直接检查包内源码/纹理所得，而非黄花梨实测：

| 参数 | 官方实现/纹理值 | 意义与移植注意 |
|---|---|---|
| `eta` 默认 | 1.5 | 表面 finish IOR；不是细胞壁 1.55 |
| `beta` 默认 | 0.1745 rad ≈ 10° | 纤维锥展宽，非微表面粗糙度 |
| 枫 `cmaple` / `walnut1` 的 β 图 | 10294/65535 ≈ 0.157076 rad ≈ 9° | 恒定值；原 TIFF 全像素检查 |
| `walnut2` / `padauk` 的非零 β 图 | 11438/65535 ≈ 0.174533 rad ≈ 10° | padauk 图有 0 边界像素，不把它当有效 β |
| `roughness` 默认 | 0.2 | 代码用 `pow(N·H,1/roughness)`，故指数为 5；不可直接当 GGX α |
| fiber 图解码 | 线性纹理值 × 20 | 保存时预缩放；它不是限制在 [0,1] 的 albedo |
| axis 图解码 | `2*rgb−1` 后换基并归一化 | 注意示例 y 分量在纹理分支取负号 |

数值来源：[官方源码与 TIFF 下载包](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz)；本地 [源码](papers/optics-marschner2005-data/supplemental_0142/woodreflectance.sl)。本次像素读取是可复核的文件分析结果。

**迁移中需要核查的一个细节：**源码写的是 `β exp(−(ψh/β)²/2)/sqrt(2π)`，而论文称 `g` 为归一化 Gaussian，数学上应是 `exp(...)/(β sqrt(2π))`。两者幅度相差 β²。复刻作者资产时先保持原实现的幅度约定；采用归一化版本时必须重新拟合 `kf`，不能把两套参数混用。另：代码注释称 eta=0 表示无涂层，但实际分支 `eta != 1`，所以实现上无折射应用 eta=1；这是源码检查发现，不是生物测量。

## 5. 对鬼脸渲染的可执行建议（明确不是测得的黄花梨参数）

1. 先采用三项结构：无色 finish 高光 + 有色漫射 + 随三维纤维轴变化的有色纤维高光。鬼脸周围的 `u` 要跟节疤绕流/涡纹一起变化，导管坑可减弱纤维项；不要把全部视觉变化都烧进底色。依据是 [Marschner 2005 的测量与模型](https://www.cs.cornell.edu/~srm/publications/SG05-wood-lr.pdf)，将其迁移到黄花梨属于建模假设。
2. 第一版代理参数可从 **finish IOR=1.5，fiber β=9—10°** 开始；仅是官方代理硬木资产的起点。IOR=1.5 时法向 Fresnel `F0=((1.5−1)/(1.5+1))²=0.04`，为公式计算，不是蜡层的光谱测量。依据：[作者实现](https://s3.amazonaws.com/srmweb/publications/SG05-wood-data.tgz)。
3. 不给“黄花梨统一 roughness”；用目标照片里白色灯具反射的宽度校准 finish 粗糙度，再用移动点光/转台里的有色亮暗反转校准 `u/β/kf`。GUI 中只支持 tangent anisotropy 的标准 PBR 可作快速代理，但要标注无法复现三维纤维锥。
4. 若需要真实光谱渲染，当前缺口是同一块降香黄檀板面在规定打磨、蜡配方和抛光工艺下的可见段 R(λ) 与多角度数据。优先对有色区域与黑色条带分区测量 D65 色度、可见谱和 20/60/85° GU；没有该数据时，采用已注明代理的曲线与视觉拟合，不制造物种专用“标准光谱”。
