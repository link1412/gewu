# 中国古代高锡青铜镜：光学数据、漆古表层与馆藏照片

检索日期：2026-11-02。目标配比按**质量比** Cu:Sn≈3:1（Cu75Sn25）理解；若实际指原子比，材料并不相同。全文区分原始实测、基于实测的计算、读图近似及渲染假设。

## 1. 结论与建议采用的数据

推荐把材质分成“裸露抛光高锡合金”和“覆盖其上的老化复合表层”。最贴近目标配比的可用定量证据，是英国博物馆测得的 **Sn 26.1 wt% 抛光样品的 CIELAB：L*=83.76、a*=2.57、b*=10.47**。它支持略暖、低彩度的灰白色，而非把镜铜直接设成普通黄铜色；但 Lab 是特定测量条件下的颜色，不能直接充当金属着色器的反射率。[Radivojević et al., Tables 1、5、§2.3](https://doi.org/10.1016/j.jas.2017.12.001)

光谱方面，找到三条有效证据链：

| 资料 | 实际取得内容 | 与目标的差距 |
|---|---|---|
| Callet：Cu–Sn 椭偏测量 | 10%、20%、30% Sn 的可见光光学常数曲线，已下载 PDF | 没有25%样品；公开文件是低清曲线，不是可直接导入的 n/k 数表。[原文 §2.5、Fig.6](https://www.astrale3d.com/doc/Virtual_Restoration.pdf) |
| Kaiser et al. 2010 | 基于上述实测常数计算的 20%、30% Sn 法向反射率，400–700 nm；已提取高清图并整理读图 CSV | 属于“实测常数→计算反射率”，不是独立光谱反射率实验；不能直接插值成25%。[Fig.4、p.8](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 历史望远镜/镜铜文献 | 1929 年直接测量曲线；1947 年原始摘要中的450、650 nm端点 | 1929样品配比未说明；1947样品含锡45%，明显不同于25%。[Coblentz & Stair](https://doi.org/10.6028/jres.002.005)、[Tolansky & Donaldson](https://doi.org/10.1088/0950-7671/24/9/308) |

**没有取得可声称为 Cu75Sn25、380–780 nm 全波段实测的 n/k 数表，也没有取得水银沁/黑漆古的标定可见反射谱或 Lab 数表。** 下文保留缺口，不用纯 Cu、Sn、Hg 的参数混合或照片取色补成“实测”。高清馆藏镜面照片已经取得，但其现存表面含蚀斑；洁净抛光高锡中国古镜的明确照片证据仅为低分辨率局部图。

## 2. 镜铜与高锡青铜的光谱证据

### 2.1 最相关的 n、k 测量：Callet 的 Cu–Sn 合金

Callet 的 *Virtual Restoration of Bronze—3D Capture and Optical Simulation in Parallel Spectral Ray-Tracing*，PDF第7页说明合金为 **10%、20%、30% Sn，质量百分比**；第9页 §2.5、Fig.6 给出抛光面的椭偏测量曲线。它们是重新配制的实验合金，不是古镜腐蚀层测量。[原始 PDF](https://www.astrale3d.com/doc/Virtual_Restoration.pdf)；[本地全文](papers/Callet_Virtual_Restoration_of_Bronze.pdf)。

![Callet的光学常数曲线，原始图清晰度有限](img/Callet_Fig6_optical_constants.png)

**必须核对定义：**该文写的是 \(\tilde n=n(1+i\kappa)\)，因此若渲染器采用 \(\tilde n=n+ik\)，应输入 **\(k=n\kappa\)**，不能把图右侧的 κ 原样当作消光系数 k。曲线横轴覆盖可见区，约380–780 nm；下载版两幅原始嵌图仅220×176、221×177像素，无法可靠恢复高精度数表。本报告只展示原图，不编造小数位。[同文 PDF第9页公式及Fig.6](https://www.astrale3d.com/doc/Virtual_Restoration.pdf)

同组原始研究 *Rendering of Binary Alloys—Example and Validation with Bronze* §3 称仪器原始数据在 **200–1200 nm、1 nm间隔**取得，图中只画了简化数据；这说明全可见测量确实存在，但本次未找到该原始数组的公开下载。[作者上传全文 §3](https://www.researchgate.net/publication/336854878_RENDERING_OF_BINARY_ALLOYS_Example_and_validation_with_bronze)

### 2.2 可直接读取的近目标反射率曲线：Kaiser et al. 2010

Norbert Kaiser 等，*A journey from ancient China: bronze mirrors to picometer-shaped interference coatings*，Chinese Optics Letters 8(S1), 7–11，DOI 10.3788/COL201008S1.0007。Fig.4 是用 Callet 的复折射率计算的**法向反射率**。作者把 Cu70Sn30 描述为可见区大约50%反射、50%吸收的近中性色材料。[原文p.8及Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf)；[本地全文](papers/Kaiser_2010_Journey_ancient_China_mirrors.pdf)。

![Kaiser2010 Fig4原始嵌图](img/Kaiser_2010_Fig4_reflectance.png)

以下是**本次人工读图近似**，R为0–1的能量比例；读图不确定度保守取±0.02（绝对反射率，非论文实验误差）。精确原始数字未公开，不能把这些行标成逐波长仪器测量。

| 波长/nm | Cu80Sn20：R≈ | Cu70Sn30：R≈ | 出处 |
|---:|---:|---:|---|
| 400 | 0.45 | 0.50 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 450 | 0.50 | 0.49 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 500 | 0.59 | 0.48 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 550 | 0.75 | 0.48 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 600 | 0.83 | 0.47 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 650 | 0.85 | 0.47 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |
| 700 | 0.85 | 0.47 | [Fig.4](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf) |

文件：[data/Kaiser2010_Fig4_readout.csv](data/Kaiser2010_Fig4_readout.csv)。**380–400、700–780 nm没有从此图取得数据。**两条曲线尤其在红端差别很大，应保留为不同样品参照，不把它们的算术平均称为25%锡的实测值。图中纯Cu红端接近100%，也提示这套历史数据不宜单独承担高精度绝对辐射定标。

### 2.3 直接实测：Coblentz & Stair，1929

*Reflecting power of beryllium, chromium, and several other metals*，Bureau of Standards Journal of Research 2, 343–354，RP39。§III.5、p.350指出镜铜样品重新抛光以去除失光层；Fig.5在p.351。该文测量配置为**45°入射**，不是严格法向值；高抛光表面与抛光差异会影响结果。[原始全文](https://nvlpubs.nist.gov/nistpubs/jres/2/jresv2n2p343_A2b.pdf)；[本地PDF](papers/Coblentz_Stair_1929_Reflecting_power_RP39.pdf)。

![1929年镜铜直接测量曲线](img/Coblentz_1929_Fig5_speculum.png)

Fig.5 中 **C.&S. Speculum** 是实线空心圆，不能误取上方实心点的 cobalt：在约400、450、550 nm处读图约 **55%、59%、61%**，读图约±2个百分点。该曲线主要覆盖紫外至约560 nm，样品Cu/Sn配比未注明，不能代表指定的Cu75Sn25；虚线 Hulburt 是另一组旧测量。[p.350–351、Fig.5](https://nvlpubs.nist.gov/nistpubs/jres/2/jresv2n2p343_A2b.pdf)

### 2.4 经典镜铜实测：Tolansky & Donaldson，1947

*The Reflectivity of Speculum Metal*，Journal of Scientific Instruments **24(9), 248–249 (1947)**，DOI 10.1088/0950-7671/24/9/308。ResearchGate 显示的2002年日期不应当作原始发表年份；档案目录也将该文列在1947年。[原文DOI](https://doi.org/10.1088/0950-7671/24/9/308)、[伦敦大学Tolansky档案MS827/D/19](https://archives.libraries.london.ac.uk/resources/MS827.pdf)

本次未取得原始两页全文；以下来自**原论文摘要在ResearchGate的转载**，不是读到全文后的仪器配置核验。摘要明确新抛光电沉积样品含 **45%锡**，测量450–650 nm；蒸发膜反射率更高。[原摘要转载](https://www.researchgate.net/publication/231146129_The_Reflectivity_of_Speculum_Metal)

| 波长/nm | 新抛光电沉积镜铜R | 蒸发于玻璃上的镜铜R | 出处 |
|---:|---:|---:|---|
| 450 | 0.63 | 0.68 | [原摘要](https://www.researchgate.net/publication/231146129_The_Reflectivity_of_Speculum_Metal) |
| 650 | 0.75 | 0.78 | [原摘要](https://www.researchgate.net/publication/231146129_The_Reflectivity_of_Speculum_Metal) |

文件：[data/Tolansky1947_abstract_endpoints.csv](data/Tolansky1947_abstract_endpoints.csv)。摘要还报告潮湿空气存放半年后，红区下降10%、蓝区下降2%；**没有全文核定其相对百分比/百分点含义，本报告不换算成精确老化后端点**。这些不是古镜水银沁/黑漆古的实测反射率。[同一原摘要](https://www.researchgate.net/publication/231146129_The_Reflectivity_of_Speculum_Metal)

### 2.5 现代镜铜实测线索，未取得完整光谱

Nazimudeen、Girish、Abraham，2018，*On the nature of thin films of speculum metal*，Materials Today Communications 16, 314–319。原文研究 Aranmula 铸造抛光镜及热蒸发薄膜，使用EDS、AFM、XRD及UV–Visible光谱；出版社公开片段给反射面Cu约 **62–69%**、Sn约 **30–32%**，指出蒸发膜反射率更高。公开摘要/片段不足以恢复逐波长值，未下载到全文，因此不提供假造的R表。[出版社原始页面与摘要](https://www.sciencedirect.com/science/article/pii/S2352492818301302)、[DOI](https://doi.org/10.1016/j.mtcomm.2018.07.005)

## 3. 抛光合金的实测颜色：接近25%锡的定量锚点

Radivojević 等，*Experimental design of the Cu–As–Sn ternary colour diagram*，Journal of Archaeological Science 90 (2018), 106–119。已取得UCL作者接受稿。测色前用SiC至4000 grit抛光；英国博物馆 Minolta CM-2600D，**d/8°、SCI（包含镜面分量）、D65、10°标准观察者、3 mm孔径，每样本5次测量取平均**。下表合金实际成分来自pXRF，不是预设投料比例。[原始接受稿§2.2–2.3、Tables 1、5，PDF第6–7、27、31页](https://discovery.ucl.ac.uk/id/eprint/10042747/1/Radivojevic%20et%20al%202017%20Cu-As-Tin%20Colour%20RPS.pdf)

| 样品号 | Cu/Sn实测wt% | L* | a* | b* | 原文转换RGB，8 bit | 出处 |
|---|---|---:|---:|---:|---|---|
| 10 | 78.6 / 21.4 | 85.81 | 3.55 | 12.45 | 231,212,191 | [Tables 1、5](https://doi.org/10.1016/j.jas.2017.12.001) |
| **23** | **73.9 / 26.1** | **83.76** | **2.57** | **10.47** | **222,207,189** | [Tables 1、5](https://doi.org/10.1016/j.jas.2017.12.001) |
| 9 | 68.5 / 31.5 | 84.43 | 1.42 | 6.13 | 218,209,199 | [Tables 1、5](https://doi.org/10.1016/j.jas.2017.12.001) |

[本地PDF](papers/Radivojevic_2018_Cu_As_Sn_colour.pdf)；[CSV](data/Radivojevic2018_CuSn_CIELAB.csv)。RGB为作者从Lab转换后的显示色，**不是反射率或PBR base color**；优先保留Lab及测量条件。其制样也不是光学望远镜级抛光，不宜把该颜色测量等同于理想镜面BRDF。论文提醒孔隙会影响尤其是L*。[同文§2.3](https://doi.org/10.1016/j.jas.2017.12.001)

Fang & McDonnell，*The colour of copper alloys*，Historical Metallurgy **45(1) (2011), 52–61**，也直接使用积分球分光测色，观察18–33 wt%锡由金色转向银色。官网数字发布日期2021不代表卷期年份。本次下载接口返回HTML验证页，未将它伪存为PDF；未读到表格，故这里只列原始研究线索。[期刊原始条目](https://hmsjournal.org/index.php/home/article/view/141)

## 4. 水银沁、黑漆古：成分与表层结构

### 4.1 名称与真正的物质层不能画等号

“水银沁/银沁”是银白、油润光泽的外观叫法；“黑漆古”是黑、光滑、玉质或油润表面的叫法。**名称本身不能证明存在汞、银或大漆。**相关原始研究按银、黑、深绿分组，并发现同属高锡含铅基体的镜子具有不同表面状态。[Wang et al. 2024，Introduction、Tables 1–2](https://doi.org/10.1186/s40494-024-01247-9)

真实的汞齐镀锡工艺与“水银沁”名称应分开判断。Anheuser 的实验及古样复核指出，痕量Hg也可能来自污染；单凭银白外观不能证明汞齐制作。[Anheuser 2000，原始摘要](https://doi.org/10.1111/j.1475-4754.2000.tb00875.x)

### 4.2 与目标配比接近的馆藏镜：基体实测

Wang et al. 2024，*New insights on the analysis of the causes of glossy lustre on the surface of ancient Chinese bronze mirrors*，Heritage Science 12:136，Table 2（PDF第4页）：SEM–EDS在截面未腐蚀基体测量，wt%。只选与目标相关的四例；这些是**基体合金**，不是表层有效光学常数。[正式原文Tables 1–2](https://doi.org/10.1186/s40494-024-01247-9)

| 样本 | 馆藏、时代与表面分类 | Cu | Sn | Pb | 出处 |
|---|---|---:|---:|---:|---|
| JN06 昭明镜 | 济南博物馆，西汉，银沁 | 71.0 | 24.9 | 4.1 | [Tables 1–2](https://doi.org/10.1186/s40494-024-01247-9) |
| JN68 四乳四禽纹镜 | 济南博物馆，东汉，银沁 | 70.1 | 24.6 | 5.3 | [Tables 1–2](https://doi.org/10.1186/s40494-024-01247-9) |
| JZ09 四兽四乳铭文镜 | 莒县博物馆，汉，黑漆古 | 69.0 | 25.2 | 5.8 | [Tables 1–2](https://doi.org/10.1186/s40494-024-01247-9) |
| JZ12 柿蒂连弧铭文镜 | 莒县博物馆，汉，黑漆古 | 68.0 | 29.3 | 2.7 | [Tables 1–2](https://doi.org/10.1186/s40494-024-01247-9) |

### 4.3 有哪些表层证据，哪些仍为机制推断

| 层次/机制 | 证据与数值 | 对渲染的含义与限制 |
|---|---|---|
| 选择性腐蚀与残余金属相 | Taube、King、Chase的古镜截面及模型青铜实验：altered layer可达**100 μm**，α相优先失铜并被锡氧化物替代，δ相保留金属。[2008原始摘要](https://doi.org/10.1080/01411590701514375) | 表面光滑不等于完全未腐蚀；不能把整层视为连续裸金属。全文未取得。 |
| 有机铅皂 | SEM–EDS、Raman及THM-Py-GC/MS支持馆藏镜截面析出物为高级有机酸铅盐；作者观察其对应原铅相。[Wang2024，Figs.2–9](https://doi.org/10.1186/s40494-024-01247-9) | 直接证据是有机物存在；其铺展、老化使表面油润/暗化属于作者的机制解释，尚非可用于拟合的光学常数。 |
| 腐蚀层厚度与颜色 | 同文讨论概括：银沁腐蚀层一般**<50 μm**，黑漆古一般**>150 μm**。[PDF第17–18页](https://doi.org/10.1186/s40494-024-01247-9) | 是腐蚀层厚度，**不是透明铅皂膜厚**；不同实物的经验范围，不能直接当薄膜干涉厚度。 |
| 富锡腐蚀物的纳米结构 | Jiang等：Ⅰ类锈主晶相约**5 nm SnO₂纳米晶**，并有含Cu无定形组分。[2024原始研究](https://doi.org/10.1186/s40494-024-01472-2) | 研究对象是钉、戈、斧、刀等，并非镜；只作无机表层机制旁证，不能把SnO₂单晶参数直接当黑漆古。 |
| 最新着色机制 | Wang等2026研究**12面镜**，区分α优先、δ优先及两相完全腐蚀，联系金属皂氧化程度与颜色。[出版社摘要](https://doi.org/10.1007/s12520-026-02474-w) | 全文付费未取得；摘要没有提供可复用的可见反射率或Lab数值。 |

Wang2024的正式全文已保存；预印本还有不同样本的截面厚度数据，但未将它们混入上表作为正式文结论。更完整的成分与预印本证据见[表层调研笔记](patina-notes.md)。

![馆藏古镜漆古对照，主要是镜背](img/Wang_2024_Fig1_museum_mirror_patina_samples.png)

图为Wang2024 Fig.1馆藏样品，适合比较银白、黑亮、绿锈与脱层分布；多数是镜背，不能当洁净镜面色卡。[原图](https://media.springernature.com/full/springer-static/image/art%3A10.1186%2Fs40494-024-01247-9/MediaObjects/40494_2024_1247_Fig1_HTML.png)

**没有找到：**银沁、黑漆古的标定VIS R(λ)、完整有效n/k、BRDF或CIELAB数表。Liang & Parker2021虽给反射谱，但实际测的是镜3孔雀石锈的**1.8–2.4 μm近红外**，不能用来替代可见光镜面数据；该文镜2还可能是现代复制品。[原文Infrared spectroscopy与Discussion](https://doi.org/10.1186/s40494-021-00496-2)

## 5. 博物馆原图：镜面与镜背分别使用

### 5.1 主要外观参照

**京都国立博物馆JK103《内行花文精白鏡》，西汉，直径18.2 cm。**下图为真正照人正面，**3000×2992像素**，可见大面积黑亮表面与灰银、褐色、绿色蚀斑。馆方英文题名是“Polished Mirror”，但未公布当前表面的重新抛光史，也未将其化学鉴定为水银沁/黑漆古。因此可作现存古镜外观参照，不能认作无腐蚀合金本征色。[馆方记录](https://knmdb.kyohaku.go.jp/eng/6366.html)、[官方原图](https://knmdb.kyohaku.go.jp/art_images/230/229984_difile2-L.jpg)

![京都JK103照人正面](img/kyoto_JK103_229984.jpg)

**长沙市博物馆战国镜，总账号4817、分类号1B313，约前300年，直径11.4 cm。**原始研究明确描述高锡、银白及反复研磨抛光；Fig.1b为照人面强高光局部，原图仅**442×296**。它是明确抛光状态的工艺/光泽参照，不能称为高清全镜面图。[Li原始研究，Fig.1与Traces of Lapidary Tool-Use段](https://doi.org/10.1017/eac.2023.6)、[原图](https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:binary:20240525132542898-0374:S0362502823000068:S0362502823000068_fig1b.png?pub-status=live)

![长沙4817抛光正面局部](img/changsha_4817_fig1b.png)

### 5.2 已下载馆照索引

| 对象与本地文件 | 像素 | 正背面与用途 | 第一方来源 |
|---|---:|---|---|
| [京都JK103镜面](img/kyoto_JK103_229984.jpg) | 3000×2992 | 正面，黑亮/斑驳主参照 | [馆页](https://knmdb.kyohaku.go.jp/eng/6366.html) |
| [JK103背面](img/kyoto_JK103_229983.jpg)、[侧视](img/kyoto_JK103_229985.jpg)、[旧背照](img/kyoto_JK103_3136.jpg) | 3000×2977；3000×937；3000×2983 | 同物纹饰/表面辅助 | [馆页](https://knmdb.kyohaku.go.jp/eng/6366.html) |
| [长沙4817镜面局部](img/changsha_4817_fig1b.png) | 442×296 | 正面，高锡抛光证据 | [原始论文](https://doi.org/10.1017/eac.2023.6) |
| [长沙4817背面](img/changsha_4817_fig1a.png)、局部[c](img/changsha_4817_fig1c.png)/[d](img/changsha_4817_fig1d.png)/[e](img/changsha_4817_fig1e.png) | 413×400；局部各597×400 | 背面，工艺纹理 | [原始论文](https://doi.org/10.1017/eac.2023.6) |
| [京都JK126唐镜正面](img/kyoto_JK126_229987.jpg)、[背面](img/kyoto_JK126_229986.jpg)、[侧视](img/kyoto_JK126_229988.jpg) | 3000×2965；2958×3000；3000×931 | 红绿锈覆盖的腐蚀对照 | [馆页](https://knmdb.kyohaku.go.jp/eng/6389.html) |
| [上海西汉“见日之光”镜](img/shanghai_westernhan_jianrizhiguang_back.jpg) | 3614×2900 | **背面**，灰银与红绿锈；CI00000342是网页ID，非已证藏品号 | [馆页](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/CI00000342) |
| [克利夫兰1926.248唐镜](img/cleveland_1926.248_tang_back.jpg) | 3400×3288 | **背面**，银灰与绿色氧化；CC0 | [馆页](https://www.clevelandart.org/art/1926.248) |
| [辛辛那提x1961.2正面](img/cincinnati_x1961.2_comparison_front.jpg)、[背面](img/cincinnati_x1961.2_comparison_back.jpg)、[演示](img/cincinnati_x1961.2_comparison_demo.jpg)、[斜视](img/cincinnati_x1961.2_comparison_oblique.jpg) | 1000×1357；1000×1358；1000×668；1000×667 | **日本辅助参照**，不是已确认中国镜。2022馆文曾标中/日，2025馆方改归日本14–15世纪 | [2022馆文](https://www.cincinnatiartmuseum.org/about/blog/a-new-discovery-in-cam-a-magic-mirror/)、[2025馆方记录](https://www.cincinnatiartmuseum.org/art/exhibitions/exhibition-archive/2025/rediscovered-treasures/audio-exhibition/) |

每张馆图的**直接原始文件URL**、版权信息及完整侧别说明另存[图片来源清单](museum-notes.md)。图片均为下载原图，未做超分辨率或调色。仅作参照，不限授权；再次公开发布图片时需按各馆条件处理。

## 6. 如何把证据用于渲染

以下是依据上述资料的**建模建议，而非新增材料实测**：

1. **洁净镜面状态**：先以接近目标的26.1%锡测色约束色调，再以历史直接反射测量与20/30%样品曲线约束反射强度。若使用Cu70Sn30曲线作临时替代，应在材质名/注释中明确写“30%实验合金近似”，不能写成Cu75Sn25实测。
2. **银沁状态**：保留亮部的金属反射，同时用空间变化的矿化覆盖、粗糙度、微裂纹及可能有机层表达油润与失光。不能因名字而直接调用水银材质。
3. **黑漆古状态**：使用有吸收/散射的复合表层及其表面高光，局部暴露残余金属；不要只把裸金属反射色整体乘黑。厚腐蚀层与外侧有机层分开建模，文献中的微米级腐蚀层不能当纳米光学薄膜。
4. **照片用途**：京都镜面约束斑驳尺度和黑亮区域分布，长沙局部约束抛光高光；馆照没有色卡、曝光与光源标定，不能从RGB反推F0或n/k。SCI Lab也不能直接当线性RGB反射率。

对均匀光滑导体、空气中法向入射，\(R_0=((n-1)^2+k^2)/((n+1)^2+k^2)\)。单个R值只有一个约束，不能唯一求出两个未知数n、k。因此本报告没有把读图反射率伪反演成n/k。

若下一步需要有计量意义的Cu75Sn25全波段材质，决定性缺项是**指定配比、相组成、抛光/氧化状态的380–780 nm原始椭偏或反射测量**。应获得Callet原始数组或测量匹配样片，并同时记录镜面/总反射几何；银沁/黑漆古还需要对应实物区域的光谱与表层参数。当前证据足以构造可说明来源的外观近似，尚不足以宣称三种状态均已物理定标。

## 7. 本地论文与数据目录

| 本地PDF | 来源与内容 |
|---|---|
| [Callet_Virtual_Restoration_of_Bronze.pdf](papers/Callet_Virtual_Restoration_of_Bronze.pdf) | [原始PDF](https://www.astrale3d.com/doc/Virtual_Restoration.pdf)，20页，合金椭偏曲线 |
| [Kaiser_2010_Journey_ancient_China_mirrors.pdf](papers/Kaiser_2010_Journey_ancient_China_mirrors.pdf) | [原始PDF](https://www.researching.cn/ArticlePdf/m00005/2010/8/s1/COL08FOC0007.pdf)，5页，Fig.4反射率 |
| [Coblentz_Stair_1929_Reflecting_power_RP39.pdf](papers/Coblentz_Stair_1929_Reflecting_power_RP39.pdf) | [NIST原始PDF](https://nvlpubs.nist.gov/nistpubs/jres/2/jresv2n2p343_A2b.pdf)，12页，镜铜直接测量 |
| [Radivojevic_2018_Cu_As_Sn_colour.pdf](papers/Radivojevic_2018_Cu_As_Sn_colour.pdf) | [UCL接受稿](https://discovery.ucl.ac.uk/id/eprint/10042747/1/Radivojevic%20et%20al%202017%20Cu-As-Tin%20Colour%20RPS.pdf)，31页，含近25%锡Lab |
| [Wang_2024_glossy_lustre_bronze_mirrors.pdf](papers/Wang_2024_glossy_lustre_bronze_mirrors.pdf) | [出版社PDF](https://www.nature.com/articles/s40494-024-01247-9.pdf)，19页，馆藏镜成分与有机物证据 |
| [Jiang_2024_type_I_corrosion.pdf](papers/Jiang_2024_type_I_corrosion.pdf) | [出版社PDF](https://www.nature.com/articles/s40494-024-01472-2.pdf)，14页，富锡锈结构旁证 |
| [Liang_Parker_2021_four_bronze_mirrors.pdf](papers/Liang_Parker_2021_four_bronze_mirrors.pdf) | [出版社PDF](https://www.nature.com/articles/s40494-021-00496-2.pdf)，20页，四镜表面与NIR鉴定 |
| [Li_2024_Mechanical_treatments_bronzes_jades.pdf](papers/Li_2024_Mechanical_treatments_bronzes_jades.pdf) | [出版社原始全文](https://doi.org/10.1017/eac.2023.6)，43页，长沙抛光镜照片 |
| [Wang_2023_black_quicksilver_preprint.pdf](papers/Wang_2023_black_quicksilver_preprint.pdf) | [Research Square v1](https://assets-eu.researchsquare.com/files/rs-3533469/v1/4ad58ef0-0a7b-423b-a54a-9c123bb984ba.pdf?c=1715112489)，24页，2024正式论文的预印本，未混用其版本差异 |
| [Yao_2020_two_tin_rich_mirrors_preprint.pdf](papers/Yao_2020_two_tin_rich_mirrors_preprint.pdf) | [Research Square v1](https://assets-eu.researchsquare.com/files/rs-114203/v1_covered.pdf)，30页，两镜富锡层预印本 |

额外机器可读数据在[data/](data/)：反射率读图、1947摘要端点、实测Lab三份CSV，均自带来源与数据性质。已保存10份PDF、22张图片（18张馆照、1张论文馆藏对照图、3张光学图）及3份CSV。所有PDF已检查文件头并成功解析，关键数表与镜面图已目视核对；文件校验清单见[asset-manifest.tsv](asset-manifest.tsv)。

下载限制：1947镜铜论文、2018薄膜镜铜论文、2008古镜表层论文及2026着色论文未取得全文；Fang下载返回验证HTML，未保留伪PDF。Getty旧公开路径失效，未用二手转录表补充定量数据。


