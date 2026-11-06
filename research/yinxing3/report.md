# 黄银杏叶背光真值：第二次获取与证据核查

调查日期：2026-11-02。已先读上一轮 [`../yinxing2/report.md`](../yinxing2/report.md)。本报告重点记录这轮新增调查；复用原件明确标注。

## 结论与推荐用途

**仍未取得新鲜秋黄银杏叶的校准透射照片、可确定对应黄银杏的 T(λ) 数值／曲线，或其同叶 R/T。Mander 完整 Dryad 包重试仍受阻。** 没有用照片取色、夏季银杏或其他物种来填补这个缺口。

| 优先目标 | 本轮实得／状态 | 能否用于目标真值 |
|---|---|---|
| Mander 完整包 | 公开网页及整包接口403、API401；未发现完整镜像。复用作者示例中的5张含黄／橙黄JPEG及新增原文拍法摘录 | 干压叶、无颜色校准；不是完整包下载成功 |
| 黄银杏 T(λ)，最好同叶 R/T | 新发现 LOPEX_ZJU 明确含衰老银杏、实际测过同叶R/T；未取到其逐样本数据或黄银杏可识别曲线 | 有价值的测量线索，尚不是可用光谱 |
| 有校准线索的黄叶／空间透射 | MapS-Wear 八通道**归一化透射**工作簿和已知灯光测法；HyperART 空间透射论文图及测法 | 都有下文所列限制；没有黄银杏校准图或公开高光谱立方体 |
| 新鲜黄银杏高清外观 | 新增2024年2000×3000在枝照片；复用上一轮明确阳光透射的2021年3028×3028原图 | 可看条纹、褐斑／褐边；无绝对颜色／亮度标定 |

建议继续用上一轮已取得的 Noda 黄叶积分球 T 或 Morimoto 黄山药方向 T 作为**其他物种的物理范围参考**，用当前银杏照片检查空间纹理。新的 MapS-Wear 数据已确认经过通道总和归一化、缺少恢复幅值的信息，不可用于绝对透射亮度或完整可见光颜色真值。积分球半球透射率、传感器有限视角比值和后期JPEG亮度属于不同量；仅知道色温也不能恢复照明SPD。上一轮文件仍在原目录，本轮没有复制整套既有 R/T 数据。



## 1. Mander 2021：已重试，完整包仍未取得

