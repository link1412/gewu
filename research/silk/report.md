# 苏绣、双面绣、缂丝与云锦：纤维级物理渲染资料及真实照片

核查日期：2026-10-29。没有联系作者、博物馆或图片权利人。

## 推荐方向与可检查标准

**推荐从“具体样品的纤维几何 + 分开标定的散射/吸收 + 正反面及透射验证”入手。** 极近景参考 Aliaga 的真实截面散射及 Zhao 的束内几何；有捻纱和铺平绣线须分别建模。Khungurn 的丝缎拟合是可复现实例，Montazeri 是中景聚合参考。这是本报告针对任务的方案判断，不是四篇论文已经验证了苏绣。

本次交付标准：五类问题逐项覆盖；每项数字附来源和性质；图像逐张列页面、像素/器物尺度、授权；未能核实的项目明确写“没找到”或“不确定”；下载清单只放从真实页面取得的图像地址。**本次没有获得一套可直接作为苏绣默认材质的完整实测参数。**

证据标记：**实测**＝作者测量实物；**拟合**＝由测量/照片反演或统计拟合；**文献汇编/机构记录**＝原来源收集或工艺记载；**人工设置**＝论文渲染输入；**推算**＝本报告计算、列公式；**不确定**＝原文条件、转录或单位尚未核清。不同样品的数据不合并成统一“标准范围”。

术语须分开：**brin** 是单根丝素纤维；生茧丝通常由成对 brin 与丝胶构成；工艺中的“一根丝线”“一丝”“一绒”是用线口径，不能自动等同 brin。下列“宽度”“重建圆柱半径”“等效直径”也不互换。

| 需求 | 已获得的可靠约束 | 仍未找到/未核验 |
|---|---|---|
| 纤维光学 | 家蚕真实截面/脱胶形态、天然丝折射率汇编、丝素膜 n/k 拟合与机器文件 | 天然家蚕单纤维完整 n/k 张量光谱；同样品脱胶前后成对光学测量 |
| 四篇外观论文 | Aliaga 物性表、Khungurn 丝缎拟合、Zhao 两组丝纱表；代码可取得程度 | Montazeri 逐丝样参数表；多个项目的开放源码/许可 |
| 工艺 | 针法相对叠接、劈丝份数、部分底料组织；具体缂丝经纬密度 | 通用毫米针长/针距、劈后实测线径、双面绣底料密度与透光谱 |
| 植物染谱 | 丝上红花/苏木/靛蓝/栀子反射曲线位置；茜草的相关丝绸研究；羊毛原始谱数据包 | 五种植物染丝绸的公开逐波长机器数据与单纤维吸收谱 |
| 真照片 | 苏绣与双面绣局部、缂丝、云锦细节、真实丝纤维显微图 | 带校准标尺且开放授权的苏绣/双面绣/云锦显微原图；多数馆方原图像素 |

## 1. 蚕丝纤维的光学与脱胶

### 1.1 使用边界

可直接约束纤维几何的是天然丝 SEM/TEM；可直接编程读取的完整可见光 n/k 数据主要来自**丝素薄膜**。天然丝腺提取液成膜也属于薄膜，不能把论文的 “native fibroin” 写成天然茧丝的直接光学测量。天然家蚕纤维沿轴/横轴完整可见光 n(λ)、k(λ) 张量，以及同一样品脱胶前后成对测量表：**没找到可公开核验的完整数值数据**。

### 1.2 几何尺寸和脱胶