数据：[Living and fossil Ginkgo leaves](https://doi.org/10.5061/dryad.7h44j0zsj)，CC0 1.0。原清单只有 `Supplementary_Information.zip`，745,843,529 字节；发布 SHA-256 `125e541c2aec474138f14bc879e3575639da59307fd9217354d58f75a801c9a2`。**该值来自清单，本轮没有取得 ZIP，不能称已验证 ZIP 哈希。** [实时文件元数据](https://datadryad.org/api/v2/files/1145562)。

| 重试路线 | 本轮结果 |
|---|---|
| [网页原文件](https://datadryad.org/downloads/file_stream/1145562)及旧 `/stash/downloads/` 路径 | HTTP 403；旧路径重定向到当前路径 |
| [文件 API 下载](https://datadryad.org/api/v2/files/1145562/download)、数据集 API 下载 | HTTP 401；[官方文档](https://github.com/datadryad/dryad-app/blob/main/documentation/apis/api_accounts.md)明确下载需 API token |
| [论文公开分享链接](https://datadryad.org/stash/share/FMnz1duxMAX_RmH7gkCdq385OeWeUuTux9rinUzmSBo) | 可读，重定向到公开落地页；下载仍指向相同受阻文件 |
| [网页实际使用的整包文件清单接口](https://datadryad.org/downloads/zip_assembly_info/148448) | HTTP 403，未得到可下载对象 URL；接口机制核查自[官方控制器](https://github.com/datadryad/dryad-app/blob/d5db49521fb48948506c21c54aa6238fd1cbe301/app/controllers/stash_engine/downloads_controller.rb) |
| 浏览器访问 | 本环境浏览器访问主机不可用；另以 web 工具独立请求原文件／整包接口，也均不可访问 |
| Zenodo、Figshare、作者代码归档 | DOI/题名检索未找到完整包副本；[Zenodo 5590645](https://zenodo.org/records/5590645)仅约 0.76 MB 的 h2metrics 代码，已在内存检查目录；[5584877](https://zenodo.org/records/5584877)是上一轮已有的示例代码／7图归档 |
| DataONE | 按题名及 seriesId 找到一个 `formatType=METADATA`、3387 字节记录，未找到本包的 DATA 对象；元数据中的下载地址回指 Dryad，**不是 746 MB ZIP 镜像**。可从[DataONE目录](https://cn.dataone.org/cn/v2/query/solr/?q=seriesId%3A%22https%3A%2F%2Fdoi.org%2F10.5061%2Fdryad.7h44j0zsj%22&wt=json&rows=100)核查，原始查询 URL 与结果数保存在本地记录 |
| Open University 仓储论文入口 | 本环境返回 403；其检索可见论文仍指向同一 Dryad 分享链接 |

停止条件：公开文件入口、整包接口均被拒，API 明确需认证，公开归档未发现完整副本。因此没有继续猜测私有对象 URL、注册账户或联系作者。**本轮没有完成完整包下载，也没有检查其 468 张原图、格式或包内说明文件。**

### 当前目录保留的 Mander 示例

为使当前交付可独立查看，从上一轮已下载的作者归档复用 **5 张含黄／橙黄区域的原始 JPEG**。对原来 7 张重看后，排除两张主要为深褐／红褐的图。它们不是本轮新取得的 Dryad 原包成员；不能把这次复用当成突破下载限制。

共同来源是 [Zenodo ZIP](https://zenodo.org/api/records/5584877/files/haibinhang/TDA-of-ginkgo-leaves-v1.0.0.zip/content) 的 `leaf_images/`；下表提供上一轮已核对相同字节的固定提交独立 URL。**示例归档许可只写 Other (Open)，未找到具体图像许可；未与完整 Dryad 包核对，故不直接套用 Dryad CC0。**

| 本地原图 | 独立来源 URL | 目视选择依据 |
|---|---|---|
| [photos/mander/B4GS4_8.jpg](photos/mander/B4GS4_8.jpg) | [原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B4GS4_8.jpg) | 橙黄褐，小叶，细脉 |
| [photos/mander/B5GS3_1.jpg](photos/mander/B5GS3_1.jpg) | [原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B5GS3_1.jpg) | 叶片下部黄，较多褐色与明暗不均 |
| [photos/mander/B5GS3_8.jpg](photos/mander/B5GS3_8.jpg) | [原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B5GS3_8.jpg) | 这组中较黄，放射纹与黄褐梯度 |
| [photos/mander/B7GS2_7.jpg](photos/mander/B7GS2_7.jpg) | [原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B7GS2_7.jpg) | 黄褐，小叶 |
| [photos/mander/B7GS2_9.jpg](photos/mander/B7GS2_9.jpg) | [原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B7GS2_9.jpg) | 黄褐，深裂片 |

拍法依据：[配套论文 §2](https://pmc.ncbi.nlm.nih.gov/articles/PMC8611351/)，叶片先在植物压制夹中干燥，然后在灯箱上方 20 cm 拍照；并非新鲜秋黄叶实验。已取得图像为 3264×2448、iPhone 5c、f/2.4、自动白平衡 JPEG，EXIF 标记 sRGB，无嵌入 ICC。背景亮度／色偏不同。**没有同场色卡、RAW、灯箱型号、实测 CCT/SPD、透射白暗参考或绝对亮度标定。** 论文说拍摄时有尺度，但这 5 张实图未见可读实体尺；论文另给原始图像 152 px/cm，只能作有条件尺度线索，不能逐图确认。72 dpi 不能用于实物定标。

说明与核验文件：

| 文件 | 来源与许可 | 信息／校准状态 |
|---|---|---|
| [photos/mander/photography_method_excerpt.xml](photos/mander/photography_method_excerpt.xml) | [Europe PMC 原文 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8611351/fullTextXML)，论文 CC BY 4.0；本次仅提取方法章节题名／段落，去掉表格 | 作者原文拍法；不是从受阻 ZIP 解出的说明文件，无色度标定 |
| [data/mander/metadata.json](data/mander/metadata.json) | [Dryad数据API](https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.7h44j0zsj)、[文件清单](https://datadryad.org/api/v2/versions/148448/files)、[Zenodo API](https://zenodo.org/api/records/5584877)；保留上一轮选存元数据，本轮重新核查文件接口 | 包名称／体积／发布哈希／方法／许可；无校准证书 |
| [data/mander/selected_images.json](data/mander/selected_images.json) | 本次本地计算与逐项原图 URL，照片许可边界同上 | 5图文件大小、SHA-256、复用说明 |
| [data/mander/previous_exif_selected.json](data/mander/previous_exif_selected.json) | 上一轮从这些原件提取的 EXIF，本轮仅保留所选5图 | 相机、曝光、WB、尺寸；不代表光源测量 |
| [data/mander/request_status.json](data/mander/request_status.json) | 本轮 URL／请求体／HTTP 状态或错误、镜像查询结果摘要，本地调查记录 | 可复查受阻与镜像查询；非原始实验数据，无校准意义 |

已逐张解码并查看所选原图，SHA-256 与上一轮记录一致，未调色、裁切或重新编码。未保存 ZIP、代码库、化石图或未选 Mander 图片。

## 2. 黄银杏透射光谱：有实测线索，尚无目标数值或明确曲线

### LOPEX_ZJU 确有衰老期银杏同叶 R/T 测量，但未找到开放原数值

原始研究：Yao Zhang 等，*PROSPECT-PMP+: Simultaneous Retrievals of Chlorophyll a and b, Carotenoids and Anthocyanins in the Leaf Optical Properties Model*，Sensors 22(8):3025 (2022)，[DOI / 作者论文](https://doi.org/10.3390/s22083025)，[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9028795/)。本轮通过 [Europe PMC 全文 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9028795/fullTextXML) 成功读取作者原文；出版社 PDF 下载返回403。

- 作者 §2 明确 LOPEX_ZJU 于 **2015年9–12月**在浙江大学校园采集，共12种植物、59片叶。**Table 2 的 Ginkgo 行为5片叶，生活阶段为 M、S（成熟、衰老），SPAD 范围3.8–41.8**。这是确实包含银杏衰老期、并实测同叶 R/T 的原始研究，比“所有数据都是夏季绿叶”更接近目标。
- §2.1 测向轴面 directional-hemispherical reflectance / transmittance（DHR/DHT）：Shimadzu **UV-3600 + 积分球**，仪器工作范围240–2400 nm，作者称光谱分辨率约1 nm、随波长而异。它是积分球测量，不能当成相机单方向透射亮度。论文模型主要评估400–800 nm。
- 校准说明明确：参考反射板校准和黑背景修正；§2.1 Eq.(1) 给出从原始仪器读数到校正 R/T 的方程。§2.2 同叶取圆片测 HPLC 色素和含水量。**未提供逐样本白暗参考数值、参考板校准证书、测量误差或灯光 SPD。**
- **尚不能把其中一条曲线标成“秋黄银杏”**：Table 2 没有逐片叶编号/颜色/日期；低 SPAD 和衰老阶段不能替代对应照片或作者的 yellow 标记。Figure 3 虽显示实测和模型 R/T，但仅以花青素浓度分组，未明确曲线对应物种，不能默认它是银杏。图里的 T 还以 `1 − DHT` 形式显示，不能直接当 T 读取。
- 数据可用性原文为 **“Not applicable.”**；本轮全文 XML 中无数据仓储/数值补充材料链接。论文 CC BY 4.0 不等于已经公开了这59片叶的原始数值文件。
- 已继续查其前身 [Zhang 等 Remote Sensing 2020,12:3615](https://doi.org/10.3390/rs12213615)，及 [2024年同团队升级研究](https://doi.org/10.3390/rs16111885)。2020论文 [原版PDF](https://mdpi-res.com/d_attachment/remotesensing/remotesensing-12-03615/article_deploy/remotesensing-12-03615.pdf) 可通过网页阅读：Fig.1 明确物种为 Tea tree、Decipiens、Sapindus、Sugar maple，不能拿来当银杏。2024研究说明升级库含400–2400nm R/T与荧光，但本轮没有找到可公开下载、带银杏样本身份的 R/T 数值附件。2015张垚博士论文题名来自2022论文参考文献，检索未取得公开全文/附表，不能算已验证数据。

#### 本轮保留的证据文件（不是目标光谱）

| 本地路径 | 来源 URL、许可 | 文件内容、测法及校准边界 |
|---|---|---|
| `data/spectra_new/prospect_pmp_2022_methods_and_samples.xml` | [Europe PMC 原始全文 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9028795/fullTextXML)；论文 **CC BY 4.0**，作者 Yao Zhang 等 | 本次从原文选择 §2（含Table 2、§2.1和§2.2）、许可、数据可用性及Fig.3图注，外加来源标记。是**选择性派生证据XML**，并非完整原件；作者联系方式字段未纳入。可本地核对银杏5片、M/S、SPAD范围及校正方程；无原始测量数值。 |
| `data/spectra_new/ecosis_search_checks.json` | [EcoSIS CKAN API](https://data.ecosis.org/api/3/action/package_search)；本次生成的检索记录，源元数据未见统一许可 | 记录实际 `ginkgo`、`senescent`、`autumn`、`transmittance` 检索命中数；无光谱、无校准。属于元数据检索，不能证明每个资源内部都没有银杏。 |
| `data/spectra_new/manifest.json` | 本地计算；本次生成 | 以上2文件的字节数和SHA-256；完整性记录，非校准数据。 |

XML 已本地解析验证：有完整样本表、Ginkgo行、方法、许可与数据可用性。没有把占位文档/拒绝页当PDF保存。

### Matile, Flach & Eller 1992：本轮仍未获得全文和曲线图

[论文 DOI](https://doi.org/10.1111/j.1438-8677.1992.tb00261.x)，*Autumn Leaves of Ginkgo biloba L.: Optical Properties, Pigments and Optical Brighteners*，Botanica Acta 105:13–17。只获得文献记录/摘要，不能据此宣称已看过其透射光谱图。

本轮新增尝试而非重复出版社微调：

- [Zürich ZORA 官方检索](https://www.zora.uzh.ch/cgi/search/simple?q=Autumn+Leaves+Ginkgo&_action_search=Search&_order=bytitle&basic_srchtype=ALL&_satisfyall=ALL) 返回HTTP200，但页面实际为 anti-bot challenge，未获得搜索结果或文章；没有把200当下载成功。
- E-Periodica 的 [Botanica Helvetica卷目录](https://www.e-periodica.ch/digbib/volumes?UID=bot-002) 和1994卷 Matile 检索均403。它更可能对应 Matile 1994 *Fluorescent idioblasts...*，并非直接证实有1992 Botanica Acta 存档。没有取得1994全文，更没有据其题名推测T。
- 对 ZORA、ETH Research Collection、E-Periodica、SERVAL 做题名/作者检索，没有发现能下载目标1992全文的命中；SERVAL 网页入口受 robots 限制。这是本轮检索结果，不是断言这些机构绝无收藏。
- [Crossref DOI 元数据](https://api.crossref.org/works/10.1111/j.1438-8677.1992.tb00261.x) 只给 Wiley 版与文本挖掘入口；[OpenAlex DOI记录](https://api.openalex.org/works/https://doi.org/10.1111/j.1438-8677.1992.tb00261.x) 只有非开放的 DOI 位置，无 PDF URL。无可信公开镜像落点，故不继续盲改下载参数。

**许可和方法：** 没有取得全文开放许可、仪器/校准细节或图轴，不能推断。未保存无用拒绝页面或不完整PDF。未联系作者。

### EcoSIS 与相似研究排除

- [EcoSIS API 的 ginkgo 元数据检索](https://data.ecosis.org/api/3/action/package_search?q=ginkgo&rows=100) 本轮返回0；transmittance返回13条候选。秋季候选 [Spectra from in situ deciduous leaves...](https://data.ecosis.org/dataset/4c069827-5596-4ba7-9a60-157335b859b2) 元数据列 Fagus grandifolia、Betula lenta、Liriodendron tulipifera，没有银杏；且说明为leaf clip光谱，未给目标黄银杏T。没有为凑数重复下载前轮 Noda 或 Morimoto。
- [Xu & Ye 2023，Scientific Reports](https://www.nature.com/articles/s41598-023-31718-1) Fig.3b 确有银杏实测 R/T 曲线及测法（DUV-3700积分球，BaSO4反射参考、空气透射参考）；**Sample collection 明确2020年7月12–19日采成熟夏叶**，不满足秋黄。已实际查看Fig.3：3a只有其他4种绿叶照片，无银杏照片；不能凭银杏曲线高于别的植物断言它发黄。未把此绿叶图留作增量交付。
- [Merzlyak等2004](https://www.sciencedirect.com/science/article/pii/S1011134404000387) 的银杏材料说明为2002年4–5月采样，亦不能算秋黄银杏；近红外估算方法不是黄色样本真值。


## 3. 有校准线索的透射测量与空间成像

### 3.1 HyperART：空间透射论文图，没有原始立方体

[Bergsträsser et al. 2015 原文](https://link.springer.com/article/10.1186/s13007-015-0043-0)，DOI10.1186/s13007-015-0043-0。期刊声明CC BY4.0；数据声明CC0不应扩展成整个论文图的许可。

| 本地路径 | 来源URL | 文件性质与校准 |
|---|---|---|
| [`data/hyperart/13007_2015_43_Fig4_HTML.png`](data/hyperart/13007_2015_43_Fig4_HTML.png) | [出版社图4原件](https://media.springernature.com/full/springer-static/image/art%3A10.1186%2Fs13007-015-0043-0/MediaObjects/13007_2015_43_Fig4_HTML.gif) | 原响应实际为PNG，575×991，258,485字节，只按真实格式改后缀，未重编码。CC BY4.0。病斑甜菜的R/T/R+T合成RGB、CLSI及分类误差图；已目视检查。**不是原始照片或可反推T的cube**。CLSI色标−1.7至−0.2为指数，不是透射率。无可用毫米尺。 |
| [`data/hyperart/Bergstrasser_2015_HyperART.pdf`](data/hyperart/Bergstrasser_2015_HyperART.pdf) | [出版社原PDF](https://link.springer.com/content/pdf/10.1186/s13007-015-0043-0.pdf) | 2,361,709字节，CC BY4.0，完整测法/仪器/校正与图2 R/T坐标轴。不是原超立方体。 |

方法要点：整叶夹平、镜面分路，用同一线扫描相机记录R和T；VNIR400–1000nm和SWIR1000–2500nm。图4所用第一原型有OMNILUX卤素光源、Spectralon99%白参考及暗帧，逐像素除白参考并乘厂家修正因子。所得甜菜为病变绿/红叶，非秋黄银杏。原全文只有一份补充相关性图，没有找到公开的数值超立方体或逐像素校准文件；这幅合成RGB不能充当色度真值。

### 3.2 MapS-Wear：八通道归一化表，不能定绝对亮度

来源：[Jiang et al. 2025论文DOI](https://doi.org/10.1126/sciadv.adw7279)，[作者团队提供的PDF](https://www.softintel.top/papers/2025/jq_SA.pdf)，[Zenodo15192884](https://zenodo.org/records/15192884)。Zenodo归档标题`qin-star/HUST-Plant-Wearable-Sensor: New MapS-Wear`，数据许可CC BY4.0；论文PDF页首明确 **CC BY-NC4.0**，不可混淆。

**关键纠正：** 光谱分类五类是健康、N/K/P缺素、螨害；热/旱/衰老是另一个温湿度诊断模块，不能把它们当作此表分类。正文说N缺素叶黄化、K缺素边缘黄化，但没有逐行叶色/照片匹配表，不能保证每条N记录对应已完全变黄的叶。

**不能当绝对T：** 原PDF第9页公式是每个传感器分别`Ts(i)=Ii/Ienv, i=1,2`，随后每个八通道向量再除以其八通道之和。通道中心415/445/480/515/550/590/630/680nm。XLSX没有Ienv、原始辐射幅值或明确的处理阶段说明；通道和接近1也支持其为归一化特征。因总幅值已丢失，**不能从此表恢复背光亮度，也不能将通道值误作绝对单色透射率**。两个传感器测中心/边缘，不构成空间像素图。

光源与测法有用：Mijia1S台灯，正文写4500lux、5000K、叶上方约30cm，遮光罩；AS7341八可见通道，两个贴叶传感器与环境传感器记录Ii/Ienv。未取得逐样本灯光SPD、暗参考、通道响应修正和未归一化信号。

| 本地路径 | 独立来源/归档成员 | 许可与用途 |
|---|---|---|
| [`data/maps_wear/Spectral data.xlsx`](<data/maps_wear/Spectral data.xlsx>) | [Zenodo原ZIP](https://zenodo.org/api/records/15192884/files/qin-star/HUST-Plant-Wearable-Sensor-MapS-Wear.zip/content)，成员`qin-star-HUST-Plant-Wearable-Sensor-3a6e60f/spectral data/Spectral data.xlsx` | CC BY4.0，280,761字节，原字节选择下载。Transmittance表前3行为标题，第4–1371行共1368数据行、两传感器各8列，=2736向量；与正文2742序列相差6，本次不补齐。 |
| [`data/maps_wear/github_Weight_tree_RF.ipynb`](data/maps_wear/github_Weight_tree_RF.ipynb) | 同ZIP，成员`qin-star-HUST-Plant-Wearable-Sensor-3a6e60f/original Code/SDM model&code/github_Weight_tree_RF.ipynb` | CC BY4.0，6,584字节，仅静态读代码，未执行。模型直接读16特征，不提供原辐射/光源表。 |
| [`data/maps_wear/MapS_Wear_2025_author_copy.pdf`](data/maps_wear/MapS_Wear_2025_author_copy.pdf) | [作者PDF](https://www.softintel.top/papers/2025/jq_SA.pdf) | CC BY-NC4.0，1,419,293字节；第3页N/K叶色依据，第9页灯光/比值/归一化公式已渲染目视核查。 |
| [`data/maps_wear/source_metadata.json`](data/maps_wear/source_metadata.json) | [Zenodo API](https://zenodo.org/api/records/15192884) | CC BY4.0原记录选存，含归档许可/链接/文件MD5。原完整ZIP655,126,200字节、发布MD5`b6ebf0d381d86c1a327b704780b9e438`，仅HTTP Range选择读取，没有完整下载故**未验证全ZIP的MD5**。 |
| [`data/maps_wear/manifest.json`](data/maps_wear/manifest.json) | 上述原ZIP与本地计算 | 本次整理；原成员路径、CRC、SHA256。选择成员的ZIP CRC均验证一致。 |
| [`data/maps_wear/validation.json`](data/maps_wear/validation.json) | XLSX本地解析 | 本次整理；标签数health398/K283/N374/P108/white205；21888数值全部有限，范围0.01688318–0.28832897；传感器八通道和范围分别0.951726–1.048064、0.958536–1.06543。未做裁零/归一化/调数。 |

四幅试取图(K_1、N_1、N_94、P1)已目视，都是白底叶片/抠图，无色卡、不支持背光且无法与表匹配，所以未收进交付。全部未选照片与完整ZIP均不在交付目录。


## 4. 新鲜黄银杏高清外观参考

### 4.1 新增2024年在枝单片黄叶照片

- 本地：[`photos/supplementary/ginkgo_yellow_attached_DSM4694_2024.jpg`](photos/supplementary/ginkgo_yellow_attached_DSM4694_2024.jpg)，2000×3000，3,473,325字节。[作者来源页](https://commons.wikimedia.org/wiki/File:2024-10-24_-_vivid_yellow_ginkgo_leaf_on_distant_twig_against_a_blue_sky_-_DSM4694.jpg)；[原图](https://upload.wikimedia.org/wikipedia/commons/6/69/2024-10-24_-_vivid_yellow_ginkgo_leaf_on_distant_twig_against_a_blue_sky_-_DSM4694.jpg)。作者 Franz van Duns，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。SHA-1与Commons记录一致，原字节未改色/裁切。
- 拍法：2024-10-24 Dortmund，叶仍连在树上；Fujifilm GFX100S，350mm，ISO800、1/640s、f/11、相机WB7000K。源记录说保存JPEG+RAF，但仅JPEG公开，未取得RAF。Lightroom曝光+0.28、Texture+50、Vibrance+10等；Photoshop蓝色饱和度+45、旋转和裁切。
- 校准：无同场色卡、裸光源SPD、灰/白透射参考或曝光标定；7000K是WB设置，不是实测光源。实际文件嵌入 **ProPhoto RGB**，不要按sRGB解释RGB数值。
- 实图核查：单叶放射细条纹、褐色小斑、细脉、局部深边清楚，另有卷曲叶及阴影。来源确认在枝，支持新鲜；图像视觉支持存在透射光分量，但作者未明确写纯背光，**不能称纯透射测量**。
- 比例：没有实体尺或叶宽记录，无法定毫米尺度；240dpi不能作为实物比例。

### 4.2 复用2021年明确阳光透射照片

- 本地：[`photos/fresh_ginkgo/ginkgo_yellow_sun_transmission_Franz_van_Duns_2021.jpg`](photos/fresh_ginkgo/ginkgo_yellow_sun_transmission_Franz_van_Duns_2021.jpg)，3028×3028；逐字节复制自上一轮同名文件，并再次打开检查；SHA-1仍为`c5c1aff1101d647c75080fb5eeccaeccc9f86999`，匹配Commons。
- [作者说明](https://commons.wikimedia.org/wiki/File:DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)；[原图](https://upload.wikimedia.org/wikipedia/commons/5/52/DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)，Franz van Duns，[CC BY-SA4.0](https://creativecommons.org/licenses/by-sa/4.0/)。**这是旧成果复用，不是本次新发现。**
- 拍法：2021-10-22在枝黄叶，作者明确称秋日阳光透射；Sony A7R IV、400mm、1/2000s、f/7.1、ISO800，WB5600K。经过Lightroom/Photoshop对比度、色彩、细节调整；实际ICC为sRGB。
- 无色卡/白暗参考/光源SPD，无公开ARW，不能取颜色/亮度为真值。实图可见细脉、放射条纹、重叠叶影；作者称最上叶宽约80mm，可粗估尺度，因倾斜/弯曲且无同平面尺，不能精确定标。


## 5. 仍未取得的空间透射数据与 RAW 候选

- [LeafVAE2026原PDF](https://research.fs.usda.gov/download/treesearch/80751.pdf)，DOI10.1016/j.compag.2026.111971。第10页Data availability明确“Data will be made available on request.” 有校正叶片透射高光谱/山毛榉多光谱，未找到公开原数据，未联系作者。
- [Thomas et al.2022作者机构PDF](https://phenorob.com/wp-content/uploads/2024/08/Thomas_2022_JPlDisProtect_129_505.pdf)，DOI10.1007/s41348-022-00570-2：大麦病叶R/T空间成像，但Data availability明确因体量大未公开数据。未当作可下载cube。
- [Pixls MotorolaG7 DNG作者帖](https://discuss.pixls.us/t/motorola-g7-150-200-dollar-phone/21192)：公开24MB DNG、CC BY-SA4.0且作者明说背光。实际打开OOC图发现是**绿叶**，非黄叶，未下载RAW作为目标成果。
- [Pixls Backlit fall leaves作者帖](https://discuss.pixls.us/t/backlit-fall-leaves/61669)：知道Smallrig flexlight背侧光，但无完整型号、色温、色卡、RAW；作者已做对比度/色彩处理，不构成校准。未下载凑数。
- [Franz2019灯箱黄银杏](https://commons.wikimedia.org/wiki/File:Ginkgo_biloba_leaves_in_radial_arrangement_-_2019-10-25_focus_stack.jpg)：9504×6336，作者明确well-dried/pigments faded并增强黄色，灯箱无型号，未作为新鲜真值下载。

辅助索引：[`data/image_sources_manifest.json`](data/image_sources_manifest.json)逐项给本次两幅照片与HyperART图/PDF的来源、许可、字节数、SHA-1/SHA-256；本次整理文件本身不是校准证书。

## 6. 本地验证与交付边界

- `photos/mander/` 仅5张选定原JPEG及1份原文方法摘录；没有把完整包未下载说成已筛完468片叶。所选JPEG全部解码、目视检查并与上一轮SHA-256核对，无调色／重编码。
- 新增2024图与复用2021图已实际打开，Commons SHA-1匹配；来源ICC分别为ProPhoto RGB与sRGB，不能无视色彩空间直接比较RGB。无可用于绝对色度／亮度标定的照片。
- HyperART图4已实际查看，它的指数色标不是T；PDF、论文图与原始高光谱数值严格区分。未取得可导出逐像素T的立方体。
- MapS-Wear工作簿已解析：1368行、16特征列、21888个有限数；两个传感器共2736向量；归一化限制、标签原文及与论文样本数的差异保留，不补数、不反推幅值。抽取的ZIP成员CRC已核对，未宣称校验完整归档MD5。
- LOPEX_ZJU证据XML已解析，有银杏样本行和测量校正方法，但它没有逐样本目标光谱。Matile1992仍未取得全文或可数字化图。

除索引自身外，全体交付文件的本地字节数和SHA-256见 [`data/file_checksums.json`](data/file_checksums.json)，这是本次生成的完整性索引，不是实验校准文件；来源、许可与适用范围按本文对应条目。原有 `brief.md`、`log.txt` 未修改；上一轮目录未修改。当前交付目录没有完整ZIP、未选Mander图或无关候选照片。

**尚缺的最终真值明确未找到：新鲜秋黄银杏可见光透射T(λ)／同叶R/T、具色度与亮度校准的背光照片，以及黄银杏空间分辨的数值透射图。** 本轮提供的新增线索和替代材料不能消除这些物种、状态、几何和校准缺口。