| 对象/量 | 数值 | 性质、条件与定位 | 原始来源 |
|---|---:|---|---|
| 天然家蚕丝单根丝素 brin 的截面 | 近三角形，不能视为恒定圆截面 | TEM 实测；不是理想等边三角形的定量证明 | Shen, Johnson & Martin 1998，摘要；[出版页](https://pubs.acs.org/doi/10.1021/ma980281j)，DOI 10.1021/ma980281j，Macromolecules 31:8857–8864 |
| 丝胶覆盖层厚度 | 0.5–2 μm | TEM 实测；脱胶前 | 同上 |
| 脱胶后沿轴可见带状结构间距 | 约 600 nm | TEM 实测；存在于其制样条件，不能等同外表面起伏振幅 | 同上 |
| 原茧双 brin 的宽度 | 22–40 μm；作者报告分布参数 x_c=28.86 μm | SEM 图上测量、对数正态拟合；非单 brin 直径 | Yaiphabi et al., online 2025/issue 2026，SEM study、Fig.8a；[全文](https://link.springer.com/article/10.1007/s10973-025-15115-6) |
| 脱胶后单 brin 的宽度 | 7–18 μm；作者报告 x_c=12.37 μm | 同批流程 SEM 测量/拟合，图上共 70 个计数；非等效圆直径 | 同上 Fig.8c |
| 原茧丝胶层 | 约 850 nm | SEM 截面实测，作者写 rough thickness | 同上 Fig.7、SEM study |

Yaiphabi 样品由印度 Imphal 的 RSRS 提供；先 EDTA 去矿，再以 0.02 M Na₂CO₃ 在 100 °C 脱胶 1 h，SEM 前镀金，20 kV。其 Fig.7d 是脱胶单 brin 截面。**不能**用原茧双丝宽减去脱胶单丝宽来求丝胶厚度，也不能将 28.86 μm 除以二当作单 brin 的直径。原文将对数正态参数 x_c 称为 expected mean，此处保留作者命名，不重新解释为算术均值。

Shen 1998 的同一研究观察到：原茧是成对且扭转的丝素单丝，去掉丝胶后分离为单丝并显露与内部定向纤原结构一致的纹理。这是脱胶前后几何建模的直接依据；粗糙度 RMS、相关长度及其双向 PSD：**没找到**。

### 1.3 折射率、双折射与吸收

#### 1.3.1 天然纤维与标准识别参考值

| 数据 | 数值/条件 | 证据等级与限制 | 来源 |
|---|---|---|---|
| cultivated silk 纵向/横向折射率 | n∥=1.591，n⊥=1.538；Δn=0.053，正双折射 | **官方方法引用的识别参考值**；表注 compiled from *The Particle Atlas*，不是该机关实测；波长、温湿度、脱胶程度、批次**没找到** | South Coast AQMD Method 317-93，表格 “Silk (cultivated)”，PDF 印刷 p.5；[官方 PDF](https://www.scaqmd.gov/docs/default-source/laboratory-procedures/methods-procedures/317-93.pdf?sfvrsn=d7bd1761_2)（检索缓存可读表，直接打开时服务器报错） |
| 另一汇编对同组值的交叉确认 | 1.591 / 1.538 / 0.053 | **文献汇编**，不是新实测；不能作为独立重复实验 | Xiangwu Zhang, *Fundamentals of Fiber Science*, Table 20.1, p.401；[出版社样章](https://www.destechpub.com/wp-content/uploads/2016/10/Fundamentals-of-Fiber-Sci-1-19-409-430.pdf?x60473=) |
| 蚕丝纤维双折射数量级 | Δn≈4×10⁻³，d=48 μm；液晶延迟片在 635 nm、22.8 °C 校准，成像用白光 | **实测延迟后估计**；作者明确只是数量级。该段/图注未逐图清楚指认物种，研究同时有家蚕和柞蚕，故**不作为家蚕精确常数**；与上面 0.053 不混合平均 | Ryu et al. 2019, p.925, Fig.3 / Results and Discussion；[全文](https://www.beilstein-journals.org/bjnano/articles/10/93)，[PDF](https://www.beilstein-journals.org/bjnano/content/pdf/2190-4286-10-93.pdf)，DOI 10.3762/bjnano.10.93 |
| 柞蚕 A. pernyi（不是家蚕） | Δn=1.63×10⁻²，约 2% 不确定度，425–625 nm 平均 | 实测，供区分物种，**不移植**为苏绣家蚕丝参数 | Honda et al. 2018, *Simple multi-wavelength imaging of birefringence: case study of silk*；[原论文](https://doi.org/10.1038/s41598-018-36114-8)，[作者预印本](https://arxiv.org/abs/1809.09723) |

#### 1.3.2 有可程序读取 n/k 的薄膜数据（不是天然纤维张量）

Perotto et al. 2017，*The optical properties of regenerated silk fibroin films obtained from different sources*, APL 111:103702，[出版 PDF](https://pubs.aip.org/aip/apl/article-pdf/doi/10.1063/1.4998950/14502984/103702_1_online.pdf)，[DOI](https://doi.org/10.1063/1.4998950)。以下为椭偏测量后的 **Cauchy/Urbach 拟合**，300–1700 nm，pp.103702-2–3、Table I/Fig.2。

| 家蚕丝素薄膜状态 | n @500 nm | k @500 nm | Cauchy A | B | C |
|---|---:|---:|---:|---:|---:|
| 未结晶再生薄膜 | 1.554 | 约 1×10⁻⁴ | 1.5231±0.0004 | 0.0079±0.0001 | (6±1)×10⁻⁶ |
| 甲醇退火结晶薄膜 | 1.559±0.001 | 约 3×10⁻⁴ | 1.5303±0.0003 | 0.0066±0.0001 | (110±10)×10⁻⁶ |
| 从丝腺提取后制成薄膜（论文 native） | 1.566±0.001 | 原文仅明确比再生薄膜大；机器转录见下 | 1.551±0.001 | 0.0026±0.0003 | (240±30)×10⁻⁶ |

“native” 样品是丝腺取出后溶入水再旋涂的薄膜；结晶组甲醇处理 30 min；**不是脱胶前/后天然纤维对比**。不能把 k（无量纲消光系数）直接填写成 μm⁻¹ 吸收系数。

可下载的机器数据（**数据库转录/加工，不标成原始实测逐点 CSV**）：[官方数据库目录](https://github.com/polyanskiy/refractiveindex.info-database/tree/main/database/data/other/silk/Bombyx%20mori/nk)。三个 YAML 文件均将数据标为 CC0，给出 Cauchy 公式和 tabulated k：

- [Perotto-uncrystallized.yml 原始文本](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/silk/Bombyx%20mori/nk/Perotto-uncrystallized.yml)
- [Perotto-crystallized.yml 原始文本](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/silk/Bombyx%20mori/nk/Perotto-crystallized.yml)
- [Perotto.yml 原始文本（丝腺薄膜）](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/silk/Bombyx%20mori/nk/Perotto.yml)

数据库 formula 5 对应 n(λ)=A+Bλ⁻²+Cλ⁻⁴，λ 单位 μm；0.3–1.7 μm 是数据库有效范围。**转录异常**：`Perotto-crystallized.yml` 的 COMMENTS 写成 Uncrystallized，但系数 1.5303 / 0.0066 / 1.1×10⁻⁴ 与论文结晶组相符，文件名也指结晶组。应按原论文核对后使用。其丝腺薄膜 YAML 的 k(0.500 μm)=3.762740×10⁻⁴，属数据库值，不是本文逐字报告的精确数字。

换算示例（**推算**）：以论文再生薄膜的近似 k=10⁻⁴、λ=500 nm，用 α=4πk/λ，得到 α≈25.1 cm⁻¹ = 0.00251 μm⁻¹。这只是对应**薄膜材料的本征吸收**；不能据此宣称苏绣纤维 k 已经测定。天然丝中几何散射、界面反射与本征吸收应分开。

#### 1.3.3 脱胶前后光学：已确认与没找到

- 天然丝胶去除导致双 brin 分离、外形/可见纹理改变，有上述 SEM/TEM 证据。
- 同批天然家蚕丝在相同湿度、波长、偏振下的脱胶前后 n∥/n⊥/k 差值：**没找到**。
- 丝胶膜与丝素膜可作为成分研究，不能直接给未脱胶茧丝套同样的各向同性常数。Bucciarelli et al. 2018 的题目为 *A comparative study of the refractive index of silk protein thin films towards biomaterial based optical devices*，属于**蛋白薄膜**；本次未核验其原文完整数值，故不补填。
- 完整可见光天然纤维消光谱：**没找到开放且已核验的数值表**。有直接天然丝反演的后续论文 Tao & Qiu, JQSRT 333 (2025) 109314，[DOI](https://doi.org/10.1016/j.jqsrt.2024.109314)，[出版页](https://www.sciencedirect.com/science/article/pii/S0022407324004217)。其 FDTD–PSO 通过单纤维散射反演 n/k；本次仅公开摘要/引言可读，全文具体波段和数值表**没找到**，不猜。
- 可见光下“透明薄膜透过率高”不等于“天然丝纤维无散射”；Choi et al. 2018 实际在天然丝观察纳米内部结构，[论文](https://www.nature.com/articles/s41467-017-02500-5)，Fig.1 给出真实 SEM/TEM，可用于几何细节参考。

## 2. 有丝样参数的纤维、纱线和织物外观模型

先看代码可用性：Aliaga 为非商业用途可索取；Zhao 有官方 Code and Data ZIP；Khungurn 与 Montazeri 未找到独立作者开源发布。**可下载文件不等于已核验开放源码许可证，也不等于已编译运行。** 各项来源和参数如下。

### 2.1 Aliaga et al. 2017

**An Appearance Model for Textile Fibers**，Computer Graphics Forum 36(4), 35–45，DOI [10.1111/cgf.13222](https://doi.org/10.1111/cgf.13222)。[作者项目页](https://graphics.unizar.es/projects/clothEGSR17/)，[作者版 PDF](https://graphics.unizar.es/projects/clothEGSR17/downloads/aliaga_egsr17.pdf)，[作者本人镜像](https://www.aliagabadal.com/data/papers/Aliaga_cloth_EGSR2017.pdf)。

Table 1（印刷 p.38，PDF p.4）的 silk 一行如下。**这些是论文汇总已有纺织文献的物性，不是 Aliaga 团队新测的同一根丝，也不是专门苏绣绣线的测量。** 表注把直径追溯到 Trotman 1984，把密度/折射率追溯到 Hearle & Morton 2008，把粗糙度追溯到 GK81/LXD08。

| 参数 | silk 数值 | 单位 | 证据类型及限制 |
|---|---:|---|---|
| 直径 | 5–10 | µm | Table 1 文献汇编；不是截面的三边尺寸 |
| 密度 ρ | 1.34 | g/cm³ | Table 1 文献汇编；表注明 65% RH、20°C 标准气氛 |
| 轴向折射率 η∥ | 1.591 | 无量纲 | Table 1 文献汇编；该表没有给测量波长 |
| 横向折射率 η⊥ | 1.538 | 无量纲 | 同上 |
| Δη=η∥−η⊥ | 0.053 | 无量纲 | **本报告算术推算**，不是论文另一次测量 |
| 表面粗糙度 Ra | 8–9 | nm | 原表文本转录；一致性问题见下 |
| 表列 profile length l | 30 | nm | 原表括号值转录；一致性问题见下 |
| 表列 Beckmann 粗糙度角 β | 6–7 | ° | 原表文本转录；一致性问题见下 |

**粗糙度疑点不能隐去。** 正文 §3.1 / p.39 写 `β=arctan(Ra/l)`，但把上述 silk 表值代入得到 **14.93–16.70°（本报告推算）**，与表列 6–7° 不符。本轮三个作者/学会镜像的索引文本都给相同表值；大 PDF 被网页工具的文件大小限制挡住，未能逐像素检查原表排版，作者 slides 也抓取超时。因此当前不能确定是原文错误还是抽取问题，**不要把这组 Ra/l/β 同时当作已自洽的渲染输入；未找到勘误。**

模型用真实截面显式几何追踪再预计算 BCSDF。正文 §4 说明采用各向同性介质及平均折射率，忽略偏振、双折射传播、衍射和荧光；Table 1 虽列两个折射率，**渲染器没有因此完整模拟双折射**。[上述 PDF，§3–4](https://graphics.unizar.es/projects/clothEGSR17/downloads/aliaga_egsr17.pdf)

吸收由染料浓度构造：`μa=κ ε`，`κ=ρζ`；ρ 是纤维密度，ζ 为染料质量/纤维质量的 Depth of Shade，ε 为单位染料质量的消光系数。Figure 5 / p.39 的 **5.08、40.46、84.68 mm⁻¹** 是同一橙色染料不同染深的**模型示例输入**，不是未染蚕丝的本征吸收谱，也不是植物染料谱。未找到该文提供可直接下载的未染丝全可见光 `μa(λ)` 数组。[PDF，§3.1、Fig.5](https://graphics.unizar.es/projects/clothEGSR17/downloads/aliaga_egsr17.pdf)

图 1 的丝缎设置为 **1 ply、1 twist/cm、30 fibers/yarn**，是论文展示的布样/模型设定，不是苏绣工艺标准；图 5 显微照片示例为 **3 plies、每 ply 90 fibers**，不可混同。[PDF，Fig.1、Fig.5](https://graphics.unizar.es/projects/clothEGSR17/downloads/aliaga_egsr17.pdf)

实现：作者项目页明确代码及 Fibers BCSDF 属 Universidad de Zaragoza，因数据量大，**可索取、非商业用途免费**。这不是已确认的 OSI 开源许可。公开 GitHub 仓库/许可证：**没找到**；本文没有向作者发消息。[官方 Downloads](https://graphics.unizar.es/projects/clothEGSR17/)

### 2.2 Khungurn et al. 2015

**Matching Real Fabrics with Micro-Appearance Models**，DOI [10.1145/2818648](https://doi.org/10.1145/2818648)。作者/项目站写 2015 年 12 月、TOG 35(1)；后续论文也有标为 2016 的引用，查找应以标题及 DOI 识别，不能误认为两篇论文。[Cornell 官方项目汇总](https://research.cs.cornell.edu/ctcloth/index.htm)，[作者版 PDF](https://projects.shuangz.com/ctcloth-tog15/ctcloth-tog15.pdf)，[Cornell PDF](https://www.cs.cornell.edu/projects/ctcloth/download/matching-cloth/togpaper_20150904.pdf)。

Table III / PDF p.13：`Silk` 是**红色 silk satin**；CT voxel 边长 **1.40 µm（采集分辨率）**、数据尺寸 **780×530×160 voxels（采集/处理后的体积规模）**、纤维圆柱半径 **4.72 µm（几何重建拟合）**。§6.5 / p.11 是按圆柱所覆盖体积与 CT 非空体素的一致性选半径，因此不能写成“显微镜直接测得直径 9.44 µm”；**9.44 µm 只能称为从圆柱半径乘二得到的重建直径（推算）**。[PDF，§6.5、Table III](https://www.cs.cornell.edu/projects/ctcloth/download/matching-cloth/togpaper_20150904.pdf)

Table IV / PDF p.18 给出完整 silk 参数。下表每个数都是**对多角度照片作外观匹配后的拟合值**；RGB 无量纲，βR/βTT 是反射/透射纵向瓣宽，γTT 是透射方位瓣宽，角宽表数采用度。`CR` 和 `CTT` 是模型反射/透射颜色系数，**不是反射光谱、透射光谱、Fresnel 常数或吸收系数**。

| 模型 | CR (RGB) | CTT (RGB) | βR (°) | βTT (°) | γTT (°) | α (RGB) |
|---|---|---|---:|---:|---:|---|
| Fiber scattering / fibers | (0.745,0.008,0.070) | (0.620,0.553,0.562) | 1.000 | 10.000 | 19.823 | 不适用 |
| Fiber scattering / volume | (0.992,0.001,0.034) | (0.002,0.690,0.570) | 1.000 | 10.000 | 13.900 | (0.940,0.746,0.773) |

体积 microflake 基线另外拟合为 `α=(0.936,0.051,0.214)`、`γ=0.013`（原表值；γ 在该微片分布的约定下使用，不应当作上表的 γTT 度数）。α 为单次散射反照率，亦无量纲。[PDF，§4、Table IV](https://www.cs.cornell.edu/projects/ctcloth/download/matching-cloth/togpaper_20150904.pdf)

局限：光学拟合针对反射照片，样品下面有黑色金属板，虚拟场景也放黑网格；不能据此宣称已验证自由悬挂双面绣的透射。作者 §7.3 也指出 silk 掠射高光出现非物理青色，源于允许 R 瓣带颜色。论文独立开源仓库/许可证：**没找到**；官方页面提供 PDF、补充 PDF 和视频，不列源代码。[PDF，§7.1、§7.3](https://www.cs.cornell.edu/projects/ctcloth/download/matching-cloth/togpaper_20150904.pdf)，[官方项目页](https://research.cs.cornell.edu/ctcloth/index.htm)

### 2.3 Zhao, Luan & Bala 2016

**Fitting Procedural Yarn Models for Realistic Cloth Rendering**，TOG 35(4), Article 51，DOI [10.1145/2897824.2925932](https://doi.org/10.1145/2897824.2925932)。[官方项目页](https://research.cs.cornell.edu/ctcloth/index.htm)，[作者版 PDF](https://www.cs.cornell.edu/~kb/publications/SIG16ProceduralYarn.pdf)。

Figure 15 / PDF p.9 的 `Silk 1`、`Silk 2` **都是 3-ply 实物纱线**。Table 2 / PDF p.11 是从 micro-CT 测量重建几何后得到的**统计拟合参数**，不是普适蚕丝常数。§6 报告扫描分辨率 **2.5 µm（采集值）**。下表逐项转录 silk 数据；成对值为正态分布的 **(均值,标准差)**。

| Table 2 参数 | Silk 1 | Silk 2 | 含义/单位 |
|---|---:|---:|---|
| β | 0.462 | 0.554 | 横截面纤维概率分布形状参数，无量纲 |
| ε | 0.000 | 0.405 | 同一分布的背景项，无量纲 |
| α | −0.458 | −0.556 | 纤维螺旋节距；长度单位未核实，负号为顺时针 |
| Rmin | 0.95 | 0.70 | 迁移径向比例，无量纲 |
| s | 1.8 | 1.2 | 纤维迁移频率参数，无量纲 |
| ex | 0.025 | 0.031 | ply 截面 X 缩放；原表坐标尺度 |
| ey | 0.022 | 0.025 | ply 截面 Y 缩放；原表坐标尺度 |
| Rply | 0.038 | 0.045 | ply 中心螺旋半径；长度单位未核实 |
| αply | 0.526 | 0.702 | ply 螺旋节距；长度单位未核实，正号为逆时针 |
| m | 33 | 47 | 每 ply 纤维数，根；不是整根纱线纤维数 |
| ρloop | 20.32 | 18.89 | loop 型毛羽线密度；每原表长度单位 |
| ρhair | 23.82 | 23.09 | hair 型毛羽线密度；每原表长度单位 |
| Rloop_max | (0.024,0.004) | (0.029,0.004) | loop 最大半径；原表坐标尺度 |
| Rhair_min | (0.021,0.004) | (0.024,0.005) | hair 起始半径；原表坐标尺度 |
| Rhair_span | (0.014,0.011) | (0.010,0.008) | hair 径向跨度；原表坐标尺度 |
| zhair_span | (0.010,0.050) | (0.008,0.038) | hair 纵向跨度；原表坐标尺度 |
| θhair_span | (0.407,0.390) | (0.417,0.446) | hair 方位跨度；弧度，按 Eq.(11) 的三角函数约定 |

Table 2 设 `Rmax=1`（归一化约定）。**没有核实到该表坐标长度对应 mm、cm 还是其它场景单位的明确声明，因此上述含长度参数不能直接标成 mm。** ex/ey 是把单位圆盘缩放成椭圆的量，不能误当真实单根蚕丝直径。[PDF，Eq.(1)–(4)、§5、Table 2](https://www.cs.cornell.edu/~kb/publications/SIG16ProceduralYarn.pdf)

Table 3 / PDF p.11 使用 Khungurn 的散射模型，但表注明确说参数是**人工调整（manually adjusted）**，并非这篇论文自动反演出的光学测量：

| 样本 | CR (RGB，无量纲) | CTT (RGB，无量纲) | βR (°) | βTT (°) | γTT (°) |
|---|---|---|---:|---:|---:|
| Silk 1 | (0.10,0.10,0.10) | (0.73,0.50,0.67) | 1.0 | 10.0 | 20.0 |
| Silk 2 | (0.10,0.10,0.10) | (0.05,0.55,0.70) | 1.0 | 10.0 | 20.0 |

[PDF，Table 3 及表注](https://www.cs.cornell.edu/~kb/publications/SIG16ProceduralYarn.pdf)

实现：官方确实列出 **Code and Data** 下载，直链为 [code_data_v2.zip](https://www.cs.cornell.edu/~kb/projects/ctcloth/code_data_v2.zip)。本轮网页工具能验证这是官网链接，但不能解压 ZIP；本地网络请求受限。因此**包内许可证、构建可用性、是否包含渲染器全部修改：没找到/未验证**，不能把“公开 ZIP”自动表述为 MIT/BSD 开源。论文说使用改过的 Mitsuba；没有找到与这份官方包明确对应的作者 GitHub 仓库。[官方 Downloads](https://research.cs.cornell.edu/ctcloth/index.htm)

### 2.4 Montazeri et al. 2020

**A Practical Ply-Based Appearance Model of Woven Fabrics**，TOG 39(6), Article 251，DOI [10.1145/3414685.3417777](https://doi.org/10.1145/3414685.3417777)。[作者项目页](https://projects.shuangz.com/practical_cloth-sa20/)，[低分辨率全文 PDF](https://projects.shuangz.com/practical_cloth-sa20/practical_cloth-sa20-ld.pdf)。

这是 **woven fabric / 机织物** 模型，不能与 2021 年 knitted fabrics 续作混称。以 ply 曲线/表面承载纤维法线、切线与阴影细节，显式保留飞出纤维。§3 区分 round yarn 与平展、纤维较齐的 flat yarn，后者包括丝缎；§4 分别处理镜面反射、透射以及 body 散射。§6.1 / p.251:8 与 X-Rite TAC7 的真丝样品测量比较，§6.2 用显微观察构造纱线几何，再以 SLSQP 拟合照片。[PDF，§3–6](https://projects.shuangz.com/practical_cloth-sa20/practical_cloth-sa20-ld.pdf)

**具体丝样的 η、σt、roughness、颜色、每 ply 纤维数及逐样本拟合参数表：没找到。** 通读该公开全文，Table 1 是符号表，Table 2 是性能表；不能从渲染图颜色反推一套参数并说是论文原值。其 fiber-detail 几何引用 Zhao 2016 对应材料的程序化模型。§7 / p.251:10 承认仍把单根纤维截面简化为圆形。[同 PDF，Table 1、Table 2、§6.2、§7](https://projects.shuangz.com/practical_cloth-sa20/practical_cloth-sa20-ld.pdf)

实现：文中说已集成工业渲染系统，但官方项目 Downloads 仅列两种分辨率 PDF 和视频；**作者开源代码、仓库、许可、完整材质数据包：没找到**。[官方项目页](https://projects.shuangz.com/practical_cloth-sa20/)

## 3. 苏绣工艺、双面绣底料与缂丝密度

“针距”可能指同一针两端距离，也可能指平行线间距；来源未定义时不互换。以下将实物测量、机构说明与艺人口述分列。工艺份数不直接换成单纤维直径。

### 3.1 针法：能查到相对几何，没找到可靠的通用毫米参数

| 针法与项目 | 核实数值/结论 | 数值性质与适用范围 | 出处 |
|---|---|---|---|
| 套针中的平套：层间交叠 | 第二皮采用隔一针的稀针嵌入第一皮，覆盖前皮长度的 **8/10**；第三皮与第二皮等长，并与第一皮尾端相接 | 故宫的针法说明；比例规则，不是某件藏品实测，不是毫米针长 | 故宫博物院「红纳纱百蝶金双喜单氅衣」页面“套针”术语释义：[原页面](https://www.dpm.org.cn/collection/embroider/231344.html) |
| 散套：首皮内缘长短参差 | 约为针线自身长度的 **2/10**；第二皮隔一针，覆盖首皮约 **8/10** | 苏州市刺绣研究所的实际技法教材；相对长度，不能据此推出绝对毫米值 | 苏州市刺绣研究所《苏州刺绣》，上海人民出版社，1976，印刷页10—11“二、针法介绍”：[书籍扫描件](https://www.bannedthought.net/China/MaoEra/Arts/Misc/SuzhouEmbroidery-1976.pdf)。扫描件44.9 MB，网页工具不能全文打开，核查到该扫描件的搜索索引原页文本（含印刷页码）；尚未逐页视觉核对 |
| 施针：第一层排线间隔 | 教材称通常“间隔两针”，色彩复杂需要多层时可更稀；每层稀针逐步施密 | 同上教材，工艺规则；“两针”的物理宽度 **没找到**，不能换算为2 mm | 同上书，印刷页10—11 |
| 乱针 | 长短参差的直斜、横斜线交叉；分层加色、由稀到密 | 同上教材；并不规定统一针长 | 同上书，印刷页11。**绝对针距、针脚长度（mm）没找到** |
| 滚针 | 两线紧接连成条纹，通常针脚等长，转弯处缩短 | 故宫针法术语说明；无绝对数字 | 故宫博物院「刺绣庆寿通景屏」页面“滚针”词条：[原页面](https://www.dpm.org.cn/collection/embroider/229941.html)。**绝对针距、针脚长度（mm）没找到** |
| 套针、施针、滚针、乱针的绝对物理尺度 | **没找到**可作为苏绣通用规则、有实物测量方法或可信出处的毫米级针长/线距表 | 不把商品描述、机绣软件参数、体验教学的一次性间距写成传统苏绣定值 | 上述机构记录与技法教材均不足以支持统一毫米值 |

GB/T 38029-2019《苏绣》确实存在，国家标准全文公开系统在核查时列为现行，2019-08-30发布、2020-03-01实施：[国家标准官方题录](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=EADE307A2B81C3ECF89679A3FD5D25E8)。本次官方题录不能直接预览正文；不据第三方转录断言其规定了毫米针距，也不把网络“每针1—2 mm”当国标。

### 3.2 劈丝：比例可找到，微米尺度不能由比例直接产生

| 项目 | 有出处的数字 | 性质与限制 | 出处 |
|---|---|---|---|
| 无锡精微绣精细局部 | 一根丝线劈到 **1/80** | 中国非遗项目介绍中的工艺记录；属于苏绣的无锡精微绣扩展项目，不能推广到所有苏绣；没给原线直径、每份直径或单纤维数量 | 中国非物质文化遗产网「苏绣（无锡精微绣）」项目317、Ⅶ-18，保护单位为无锡市民间艺术博物馆：[原页面](https://www.ihchina.cn/project_details/13979.html) |
| 苏州刺绣研究所被参访时的用线 | **1/16、1/32**；鱼尾局部 **1/64** | 苏州市市场监督管理局组织活动的直接参访记录，非仪器测量；尤其1/64为表现鱼尾的局部用法 | 苏州市市场监督管理局，2023-03-09「领略非遗之美 ‘绣’出美好生活」：[原页面](https://scjgj.suzhou.gov.cn/szqts/zhxx/202303/818ce7969a844269a5b30cc98c072cb5.shtml) |
| 当代苏绣金鱼演示 | 一根丝线可劈成 **128股** | 2025年大阪世博会苏绣艺术家俞君瑶现场解释，由苏州市人民政府网站报道；艺人口述，非测量 | 苏州市人民政府「大阪世博会中国馆掀起‘苏州热’」：[原页面](https://www.suzhou.gov.cn/szsrmzf/szyw/202505/b6e0e19732224560b1406575d8d82458.shtml) |
| 各份线的微米直径、横截面积、denier/tex | **没找到**符合上述具体原线、分劈口径且附测量方法的数据 | 1/16等是分劈比例，不能把直径除16。若原线为多纤维束，份数首先对应束内纤维/物质量分配；横截面与扁平铺展另需测量 | 本轮查证结论 |

### 3.3 双面绣底料：组织要按实物确认，透光率没找到

| 项目 | 核查结果 | 性质/限制 | 出处 |
|---|---|---|---|
| 绡的组织 | 中国丝绸博物馆解释，“绡”后来多指轻薄的**平纹类生织物** | 织物术语、历史语义说明；不是指定双面绣样品的检测。不能因此认为所有现代售卖的“绡”都具有同一结构、含胶量或密度 | 中国丝绸博物馆，2023-02-14「一问Vol.6｜什么是绫罗绸缎？（下篇）」：[原页面](https://www.chinasilkmuseum.com/gskt/info_319.aspx?itemid=30975) |
| 纱的实例：直径纱 | **两经纠绞交织**、纬比经粗、呈方孔，属纱罗组织 | 故宫对清代直径纱的术语说明；这件纳纱氅衣不是用于证明所有双面绣底布相同 | 故宫「红纳纱百蝶金双喜单氅衣」“直径纱”词条：[原页面](https://www.dpm.org.cn/collection/embroider/231344.html) |
| 确实标为双面绣的历史纱地实例 | 「明黄色纱双面绣万字地云龙单袍」页面解释“实地纱”：无纹地为平纹、较密；显花部两根经线纠绞、较疏，产生纱孔 | 具体藏品页可确认双面绣与纱地并存；其通用“实地纱”释义含两种组织，不给每cm根数 | 故宫博物院：[原页面](https://www.dpm.org.cn/collection/embroider/230297.html)。本次检到官方页面的完整搜索索引段落，直接打开有超时 |
| 专用“玻璃丝纱” | 《雪宦绣谱》现代编注本称其为双面绣常用的透明薄纱 | 这里只能作名称线索。材料成分、实际组织、经纬密度未核实；**不能从“玻璃”推成玻璃纤维，也不能推成真丝** | [江苏商贸职业学院图书馆提供的PDF](https://tsjyb.jsbc.edu.cn/_upload/article/files/75/69/7346c62b453cbd4126bdc45fd5a0/ba299643-a090-4fb3-84eb-9fbfbaa7ac88.pdf)，印刷页9；PDF过大未能全文打开，仅索引文本核查 |
| 双面绣纱/绡底料经纬密度、纱径、厚度、孔隙率 | **没找到**可靠、对应具体双面绣样品的成套数字 | 不用马王堆素纱、修复用绉丝纱或商业欧根纱的数字替代目标底料 | 本轮查证结论 |
| 双面绣纱/绡底料的分光透过率、可见光总透光率、雾度 | **没找到**可追溯的实测数字 | “轻薄透明”“看不出底料”不等于具有某一百分比透光率；不使用无出处的38%、72%等网络数字 | 本轮查证结论 |

### 3.4 缂丝：有可直接使用的实物技术数据

| 对象/参数 | 数字与单位 | 性质 | 出处 |
|---|---|---|---|
| 故198922《应真飞锡图缂丝挂屏》经密 | **22根/cm**，多点测试后平均 | **论文实测**。手工打纬不均，所以作者有意多点取平均；不是宋、明、清通用值 | 陈杨《缂丝文物展前保护处理之探索》，《故宫学刊》2014，印刷页318，PDF第4页（从1计）；[故宫原PDF](https://www.dpm.org.cn/Uploads/File/2020/02/19/u5e4d030ec8c19.pdf) |
| 同件纬密 | **46根/cm**，多点平均 | **论文实测** | 同上 |
| 同件经线组合 | **2×2（4丝）**，本色生丝，弱捻合股 | **论文对实物工艺鉴别**；“丝”沿用论文原表述，没有单纤维μm直径，不能自行认定为4根brin | 同上 |
| 同件纬线组合 | **8×2（16丝）**，染色熟丝 | **论文对实物工艺鉴别**；熟丝为煮炼染色材料；论文一般工艺部分说明纬丝通常不加捻 | 同上 |
| 《应真渡海图》《应真飞锡图》屏尺寸 | 各 **纵93.5 cm、横113 cm** | 论文记载的器物尺寸，含屏的具体边界需看原图，不能默认作微观纹理裁片尺寸 | 同上 |
| 同件经线中心间距 | **0.455 mm**（10/22） | **本报告推算**，由经密倒数所得平均周期；不是经线直径 | 同上实测经密为输入 |
| 同件纬线平均节距 | **0.217 mm**（10/46） | **本报告推算**，不是纬线直径；局部波纹与压缩不由平均值决定 | 同上实测纬密为输入 |
| 同件御制诗的局部搭缂 | 每 **6—8梭** 搭缂 **1梭** | 论文显微观察得到的局部工艺记录；有些字未这样处理，非全幅统一规则 | 同上，印刷页321（PDF第7页） |

另一个差异明显的实物例子：北京艺术博物馆「金地缂丝灯笼仕女袍料」，明代，经密 **16根/cm**、纬密 **52根/cm**，捻金线直径 **0.2 mm**，色纬捻度较强、双股并用。数值为该馆对馆藏的技术说明，未说明具体仪器方法，应标为**博物馆实物记录，非本报告测量**。[北京艺术博物馆原页面](https://www.bjartmuseum.com/read/1410.htm)（本次直接打开502；数值由官方页搜索索引核查）。不将两件实物合并成“缂丝标准范围”。

### 3.5 补充对照：大都会《龙纹缂丝扇》

大都会出版的 *When Silk Was Gold: Central Asian and Chinese Textiles*（Watt & Wardwell，1997），cat.27“Fan with Dragon”，藏品 **47.18.42**，Technical Analysis 给出：经为未合股的棕褐色丝，**34根/cm**；彩色丝纬带 s 捻，约 **90–120根/cm**；裂缂接合，偏心织与飞梭用于细部；龙息处纬线跨 **2根经**，通常处跨 **1根经**。这些是**馆藏技术分析记录**，不是全体缂丝标准。[大都会分章原文件（含技术分析）](https://libmma.contentdm.oclc.org/digital/api/collection/p15324coll10/id/62264/download)

须保留目录更新差异：该旧书题作元代、尺寸 **经向26 cm、纬向25.8 cm**；[当前馆藏页](https://www.metmuseum.org/art/collection/search/39642)改为“probably 17th century”、清代，整体 **26×25.7 cm**。本报告以藏品号关联技术数据，**不把旧断代当当前结论，也不抹平尺寸差异**。对应真照片见 K02。

## 4. 植物染料的反射/透射光谱

### 4.1 已找到丝上反射曲线的原始论文

Miyoshi & Matsuda，1987，*Laser-Induced Fluorescence and Optical Reflection Spectra of Japanese Natural Dyes on Silk*，JJAP **26(2):239–245**，DOI [10.1143/JJAP.26.239](https://doi.org/10.1143/JJAP.26.239)。山口大学提供[官方知识库题录](https://petit.lib.yamaguchi-u.ac.jp/135)及[公开作者稿 PDF](https://petit.lib.yamaguchi-u.ac.jp/135/files/144898)。这是**现代丝布传统日本染色的实测反射谱**，不是染液吸收，也不是苏绣古物的原始新染色。反射测量使用带积分球的双光束 UVIDEC-610C（§2）；原文未给可核验的逐点采样步长或可下载数值表。

| 目标染料 | 丝上反射谱定位 | 样本/媒染条件（原文§2，Table I） | 数据可用程度 |
|---|---|---|---|
| 红花 safflower | **Fig.6(b)**；不同曲线为光老化前后 | 植物灰；浓度没有可定量复现的完整配方 | 有实测曲线；CSV/TXT **没找到** |
| 苏木 sappanwood | **Fig.4(b)** | 实验正文说用明矾；Table I 列一般可用明矾或植物灰，不能混成两组都测了 | 同上 |
| 栀子 gardenia | **Fig.9(b)** | 本次实验正文列为不需媒染；Table I 泛列明矾、植物灰或不用，须与实验说明分开 | 同上 |
| 靛蓝 indigo | **Fig.13(b)点线 dotted curve** 是单染靛蓝；其他线为靛蓝与黄色染料套染 | 本次实验不用媒染 | 同上；不能把套染曲线当纯靛蓝 |
| 茜草 madder | 此论文 **没找到** | 不在其试样表中 | 相关丝绸研究见下；公开机器数组仍没找到 |
| 未染丝布对照 | **Fig.3(b)** | 光照老化前后 | 有曲线，适合区分基底影响，非单纤维 k |

上述图号均由论文 Figure captions 与正文核对。**(a) 面板和 Table II 给的是荧光，不是反射率；其中峰值不能填入吸收峰表。** 本报告未将图线数值化，未编造 R(λ)。这份作者稿未找到开放数据许可；可读不表示 CC0。上述目标染料的染丝分光透射 T(λ)：**没找到公开、已核验的完整数值数据**。[原始 PDF §2–3、Table I、Figure captions](https://petit.lib.yamaguchi-u.ac.jp/135/files/144898)

### 4.2 更贴近中国染丝的研究，但未取得开放数组

| 原始研究 | 可核实内容 | 未找到/访问限制 |
|---|---|---|
| Tamburini & Dyer 2019，*Fibre optic reflectance spectroscopy and multispectral imaging for the non-invasive investigation of Asian colourants in Chinese textiles from Dunhuang (7th–10th century AD)*，Dyes and Pigments **162:494–511**，DOI [10.1016/j.dyepig.2018.10.054](https://doi.org/10.1016/j.dyepig.2018.10.054) | 出版社摘要说明丝绸亚洲染料参照样本、老化前后 FORS/MSI，与敦煌文物比较；适合追查茜草等参照谱 | 本轮实时全文403，英国博物馆知识库检索未取得本篇数据包；具体逐染料图号、波段/步长、原始CSV、附件直链、数据许可均 **没找到可核验文件**，不把“数据库”理解成已开放下载。[出版社](https://www.sciencedirect.com/science/article/pii/S0143720818317716) |
| Ding et al. 2021，*Non-invasive study of natural dyes in textiles of the Qing Dynasty using fiber optic reflectance spectroscopy*，Journal of Cultural Heritage **47:69–78**，DOI [10.1016/j.culher.2020.10.013](https://doi.org/10.1016/j.culher.2020.10.013) | 摘要报告 **11种**天然染料、**4种**纤维的FORS库；古物鉴定涉及苏木、茜草、靛蓝、黄柏及套染 | 出版社全文403；逐样本丝绸数组、媒染配方、红花/栀子的确切样本与图号、补充包及许可 **没找到可核验文件**。[出版社摘要](https://www.sciencedirect.com/science/article/abs/pii/S1296207420304842) |

### 4.3 确有原始机器数据的替代资料：羊毛，不能冒充丝

Celani et al. **2024**，*Exploring elucidation of red dye mixtures on woolen historical textiles via non-destructive spectroscopic analysis and multivariate cluster analysis*，Heritage Science **12:48**，DOI [10.1186/s40494-023-01108-x](https://doi.org/10.1186/s40494-023-01108-x)；正式发表 **2024-02-07**，DOI 中2023不是发表年份。[官方全文](https://heritagesciencejournal.springeropen.com/articles/10.1186/s40494-023-01108-x)

- **204块历史红色羊毛织物**，含茜草、胭脂虫等及混合染；不是五种目标植物的丝绸单染标准库。
- 实测 FORS **350–2500 nm**，数据波长间隔 **1 nm**；分析时去掉前 **30** 个波长，从 **380 nm** 起。间隔不等于所有波段的光学分辨率。原始/预处理图见 Fig.3。
- 官方声明附件含完整 FORS/XRF 原始导出、Rmarkdown代码/输出、部分样本高清照片；正文称从 **CSV** 导入。论文 CC BY 4.0，数据默认 CC0，除非文件另注。
- [Additional file 1 官方 ZIP](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs40494-023-01108-x/MediaObjects/40494_2023_1108_MOESM1_ESM.zip)。本轮验证到官方链接与内容声明，工具不支持解压此下载，**文件名、列名、具体单染样本ID和文件级许可未核验**。

另有 CNR-IFAC 的[DyedWool 官方库](https://fors.ifac.cnr.it/dyedwool/)：**12种染料**、多数 **3种媒染**，DRS **200–2500 nm**、FORS **350–2200 nm**。这是**羊毛**；公开页面有保留版权/访问条件，匿名原始CSV下载 **没找到**，不能列作开放染丝数据。

### 4.4 渲染时怎样使用这些谱（本报告判断）

织物 R(λ) 依赖基底、纱线几何、染深、媒染、测量背衬及老化；不能唯一换算成单纤维 μa(λ)。Ding 的 Kubelka–Munk 变换给 K/S 特征，在其假设下使用，也不自动成为绝对吸收系数。染液的 UV–Vis 吸光度、FORS 反射率、荧光强度须分开。当前可先用原始丝布曲线校验颜色趋势；要做可验证的透射或逆光双面绣，仍需同一目标样品的 R/T 测量。

## 5. 真照片与显微图：逐张目录

`download.txt` 与本节图像一一对应，**每行一个地址，无网页/PDF/代码包混入**。优先保留可查到的原文件；没有从缩略图文件名猜高清地址，没有超分辨率放大或生成假图。

核验边界：已核对来源页、图注和实际图像href；部分尺寸由馆藏记录或Commons文件元数据给出。网络工具对许多图像返回Cache miss或只返回地址，本地网络也受限，**没有完成全部图像下载、逐像素查看和文件头检查**。因此下列“像素没找到”就是未知；URL中的`1024`、`lw685`、`scaled`不作像素证据。部分地址可直接访问，其他地址仍可能需要正常网络重新访问。像素顺序为宽×高，器物尺寸保持来源口径。

使用优先级（研究者判断）：D02、D04适合苏绣双面绣局部；Y03适合云锦纹理；M01/M02适合天然丝截面；K02结合已知经纬密度；F01/F02/G01有明确像素和器物尺寸，但全幅图不保证可见单纤维。没有标尺或对应器物边界的局部图不能用于线径计量。

### F01 — 清苏绣博古图镜片（全幅）

- 所在页：[上海博物馆藏品页](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/CI00004995)；[对应Commons文件页](https://commons.wikimedia.org/wiki/File:%E8%8B%8F%E7%BB%A3%E5%8D%9A%E5%8F%A4%E5%9B%BE%E9%95%9C%E7%89%87.jpg)。
- 像素：**1324×2202（Commons原文件元数据）**。
- 器物尺度/比例尺：器物长54.8、宽39 cm（馆方记录）；无单独微观标尺。
- 授权：Commons标PD-Art/PD-old；不是上海博物馆明确授予CC0。馆方页有版权保留。
- 内容与核验：苏州制作、丝绢，馆方列套针/缠针/穿珠；用作针脚方向与整体构图，不声称分辨单brin。
- 图片直链：https://upload.wikimedia.org/wikipedia/commons/6/63/%E8%8B%8F%E7%BB%A3%E5%8D%9A%E5%8F%A4%E5%9B%BE%E9%95%9C%E7%89%87.jpg

### F02 — A Myriad of Birds，旧题Embroidered Panel，1960.276

- 所在页：[克利夫兰藏品页](https://www.clevelandart.org/art/1960.276)；[Commons同件文件](https://commons.wikimedia.org/wiki/File:Unknown_artist_-_Embroidered_Panel_-_1960.276_-_Cleveland_Museum_of_Art.jpg)。
- 像素：**2200×3400（Commons同一print文件元数据；非当前新增图的像素）**。
- 器物尺度/比例尺：118.7×76.2 cm（馆方记录）。
- 授权：CC0；[馆方开放获取政策](https://www.clevelandart.org/open-access)。署名建议：Cleveland Museum of Art，1960.276；摄影Howard Agriesti。
- 内容与核验：中国清代彩丝绣于丝缎，馆方没有明确归为苏绣；馆方修复记录提示正反面褪色不同，不能当新染颜色标准。该地址由同件文件来源记录核验；本轮端点未完成文件读取。
- 图片直链：https://openaccess-cdn.clevelandart.org/1960.276/1960.276_print.jpg

### F03 — 红纳纱百蝶金双喜单氅衣：局部

- 所在页：[故宫藏品页231344](https://www.dpm.org.cn/collection/embroider/231344.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：整衣长132.5 cm、两袖通长116 cm；局部实物覆盖范围没找到。
- 授权：没找到开放许可；故宫页面保留版权及影像授权入口。
- 内容与核验：真实纳纱刺绣局部，非已确认苏绣或双面绣；整衣尺寸不可直接校准裁片。链接从页面提取，图片工具打开成功但未返回像素。
- 图片直链：https://img.dpm.org.cn/Uploads/Picture/dc/25468.jpg

### D01 — Bird on Branch：苏州双面绣全件

- 所在页：[EGA图文及图注](https://egausa.org/embroidery-technique-from-around-the-world-suzhou/)；[2020展览原目录](https://egausa.org/app/uploads/2020/03/Asian-Fusion-Exhibition-Program.pdf)。
- 像素：**没找到**。
- 器物尺度/比例尺：器物尺寸与标尺没找到。
- 授权：没找到开放许可；EGA页All rights reserved；作品为私人出借，不能假定EGA可授予作品再用权。
- 内容与核验：目录25a明确c.2000苏州双面绣，出借人记述购自苏州刺绣研究所；并非EGA自有永久藏品。实际页面图片链接。
- 图片直链：https://egausa.org/app/uploads/2020/03/AsianFusion_25a-scaled-scaled.jpg

### D02 — Bird on Branch：双面绣近照

- 所在页：[EGA图文及图注](https://egausa.org/embroidery-technique-from-around-the-world-suzhou/)；[2020展览原目录](https://egausa.org/app/uploads/2020/03/Asian-Fusion-Exhibition-Program.pdf)。
- 像素：**没找到**。
- 器物尺度/比例尺：局部实物覆盖范围及标尺没找到。
- 授权：同D01：未找到开放许可，EGA页面版权保留。
- 内容与核验：图注明确为D01局部，可对照叶片、花和羽毛的层次；不是显微或已校准照片。实际页面图片链接。
- 图片直链：https://egausa.org/app/uploads/2020/03/AsianFusion_25a2-scaled-scaled.jpg

### D03 — Panda：苏州双面绣全件

- 所在页：[EGA图文及图注](https://egausa.org/embroidery-technique-from-around-the-world-suzhou/)；[2020展览原目录](https://egausa.org/app/uploads/2020/03/Asian-Fusion-Exhibition-Program.pdf)。
- 像素：**没找到**。
- 器物尺度/比例尺：器物尺寸及标尺没找到。
- 授权：没找到开放许可；EGA页面版权保留，私人出借。
- 内容与核验：目录24a明确双面绣，含两面同签名的说明；不是由“有背面照片”推定的双面绣。读取端点Cache miss。
- 图片直链：https://egausa.org/app/uploads/2020/03/AsianFusion_24a-scaled-scaled.jpg

### D04 — 姚建萍《螳螂猫》双面绣：局部

- 所在页：[中国大运河博物馆来源的协会转载](https://www.caech.cn/zh/news/industry/35)；[馆方展览及尺寸](https://www.grandcanalmuseum.cn/yunboxinwen/849.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：整件530×780 mm（馆方记录）；局部覆盖范围及标尺没找到。
- 授权：没找到开放许可；协会转载不能代表艺术家授予复用权。
- 内容与核验：转载明确来源中国大运河博物馆，保留馆方图床；[原馆方文章](https://www.grandcanalmuseum.cn/yunboxinwen/841.html)超时。局部端点Cache miss。
- 图片直链：https://canalmuseum.net/uploads/20240922/6f4ff3c2bd6b843fee1dfd6afe79fd9e.jpg

### D05 — 《螳螂猫》双面绣：全幅

- 所在页：[中国大运河博物馆来源的协会转载](https://www.caech.cn/zh/news/industry/35)；[馆方展览及尺寸](https://www.grandcanalmuseum.cn/yunboxinwen/849.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：整件530×780 mm（馆方记录）；图外框不能作织物边界。
- 授权：没找到开放许可；同D04。
- 内容与核验：用于对应D04局部位置；不是显微图。端点Cache miss。
- 图片直链：https://canalmuseum.net/uploads/20240922/050d6444e6f43f280db31ec7a3e93c17.jpg

### D06 — 姚建萍《吹箫引凤》双面绣：全幅

- 所在页：[中国大运河博物馆来源的协会转载](https://www.caech.cn/zh/news/industry/35)；[馆方展览及尺寸](https://www.grandcanalmuseum.cn/yunboxinwen/849.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：整件510×740 mm（馆方记录）；标尺没找到。
- 授权：没找到开放许可；同D04。
- 内容与核验：转载图注明确双面绣；全幅参照。端点Cache miss。
- 图片直链：https://canalmuseum.net/uploads/20240922/aa8d8f1dfed2a2ec8aa226452f22c11a.jpg

### G01 — Fan with Landscape，62.97.25a–c：纱地丝绣团扇

- 所在页：[大都会藏品53717](https://www.metmuseum.org/art/collection/search/53717)；[Commons同件文件页](https://commons.wikimedia.org/wiki/File:Fan_with_Landscape_-_MET_62.97.25a%E2%80%93c.jpg)。
- 像素：**1568×1968（同一DP14288文件的Commons元数据）**。
- 器物尺度/比例尺：扇面直径26.7 cm；整体高41.3 cm、深1.3 cm（馆方记录）。
- 授权：大都会Public Domain / CC0开放图像；[政策](https://www.metmuseum.org/policies/image-resources)。
- 内容与核验：材质为丝绣于simple gauze；可参考底料，但馆方未明确此件为双面绣，不能据此套用其组织。地址有对应文件来源记录。
- 图片直链：https://images.metmuseum.org/CRDImages/as/original/DP14288.jpg

### K01 — Strip of Silk Tapestry (Kesi)，1916.1332

- 所在页：[克利夫兰藏品页](https://www.clevelandart.org/art/1916.1332)。
- 像素：**没找到**。
- 器物尺度/比例尺：29×170.7 cm（馆方记录）；无已核验局部标尺。
- 授权：CC0；[馆方开放政策](https://www.clevelandart.org/open-access)。
- 内容与核验：丝与金线缂丝；官方图片实际链接，动态piction端点可能变化，馆藏页为稳定回溯入口。像素未读取。
- 图片直链：https://piction.clevelandart.org/cma/ump.di?e=F3DB161573883ACB97F3FC4A26F8CD935ACDA3443C3B4D81AC4B3E9862B38663&s=24247294&se=399313166&v=1&f=%5Cd5856%5Cu3258561%5C1916.1332_o5.jpg

### K02 — Fan with Dragon，47.18.42：缂丝扇

- 所在页：[大都会藏品39642](https://www.metmuseum.org/art/collection/search/39642)。
- 像素：**没找到**。
- 器物尺度/比例尺：当前馆藏记录26×25.7 cm；旧出版物纬向25.8 cm，差异见3.5节。
- 授权：Public Domain；馆方Open Access图像可自由商业/非商业使用。
- 内容与核验：与3.5节技术分析是同一藏品；真实缂丝图，非刺绣；官方页面实际图片端点，工具打开成功但未返回文件头。
- 图片直链：https://collectionapi.metmuseum.org/api/collection/v1/iiif/39642/97470/main-image

### Y01 — 黄地桂兔纹妆花纱，故00025250

- 所在页：[故宫藏品234518](https://www.dpm.org.cn/collection/embroider/234518.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：47×48.5 cm（馆方记录）；无已核验局部标尺。
- 授权：没找到开放许可；故宫版权保留。
- 内容与核验：馆方明确列南京云锦；彩纬及金银线妆花，可辨结构参照。地址含[1024]不等于已知1024像素，未猜测更高清路径。
- 图片直链：https://img.dpm.org.cn/Uploads/Picture/dc/487%5B1024%5D.jpg

### Y02 — 石青纱妆花云蟒纹单朝袍：下裳纹饰局部，故00041727

- 所在页：[故宫藏品230423](https://www.dpm.org.cn/collection/embroider/230423.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：局部实物覆盖范围和校准标尺没找到。
- 授权：没找到开放许可；故宫版权保留。
- 内容与核验：妆花纱与金线细节。馆方说明红色丝芯可因金箔未满裹而外露，不能全当金属丝；这里列为云锦妆花工艺参照，未据整衣图反算线径。端点Cache miss。
- 图片直链：https://img.dpm.org.cn/Uploads/Picture/dc/16714%5B1024%5D.jpg

### Y03 — 黄色云锦：实物细节

- 所在页：[南京大学“ZHI艺”黄色页面](https://artlab.nju.edu.cn/heritage/jp/brocade/yellow/)。
- 像素：**没找到**。
- 器物尺度/比例尺：具体藏品编号、实物尺寸和标尺没找到。
- 授权：[项目版权](https://artlab.nju.edu.cn/heritage/jp/copyright/)：商业须书面许可；转载/下载须署名标来源；未经许可不得修改。非CC0。
- 内容与核验：项目合作方含江南丝绸文化博物馆、南京金梭云锦织造研究所。地址由图像搜索原图字段返回，预览为黄色锦地牡丹及金属线；端点Cache miss。
- 图片直链：https://artlab.nju.edu.cn/heritage/public/b/r55908-b7b162-e6dbbc.detail.jpg

### Y04 — 《宝蓝地五彩芙蓉妆花缎》，图3

- 所在页：[中国工艺美术学会刊载张道一原文](https://www.cnacs.net.cn/20/202208/4096.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：尺寸与标尺没找到。
- 授权：没找到开放许可；收藏机构供图不等于开放授权。
- 内容与核验：图注：南京云锦研究所藏；实物面料照片，端点Cache miss，不能承诺单纤维可辨。
- 图片直链：https://cmsfiles.zhongkefu.com.cn/gongyimeishu/upload/gyms/weixin/f344fb5541377140225cd621be20deee.jpg

### Y05 — 《大红地加金龙凤祥云妆花》，图5

- 所在页：[中国工艺美术学会刊载张道一原文](https://www.cnacs.net.cn/20/202208/4096.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：尺寸与标尺没找到。
- 授权：没找到开放许可；图注“作者供图”。
- 内容与核验：云锦实物面料，真实网页图像链接；端点Cache miss。
- 图片直链：https://cmsfiles.zhongkefu.com.cn/gongyimeishu/upload/gyms/weixin/657bc659f6a8e397d44f70450f93fe76.jpg

### Y06 — 《黄地凤莲纹妆花缎》，图6

- 所在页：[中国工艺美术学会刊载张道一原文](https://www.cnacs.net.cn/20/202208/4096.html)。
- 像素：**没找到**。
- 器物尺度/比例尺：尺寸与标尺没找到。
- 授权：没找到开放许可。
- 内容与核验：图注南京云锦研究所藏；真实网页图像链接，端点Cache miss。
- 图片直链：https://cmsfiles.zhongkefu.com.cn/gongyimeishu/upload/gyms/weixin/cdc462555fb71efae141f37c8471077e.jpg

### M01 — 天然丝 SEM/TEM 组合图：Choi et al. 2018，Fig.1

- 所在页：[Nature Communications论文](https://www.nature.com/articles/s41467-017-02500-5)，DOI10.1038/s41467-017-02500-5。
- 像素：**没找到**。
- 器物尺度/比例尺：正文filament约20 µm，不是各面板标尺；图内标尺数值待文件目视核验。
- 授权：CC BY 4.0；署名Choi et al., Nature Communications 9:452；页面未见此图另列第三方例外。
- 内容与核验：b/c为SEM，d–f为TEM；a为示意、j为重建，不能称全图都是照片。已核验image href；这是网页图，不是已核实最高分辨率原图。
- 图片直链：https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41467-017-02500-5/MediaObjects/41467_2017_2500_Fig1_HTML.jpg

### M02 — 原茧/脱胶单纤维截面：Yaiphabi et al.，Fig.7

- 所在页：[原论文](https://link.springer.com/article/10.1007/s10973-025-15115-6)。
- 像素：**没找到**。
- 器物尺度/比例尺：正文c丝胶约850 nm；f膜厚11.48 µm是膜而非丝直径；图内比例尺未目视核验。
- 授权：CC BY-NC-ND 4.0；署名Yaiphabi et al.；不授权商业利用或传播改编图。
- 内容与核验：a–c为原茧双丝，d为脱胶brin，e/f为再生膜；仅a–d适合天然纤维截面参照。网页image href已核验，原图像素未读取。
- 图片直链：https://media.springernature.com/lw685/springer-static/image/art%3A10.1007%2Fs10973-025-15115-6/MediaObjects/10973_2025_15115_Fig7_HTML.png

### M03 — 敦煌唐代丝绣：真实丝纤维VP-SEM，Fig.4

- 所在页：[Tamburini et al.原论文](https://link.springer.com/article/10.1007/s12520-017-0592-4)；[英国博物馆公开作者PDF](https://www.bmitpglobalnetwork.org/wp-content/uploads/2022/05/An-investigation-of-the-dye-palette-in-Chinese-silk-embroidery-from-Dunhuang.pdf)。
- 像素：**没找到；此href为m312网页预览，非已确认原图**。
- 器物尺度/比例尺：全绣品167×249 cm（论文记录）；面板标尺未能目视核验，不能用整品大小校准SEM。
- 授权：图版权C. R. Cartwright / ©Trustees of the British Museum；论文版权保留，未找到开放图许可。公开PDF不等于CC BY。
- 内容与核验：图4是不同劣化状态丝纤维，非苏绣；图3为麻/亚麻，不能误当丝。适合看真实退化与粒子，不适合当新绣线粗糙度标定。
- 图片直链：https://media.springernature.com/m312/springer-static/image/art%3A10.1007%2Fs12520-017-0592-4/MediaObjects/12520_2017_592_Fig4_HTML.gif

### 5.1 有重要显微/高分辨率材料，但没有纳入纯图片清单

| 来源 | 可确认内容 | 尺度、像素和授权限制 |
|---|---|---|
| 陈杨《缂丝文物展前保护处理之探索》，《故宫学刊》2014，[故宫PDF](https://www.dpm.org.cn/Uploads/File/2020/02/19/u5e4d030ec8c19.pdf) | 图六为体视显微镜下的捻金线，金箔条螺旋包丝芯；图十四为污染物显微观察。与3.4节实物密度配合，比仅有全幅图更有用 | 独立图像直链、像素及可读标尺 **没找到**；图十六/十七是结构图，非实拍。未找到开放授权，故宫版权；不把PDF冒充JPG加入清单 |
| [IIC-ITCC 2017，A Study on Kesi Tapestry，Shi，Part II](https://www.iiconservation.org/sites/default/files/news/attachments/8574-iic-itcc_2017_a_study_on_kesi_tapestry_shi_part_ii.pdf) | 真缂丝的纤维显微/偏光观察，文中有400×观察 | 放大倍数不是可跨文件校准的像素比例尺；独立图片、像素、开放许可 **没找到** |
| 台北故宫[《宋緙絲八仙拱壽》开放数据页](https://digitalarchive.npm.gov.tw/opendata/Pub/DetailEng/1903?dep=P&mode=full) | 本幅82.7×40.4 cm、全幅82.7×58.6 cm（馆藏记录）；页面有多张图与IIIF入口 | 页面明示低分辨率CC0、高分辨率CC BY4.0。高分辨率下载带验证码；本轮未取得可核验的高分辨率文件/像素/永久图片直链，不猜地址。应署名The National Palace Museum, Taipei |
| [Smithsonian《Kesi tapestry of birds and snow-laden trees》F1918.11](https://asia.si.edu/explore-art-culture/collections/search/edanmdm%3Afsg_F1918.11/) | 真缂丝，馆录54.3×28.2 cm，有两视图/IIIF入口 | 本轮馆方页反复服务器错误，未取得可核验图片文件及图像许可，不将机构总体开放政策套用到这张未核验文件 |

本轮 **没找到** 带校准标尺且可核验开放授权的苏绣、双面绣、云锦显微原图。V&A、苏州丝绸博物馆的这类公开可核验图像也 **没找到**；不把展览海报、商业仿品或机器绣当作替代证据。

## 6. 对下一步物理渲染的具体含义与剩余缺口

以下是本报告的实现判断，不伪装成论文参数：

1. **几何先按实际用线确定层级。** 保留brin、丝胶双丝、工艺束/ply和针脚四个尺度；三角截面并非理想等边。Zhao的三股有捻丝纱参数不能自动套给铺平、少捻的劈丝绣线。
2. **物性与拟合颜色分开。** n∥/n⊥文献参考值不是完整谱；Perotto是薄膜；Khungurn/Zhao的RGB是模型参数。不要把两者拼接成“实测天然丝光谱材质”。Aliaga粗糙度的表/公式冲突先保留未知。
3. **双面绣要验证透射和背面结构。** 当前缺少底料的具体组织密度、纱径、厚度及R/T谱；现成黑背衬反射拟合不能填补此缺口。结与藏线方式也需目标绣品正反面同区照片。
4. **可先选一件缂丝做受约束复现。** 《应真飞锡图》有22/46根每厘米与用线组合；《龙纹缂丝扇》另有34与约90–120根每厘米。分别使用，不能混合为同件样品。
5. **补测最能改变方案的未知。** 同一样品带标尺的正/背/透光近照、单纤维截面与束内根数、同照明多角度高光、同背衬反射/自由悬挂透射；植物染须记录配方/媒染/老化和仪器条件。这是未来建议，**本次没有实施采样或实验**。

已完成：公开原始资料与可访问元数据的整理、参数性质分类、照片真实来源/授权/尺度登记、纯图片地址清单。仍受限：未取得的数值与原图均如实标记；没有声称下载包已编译、光谱CSV已解压，或全部图像已逐像素验证。不存在将“没找到”替换成无出处默认值的项目。
