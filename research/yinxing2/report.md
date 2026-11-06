# 黄银杏叶背光颜色参考：下载与校准核查

核查/下载日期：2026-11-02。

## 交付结论

**没有找到可直接当作“新鲜秋黄银杏叶透射颜色真值”的校准照片，也没有取得黄色银杏同一样本的成对 R/T 数值光谱。** 已交付可用的替代测量和外观原图，缺口没有用普通照片取色或不同叶片的光谱拼配来填补。

| 材料 | 已保存 | 适合用途 | 关键限制 |
|---|---|---|---|
| Noda / JaLTER 衰老黄叶 R/T | 20个原始CSV，5物种，350–2500nm；另有350–750nm整理表 | 当前最可靠的黄叶透射物性替代参考，优先桦木/栎树LICOR数据 | 没有银杏；有测法/仪器校准说明，无逐样本校准证书和裸光源数据 |
| Morimoto 日本自然物光谱 | 3原始CSV、2原始XLSX及选样表 | 黄色山药叶成对R/T，已知透射灯箱型号及光源比值测法 | 黄银杏只有R；有T的银杏是夏季绿叶，不能混配 |
| Mander 同项目作者示例 | `photos/mander/` 7张3264×2448 JPEG原字节 | 黄/黄褐干叶的叶脉、形状及不均匀性 | **Dryad完整包下载受阻；这7张来自作者的Zenodo归档镜像，未与Dryad包逐字节核对**；干压叶、无颜色校准 |
| 新鲜在枝/扫描银杏补充 | 3张公开JPEG原图 | 透射外观、叶肉斑点、放射条纹、局部褐边 | 无校准颜色真值；扫描新鲜性/透射模式未证实 |

推荐将黄叶实测 **T(λ)** 用作定量范围，将新鲜黄银杏照片用于空间纹理。比较颜色时明确光源 SPD、叶面朝向、观察几何和显示变换；积分球总透射率与有限视场方向测量不是同一个量。这里的其他物种数据不能冒充黄银杏真值。



## 1. 首要目标：Mander, Hang, Bauer & Mio (2021)

### 下载状态、来源与许可

[Dryad 数据集](https://doi.org/10.5061/dryad.7h44j0zsj) 的原始 API 清单仅列 `Supplementary_Information.zip`，**745,843,529字节**，发布SHA-256为 `125e541c2aec474138f14bc879e3575639da59307fd9217354d58f75a801c9a2`，数据许可 **CC0 1.0**。公开[网页下载](https://datadryad.org/downloads/file_stream/1145562)返回HTTP 403；[API下载](https://datadryad.org/api/v2/files/1145562/download)返回401，官方[API账户文档](https://github.com/datadryad/dryad-app/blob/main/documentation/apis/api_accounts.md)说明文件下载需要令牌。本环境的浏览器访问主机也不可用。因此**没有成功下载或解开这份完整Dryad ZIP，不能声称查完包中468张现生叶照片，也不能断言包内无RAW/无黄叶**。

替代取得了配套论文明确链接的作者代码库[Zenodo归档5584877](https://zenodo.org/records/5584877)，[ZIP原件](https://zenodo.org/api/records/5584877/files/haibinhang/TDA-of-ginkgo-leaves-v1.0.0.zip/content)约9.66MB。只提取归档中 `leaf_images/` 目录的7张JPEG，保留原字节，未调色/裁切。它们与作者[GitHub固定提交](https://github.com/haibinhang/TDA-of-ginkgo-leaves/tree/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images)的7个Git blob全部一致。原完整ZIP、临时仓库与未选文件均不在交付目录。

**许可边界：** Dryad原数据明确CC0；作者这个Zenodo代码/示例归档只标 `Other (Open)`，仓库没有另附具体许可。它们确属同项目作者发布示例，但本次不能用完整Dryad包校验确认其CC0对应关系。故下面7张的许可记录为“Dryad数据CC0；镜像自身具体许可未明确”，不要把整个代码镜像也说成CC0。

### 已证实的拍法与校准缺口

- [配套论文 §2](https://pmc.ncbi.nlm.nih.gov/articles/PMC8611351/)和Dryad方法描述：英国Open University一株银杏，468片成熟展开叶，**先用植物压制夹干燥**；相机在灯箱上方20cm，叶片旁放比例尺。没有说明采收月份或秋季自然衰老阶段。照片呈黄褐色不能据此证明是新鲜秋黄叶。
- 已取7图实测EXIF：Apple **iPhone 5c**，后置4.12mm f/2.4，JPEG，3264×2448；自动白平衡（WhiteBalance=0），ColorSpace=1（sRGB标记），无嵌入ICC。拍摄时间标签为2017-12-13；它是照片时间，**不是采叶日期证明**。ISO/曝光见下表。只对这7张实测，不外推完整包相机/格式。
- **未找到灯箱品牌/型号、实测色温或SPD、照度、色卡、透射白参考/暗参考、相机响应标定、RAW。** 最后这项仅指已经取得的示例，没有检查完整包。
- 7张实图可见白/灰背景与手写标签，**均未见可读实体尺或色卡**。背景有明显明暗和色偏，纸标签不是已校准的白参考。论文另给原始影像 **152 px/cm**、分析图下采样1/8后的19 px/cm；这可作有条件尺度线索，但没有图内尺逐张复核，不能宣称每张已完成毫米标定。EXIF 72dpi不是实物比例。

### 保留的7张原图

本表各项共同采用上述拍法与校准限制。每项均可从上面的Zenodo ZIP按同名成员取得；逐项链接同时指向已核对字节一致的作者固定提交文件。目视颜色用于筛选，不是色度测量。

| 本地文件 | 独立来源URL | 目视外观 | 曝光/ISO |
|---|---|---|---|
| [`photos/mander/B1GS2_8.jpg`](photos/mander/B1GS2_8.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B1GS2_8.jpg) | 黄褐，较深色，裂片明显 | 1/50s / 50 |
| [`photos/mander/B4GS4_8.jpg`](photos/mander/B4GS4_8.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B4GS4_8.jpg) | 橙黄褐，细脉可见 | 1/100s / 80 |
| [`photos/mander/B5GS3_1.jpg`](photos/mander/B5GS3_1.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B5GS3_1.jpg) | 黄褐，叶肉明暗/色斑明显 | 1/25s / 50 |
| [`photos/mander/B5GS3_5.jpg`](photos/mander/B5GS3_5.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B5GS3_5.jpg) | 橙褐为主，少量浅色区 | 1/50s / 64 |
| [`photos/mander/B5GS3_8.jpg`](photos/mander/B5GS3_8.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B5GS3_8.jpg) | 较黄，放射条纹和褐色渐变 | 1/33s / 50 |
| [`photos/mander/B7GS2_7.jpg`](photos/mander/B7GS2_7.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B7GS2_7.jpg) | 黄色到褐色渐变 | 1/50s / 50 |
| [`photos/mander/B7GS2_9.jpg`](photos/mander/B7GS2_9.jpg) | [作者原件](https://raw.githubusercontent.com/haibinhang/TDA-of-ginkgo-leaves/cffb417b353cb5774e5eb21c16847b5f3c284b10/leaf_images/B7GS2_9.jpg) | 黄褐，深裂片 | 1/50s / 50 |

### Mander 支持文件

| 路径 | 来源URL / 许可 | 内容、拍法/校准信息 |
|---|---|---|
| [`data/mander/dataset_metadata.json`](data/mander/dataset_metadata.json) | [Dryad API](https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.7h44j0zsj)；数据声明CC0 | 原始API响应去掉作者联系字段，保存方法/许可；不是校准证书。 |
| [`data/mander/file_manifest.json`](data/mander/file_manifest.json) | [Dryad文件API](https://datadryad.org/api/v2/versions/148448/files)；同数据集 | ZIP名称、字节数、发布SHA-256；未下载ZIP，不能说已校验其完整性。 |
| [`data/mander/mirror_metadata.json`](data/mander/mirror_metadata.json) | [Zenodo API](https://zenodo.org/api/records/5584877)；归档标Other Open | 镜像来源、下载URL、许可原文与记录信息；选存相关字段。 |
| [`data/mander/exif_selected.json`](data/mander/exif_selected.json) | 上述7图的EXIF/本地SHA-256 | 本次提取的相机、曝光、白平衡、时间、尺寸等；不是作者提供的校准数据。许可随对应图像限制。 |
| [`data/mander/download_status.json`](data/mander/download_status.json) | 上述Dryad网页/API与本次操作记录 | 403/401阻碍、镜像替代范围、未核验事项；本次整理说明。 |

## 2. 黄/衰老叶的成对反射与透射光谱

### 结论与建议

已实际取得 Noda 等（2014）的 20 个原始黄/衰老叶光谱 CSV，来自 5 个物种。每个文件都同时包含同一样本向轴面和背轴面各自的反射率 R、透射率 T。原始附录对全部 20 项明确标为衰老黄叶，因而不是凭低叶绿素或颜色曲线猜测。**没有银杏**。用于黄银杏材质的替代参考时，优先看阔叶的 **Betula ermanii（岳桦）和 Quercus crispula（水楢）**，特别是 `LICOR` 数据；可以约束黄叶可见区光谱的一般范围，不能当作黄银杏的精确真值。[数据论文 DOI](https://doi.org/10.1007/s11284-013-1096-z)，[原始测法](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/metadata/)，[逐样本附录](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/appendix.csv/at_download/file)。

20份文件含同编号叶片的不同积分球测量，按物种、日期、叶编号去重为15个组合，不能当成20个独立叶片。

数据版权以 2025-07-05 迁移后当前记录中的明确声明为据：**CC BY 4.0**。此声明已保存在本地 `noda2014/metadata.xml` 的 `intellectualRights` 中；作者署名见文末。[当前记录](https://jalter.diasjp.net/view/urn%3Auuid%3A103510db-c32a-4dec-b1e3-502cba05e7c2)。完整 ZIP 约 8.1 MB，仅临时下载并选择解出 20 个黄叶 CSV；整包与绿色样本均已删除。

### 测法、单位、校准与用途

- 文件第 3 行为 `#wl,R(adaxial),T(adaxial),R(abaxial),T(abaxial)`。首列是 nm，其余为无量纲比例，0.5 表示 50%，不应再除 100。向轴面、背轴面描述照明/测量所对的叶面；不是颜色空间通道。
- 原始光谱为 350–2500 nm，每 1 nm 一个采样值；**采样间隔不等于仪器光谱分辨率**。R/T 是积分球测得的叶片光学比率，适合计算给定照明 SPD 下的透射色。它不是相机 RGB，也不包含透射光的完整角分布，不能单独定义双向透射分布函数。
- 每个保留样本使用 FieldSpec FR 光谱辐射计。`LICOR` 是 LI-COR LI-1800-12 积分球，`ASDIS` 是 ASD RTS-3ZC 积分球。附录将阔叶列为 B-1 测法；落叶松针叶与芒草窄叶列为 B-2，涉及窄叶/针叶的端口填充处理。叶片采下数小时内在实验室测量，因而是新鲜采集的衰老黄叶，不是烘干材料。
- 原始测法说明 FieldSpec FR / FieldSpec 3 **每年校准**，积分球内表面/白参考涉及 BaSO4 / PTFE；引用了 Noda 等（2013）的标准测法。**未找到每个黄叶测量文件的独立白/暗参考读数、光源 SPD、色温、校准证书或测量不确定度**。因此可称有仪器与测法校准信息的光谱，不能声称有逐样本可追溯的绝对标定文件。[测法与仪器说明](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/metadata/)。
- 原作者指出 RTS-3ZC 的近红外 R+T 有时超过 1，故 `ASDIS` 与 `LICOR` 的同一样本不应无区别合并。LI-1800 在 1650–1740、1890–1950、2050–2500 nm 使用 `-9.999` 表示不可用数据；不能把这个占位值当物性。
- 这里的 R/T 没有给光源颜色或曝光；比渲染时，必须给真实或约定的光源 SPD 和观察者函数，计算 `SPD × T(λ)` 后再积分为 XYZ/RGB。透射率本身不是背光像素亮度；也不能把 R 颜色直接用作透射色。若材质不模拟荧光，这组普通 R/T 仍不等于对银杏荧光贡献的校准。

### 原始文件清单

下表每项许可均为 **CC BY 4.0**，拍法/测法、校准信息同上。每项来源均为[原始 ZIP 下载 URL](https://jalter.diasjp.net/metacat/d1/mn/v2/object/urn%3Auuid%3Af8bfce94-e567-4002-a966-44c4cc070d51)，成员路径前缀为 `ERDP-2013-02/`；本地 CSV **逐字节保留原始内容**，未裁剪、平滑、归一化或钳位。表内物种/衰老状态、B-1/B-2 测法来自附录；每项的完整 URL、归档成员路径、字节数和 SHA-256 另列于 `manifest.json`。

| 本地文件 | 物种 | 测量日 | 仪器/测法 | 黄/衰老证据 |
|---|---|---|---|---|
| [`Betula_leaf_yellow_2010_1006_1_ASDIS.csv`](data/spectra/noda2014/Betula_leaf_yellow_2010_1006_1_ASDIS.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Betula_leaf_yellow_2010_1006_1_LICOR.csv`](data/spectra/noda2014/Betula_leaf_yellow_2010_1006_1_LICOR.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Betula_leaf_yellow_2010_1006_2_LICOR.csv`](data/spectra/noda2014/Betula_leaf_yellow_2010_1006_2_LICOR.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Betula_leaf_yellow_2010_1006_3_LICOR.csv`](data/spectra/noda2014/Betula_leaf_yellow_2010_1006_3_LICOR.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_1_LICOR.csv`](data/spectra/noda2014/Larix_leaf_yellow_2011_1030_1_LICOR.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_2_ASDIS.csv`](data/spectra/noda2014/Larix_leaf_yellow_2011_1030_2_ASDIS.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + ASDIS / B-2 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_2_LICOR.csv`](data/spectra/noda2014/Larix_leaf_yellow_2011_1030_2_LICOR.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_3_LICOR.csv`](data/spectra/noda2014/Larix_leaf_yellow_2011_1030_3_LICOR.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Miscanthus_leaf_yellow_2010_1102_1_LICOR.csv`](data/spectra/noda2014/Miscanthus_leaf_yellow_2010_1102_1_LICOR.csv) | Miscanthus sinensis Andersson | 2010-11-02 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Miscanthus_leaf_yellow_2010_1102_2_LICOR.csv`](data/spectra/noda2014/Miscanthus_leaf_yellow_2010_1102_2_LICOR.csv) | Miscanthus sinensis Andersson | 2010-11-02 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Miscanthus_leaf_yellow_2010_1102_3_LICOR.csv`](data/spectra/noda2014/Miscanthus_leaf_yellow_2010_1102_3_LICOR.csv) | Miscanthus sinensis Andersson | 2010-11-02 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Pleioblastus_leaf_yellow_2013_0109_1_LICOR.csv`](data/spectra/noda2014/Pleioblastus_leaf_yellow_2013_0109_1_LICOR.csv) | Pleioblastus chino (Franch. et Sav.) Makino | 2013-01-09 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Pleioblastus_leaf_yellow_2013_0109_2_LICOR.csv`](data/spectra/noda2014/Pleioblastus_leaf_yellow_2013_0109_2_LICOR.csv) | Pleioblastus chino (Franch. et Sav.) Makino | 2013-01-09 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Pleioblastus_leaf_yellow_2013_0109_3_LICOR.csv`](data/spectra/noda2014/Pleioblastus_leaf_yellow_2013_0109_3_LICOR.csv) | Pleioblastus chino (Franch. et Sav.) Makino | 2013-01-09 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_1_ASDIS.csv`](data/spectra/noda2014/Quercus_leaf_yellow_2010_1007_1_ASDIS.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_1_LICOR.csv`](data/spectra/noda2014/Quercus_leaf_yellow_2010_1007_1_LICOR.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_2_ASDIS.csv`](data/spectra/noda2014/Quercus_leaf_yellow_2010_1007_2_ASDIS.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_2_LICOR.csv`](data/spectra/noda2014/Quercus_leaf_yellow_2010_1007_2_LICOR.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_3_ASDIS.csv`](data/spectra/noda2014/Quercus_leaf_yellow_2010_1007_3_ASDIS.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_3_LICOR.csv`](data/spectra/noda2014/Quercus_leaf_yellow_2010_1007_3_LICOR.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |

### 元数据与派生文件逐项清单

| 本地文件 | 来源 URL / 许可 | 内容、校准与处理 |
|---|---|---|
| [`noda2014/metadata.xml`](data/spectra/noda2014/metadata.xml) | [当前 JaLTER 原始 EML](https://jalter.diasjp.net/metacat/d1/mn/v2/object/urn%3Auuid%3A103510db-c32a-4dec-b1e3-502cba05e7c2)；文件声明 CC BY 4.0 | 2025 年迁移记录，含作者、数据集介绍、版权、原始附件定义。保留原文。不是校准证书。 |
| [`noda2014/appendix.csv`](data/spectra/noda2014/appendix.csv) | [原始附录](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/appendix.csv/at_download/file)；归属于同一 CC BY 4.0 数据集 | 全部样本的物种、叶类型、仪器与测法索引。其 `File_name` 用 `.txt` 后缀，而 ZIP 实物为 `.csv`；按同名主干匹配，未改原附录。 |
| [`yellow_leaf_RT_350_750nm.csv`](data/spectra/yellow_leaf_RT_350_750nm.csv) | [同上 ZIP](https://jalter.diasjp.net/metacat/d1/mn/v2/object/urn%3Auuid%3Af8bfce94-e567-4002-a966-44c4cc070d51)；CC BY 4.0，派生整理 | 20 文件 × 401 波长 = 8020 行。统一列名并补源文件名与物种；仅裁取 350–750 nm，**保留所有原始数值**。有 `has_negative` 和 `R_plus_T_exceeds_1` 标志。 |
| [`validation.csv`](data/spectra/validation.csv) | 同上原始 CSV 的本地计算；CC BY 4.0 派生 | 逐文件记录完整点数、350–750 nm 极值、R+T 最大值、负值个数及波长范围。用于识别噪声，不是作者提供的误差估计。 |
| [`manifest.json`](data/spectra/manifest.json) | 原始 ZIP、[附录](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/appendix.csv/at_download/file)与本地校验；CC BY 4.0 派生 | 每一原始光谱的独立文件路径、来源 URL、ZIP 成员路径、许可、SHA-256、样本元数据。 |
| [`notes.md`](data/spectra/notes.md) | 本次研究记录；来源逐处标注 | 中文使用说明；非原始研究数据。 |

### 实际验证结果与限制

20 个原始 CSV 均成功解码/解析为 2151 个连续整数波长点（350–2500 nm）。350–750 nm 各有 401 点，无缺点、无 `-9.999` 占位值。此范围内所有样本、两面均 **R+T≤1**，所有文件中的最大值为 0.97384。Betula、Quercus、Pleioblastus 的四个 R/T 通道均非负。Larix 的 4 个文件与 Miscanthus 的 2 个文件在短波边缘出现负值，最坏为 Larix 的 ASDIS 样本 -0.0615091，负值最长延伸至 422 nm；说明该部分测量噪声/基线误差不可忽略。没有偷偷裁零或按光谱外形筛除不合意曲线。详细波长与数量见 `validation.csv`；优先使用桦木和栎树的 LICOR 曲线，并保留样本间差异。

这里只验证数据结构与基本物理范围，没有重新验证仪器校准，也没有把曲线数字化自论文图片。没有叶片对应照片、空间纹理或比例尺。

### 未取得的目标与检索记录

1. **黄银杏成对 R/T 数值光谱：本次未找到可公开直接下载的原始测量数据。** Noda 数据物种清单中没有银杏。
2. **Matile, Flach & Eller (1992) 全文：未下载成功。** 正确题名为 *Autumn Leaves of Ginkgo biloba L.: Optical Properties, Pigments and Optical Brighteners*，*Botanica Acta* 105(1):13–17，[DOI](https://doi.org/10.1111/j.1438-8677.1992.tb00261.x)。核查了[出版社正文入口](https://onlinelibrary.wiley.com/doi/10.1111/j.1438-8677.1992.tb00261.x)、[出版社 PDF 入口](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1438-8677.1992.tb00261.x)、[Crossref DOI 记录](https://api.crossref.org/works/10.1111/j.1438-8677.1992.tb00261.x)以及仓储检索。出版社访问受阻；Crossref 仅列出 Wiley 的出版版/文本挖掘链接和普通使用条款，没有开放许可或开放全文地址。没有绕过访问控制、没有发送索取邮件，也没有从文摘猜测其仪器/光源/黄叶光谱数值。
3. **EcoSIS ANGERS 2003**：[数据集 API](https://data.ecosis.org/api/3/action/package_show?id=angers-leaf-optical-properties-database--2003-) 可读，资源明确有 276 叶样的反射、透射 XLSX 和生化元数据，许可仅写 `Other (Open)`。但采集时间是 2003 年 6 月，不能作为秋黄叶证据；得到更直接的 Noda 黄叶资料后，未下载保留该整套候选。这样也避免将绿色/黄叶状态未知的样本混入交付。
4. **LOPEX93**：[EcoSIS 页面](https://data.ecosis.org/dataset/leaf-optical-properties-experiment-database--lopex93-) 可读，属于夏季经典叶片 R/T 数据库；本次未据此声称得到黄叶，也未另存一套冗余数据。

### 建议署名

Hibiki M. Noda, Takeshi Motohka, Kazutaka Murakami, Hiroyuki Muraoka, Kenlo Nishida Nasahara (2014), *Reflectance and transmittance spectra of leaves and shoots of 22 vascular plant species and reflectance spectra of trunks and branches of 12 tree species in Japan*. Ecological Research 29:111. DOI: [10.1007/s11284-013-1096-z](https://doi.org/10.1007/s11284-013-1096-z). 数据来自 JaLTER，CC BY 4.0；使用本项目派生 CSV 时注明仅选黄叶且截取 350–750 nm、原值未修改。

## 3. 已知灯箱与样品照片关联的 Morimoto 数据

来源：[Zenodo 5217752 v1.2](https://zenodo.org/records/5217752)，许可 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。署名：Takuma Morimoto, Cong Zhang, Kazuho Fukuda, Keiji Uchikawa；配套论文 *Spectral measurement of daylights and surface properties of natural objects in Japan*，Optics Express 30:3183–3204 (2022)，[DOI](https://doi.org/10.1364/OE.441063)。[全文测法 §2.1](https://pmc.ncbi.nlm.nih.gov/articles/PMC7612288/)。

### 决定性发现

- 有黄色银杏的**反射 R**：2014-12-10，反射原 CSV 第 306 行（含标题行计数）；原工作簿内照片明显黄色。
- 有银杏成对 R/T：2014-08-21，反射原 CSV 第 230 行、两份透射原 CSV 第 28 行；工作簿内照片为**绿叶**。
- **黄色银杏没有相同日期的 T**。不可把 12 月黄叶 R 与 8 月绿叶 T 拼成黄银杏真值。
- 有 *Dioscorea japonica*（山药属）黄色叶成对 R/T：2014-11-05，反射原 CSV 第 303 行、两份透射原 CSV 第 19 行。黄色来自对工作簿样品图的目视确认，日期与物种在三表一致；不是原作者专门给出的衰老诊断。它能作为其他物种黄叶的定量透射参考。
- 采后含水量/储存时长未给，不能对每片材料的新鲜程度作额外保证。物种名来自校园名牌或植物识别软件，未见样本逐项鉴定记录。

### 测法与校准

反射：X-Rite **SpectraLight QC** 灯箱设 D65，漫射顶光；Topcon **SR-2A**，1°视场、45°仰角接收；用平坦白校准板测得的入射光谱相除。透射：叶片展平放在 **FUJICOLOR LED Viewer ST-A4** 灯箱上，以黑纸开孔限制杂光；同一仪器测透射光，再除以单独测量的裸灯箱光谱。全部在暗室进行。`FrontSideUp` 表示正面朝接收器、光从叶背入射，`BackSideUp` 则相反。380–780 nm，5 nm 步长，81 个波长；数值为无量纲比例，0.4 即 40%，不要再除 100。来源：上述原始论文 §2.1.2–2.1.3。

有明确灯箱型号、光源比值和反射白参考，**没有逐样本原始裸光源 SPD、校准证书/误差条或照片色卡**。工作簿照片是样本识别缩略图，不是校准照片。该测法用有限视场接收，不是 Noda 积分球的总半球 R/T，二者不可无条件混作同一种散射参数，也不能用这组方向 R/T 的和强行推吸收率。380 nm 附近 T 有明显量化/低信号现象，不能把每一位小数都当相同精度。

### 文件清单

所有原始文件均为 Zenodo 原字节下载，MD5 与源 API 的 `checksum` 全部吻合；SHA-256、字节数、来源见 `manifest.json`。以下许可均为 CC BY 4.0，派生文件注明了变动。

| 本地路径 | 来源 URL | 内容与校准 |
|---|---|---|
| [`data/morimoto/Reflectance_v1-2.csv`](data/morimoto/Reflectance_v1-2.csv) | [原始文件](https://zenodo.org/api/records/5217752/files/Reflectance_v1-2.csv/content) | 359 自然物原始 R 数值表，含113叶，测法同上。 |
| [`data/morimoto/Transmittance_FrontSideUp_v1-2.csv`](data/morimoto/Transmittance_FrontSideUp_v1-2.csv) | [原始文件](https://zenodo.org/api/records/5217752/files/Transmittance_FrontSideUp_v1-2.csv/content) | 75叶正面朝上的原始 T 表，测法同上。 |
| [`data/morimoto/Transmittance_BackSideUp_v1-2.csv`](data/morimoto/Transmittance_BackSideUp_v1-2.csv) | [原始文件](https://zenodo.org/api/records/5217752/files/Transmittance_BackSideUp_v1-2.csv/content) | 相同75叶背面朝上的原始 T 表，测法同上。 |
| [`data/morimoto/Reflectance_v1-2.xlsx`](data/morimoto/Reflectance_v1-2.xlsx) | [原始文件](https://zenodo.org/api/records/5217752/files/Reflectance_v1-2.xlsx/content) | 原始 R 工作簿，内嵌359样品照片；照片无色卡/比例尺，仅用于核对样品。 |
| [`data/morimoto/Transmittance_FrontSideUp_v1-2.xlsx`](data/morimoto/Transmittance_FrontSideUp_v1-2.xlsx) | [原始文件](https://zenodo.org/api/records/5217752/files/Transmittance_FrontSideUp_v1-2.xlsx/content) | 原始 T 工作簿，内嵌75样品照片；无色卡/比例尺。 |
| [`data/morimoto/source_metadata.json`](data/morimoto/source_metadata.json) | [原始 API](https://zenodo.org/api/records/5217752) | 选存题名、说明、许可、文件下载/校验信息，未保存作者联系字段。 |
| [`data/morimoto/selected_spectra_derived.csv`](data/morimoto/selected_spectra_derived.csv) | 上述三份原始 CSV | 本次派生，3样本×81波长=243行；只转置/提取、按物种及日期匹配，原值未平滑/归一化，黄银杏 T 留空。保留源CSV行号。 |
| [`data/morimoto/manifest.json`](data/morimoto/manifest.json) | 上述源文件与本地 SHA-256 计算 | 逐文件路径、字节数、校验、许可与原件/派生标志，非校准证书。 |
| [`data/morimoto/notes.md`](data/morimoto/notes.md) | 本次核查，上述来源 | 使用说明，非实测数据。 |
| [`photos/morimoto/ginkgo_green_20140821_thumbnail.png`](photos/morimoto/ginkgo_green_20140821_thumbnail.png) | `Reflectance_v1-2.xlsx` 内 `xl/media/image1.png`，样本229 | 从原嵌入长条图按359个等高样本切出，无调色；约65×65像素，原图索引见源CSV行230。绿色，不能当黄叶。 |
| [`photos/morimoto/ginkgo_yellow_20141210_thumbnail.png`](photos/morimoto/ginkgo_yellow_20141210_thumbnail.png) | 同工作簿，样本305 | 同样派生，仅支持黄叶外观，原图索引见源CSV行306。无 T、无实体尺。 |
| [`photos/morimoto/dioscorea_yellow_20141105_thumbnail.png`](photos/morimoto/dioscorea_yellow_20141105_thumbnail.png) | 同工作簿，样本302 | 同样派生，目视黄色；原图索引见源CSV行303。可关联同日R/T，非高清纹理或校准图。 |

源反射 CSV 含尾部空行，透射 CSV 也含空行，实际有效样本分别359和75；不要把空行当新样本。所有选出光谱在380–780nm完整，R和两份T均在0–1。下列只为快速核对，不能代表全谱：山药黄色样本 T（FrontSideUp）450/550/650nm 为0.11038/0.40247/0.47045；夏季绿银杏对应为0.00044/0.05333/0.00784；黄银杏只有 R，450/550/650nm为0.07163/0.39051/0.47710。

## 4. 新鲜黄银杏背光与扫描照片

调查日期：2026-11-02。下载的三个文件均为 Commons 所列 **Original file** 的原字节文件，未裁切、调色或重新编码；已实际打开检查。`checksums.json` 记录大小、SHA-1、SHA-256。三张文件的 SHA-1 与 Commons 页面给出的值一致。

结论：找到有详细拍摄/处理记录的**在枝黄银杏透射照片**，以及可看斑点、细条纹和局部褐边的高清在枝照片、秋叶扫描。**没有找到公开可直接下载、带色卡/透射白参考、可作绝对颜色真值的新鲜黄银杏透射照片或相应 RAW。** 已知白平衡设置、ICC 或扫描仪型号不能替代光源光谱与色度标定。

### 1. 黄色在枝银杏，明确阳光透射，3028 × 3028

- 路径：`photos/supplementary/ginkgo_yellow_sun_transmission_Franz_van_Duns_2021.jpg`，3,129,292 字节。
- [来源与作者拍摄说明](https://commons.wikimedia.org/wiki/File:DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)；[原图 URL](https://upload.wikimedia.org/wikipedia/commons/5/52/DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)。作者：Franz van Duns。许可：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)，复用须署名，改编须按许可处理。
- 拍法：2021-10-22，德国 Dortmund；仍连在同一枝条上的黄叶，作者明确称秋日阳光透射。Sony Alpha 7R IV，FE 200–600 mm 镜头，400 mm、ISO 800、1/2000 s、f/7.1、曝光补偿 −1.3 EV；相机白平衡 5600 K。来源说明曾同时拍 JPEG 与 ARW，但**仅此 JPEG 公开，未找到 ARW 下载**。
- 处理：Lightroom 色温 5700 K、tint +13、texture +50、clarity +30、vibrance +10、saturation +3，并有非线性色调曲线；TIFF 中间文件后经 Photoshop 裁切成 JPEG。以上为作者记录，不能把 WB 数值当成实测日光色温。文件实际嵌入 `sRGB IEC61966-2.1` ICC（`sips` 检查）。
- 校准：无同场色卡、无白/灰参考、无光源 SPD/照度；后期已改对比度和饱和度。**只能作透射外观、脉序和重叠阴影参考，不能取色当真值**。
- 比例：作者称最上叶宽约 **80 mm**，可粗定尺度；无同平面实体尺，叶片弯曲、倾斜，不宜用作精密毫米标定。
- 新鲜性与细节：叶仍在枝上（来源文字和图像均支持），不属干燥标本。实际图可见放射条纹、细脉和重叠阴影；褐斑较少，边缘高光局部很亮。

### 2. 高清在枝黄叶，斑点与局部褐边，4032 × 3024

- 路径：`photos/supplementary/ginkgo_turning_yellow_Famartin_2020.jpg`，1,809,873 字节。
- [来源](https://commons.wikimedia.org/wiki/File:2020-10-24_13_13_22_Ginkgo_leaf_turning_yellow_in_autumn_at_the_Franklin_Farm_Village_Shopping_Center_in_the_Franklin_Farm_section_of_Oak_Hill,_Fairfax_County,_Virginia.jpg)；[原图 URL](https://upload.wikimedia.org/wikipedia/commons/5/57/2020-10-24_13_13_22_Ginkgo_leaf_turning_yellow_in_autumn_at_the_Franklin_Farm_Village_Shopping_Center_in_the_Franklin_Farm_section_of_Oak_Hill%2C_Fairfax_County%2C_Virginia.jpg)。作者：Famartin。许可：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。
- 拍法：2020-10-24，Virginia Franklin Farm，室外在树黄叶近照；iPhone X、4 mm、f/1.8、1/2114 s、ISO 20、自动曝光、自动 WB、无闪光；JPEG。文件实际嵌入 **Display P3** ICC（`sips` 检查），不要无视 ICC 直接按 sRGB 读 RGB 数值。
- 校准：无色卡、白参考、RAW、光源实测色温/SPD；**作者未明确说背光，单凭图像不能确认是纯透射**，保留作形态补充，不作为已校准透射图。
- 比例：无尺、未知叶宽，不能定毫米比例；EXIF 的 72 dpi 不能用来算叶片实物大小。
- 新鲜性与细节：图中叶柄连接树枝，支持在枝新鲜秋叶；实际打开可清楚看叶肉细条纹、小褐斑、轻微残绿和局部边缘褐损。不是扫描、压叶或干叶。

### 3. 单片变黄银杏扫描，1552 × 1944

- 路径：`photos/supplementary/ginkgo_autumn_scan_Ninjatacoshell_2008.jpg`，430,760 字节。
- [来源](https://commons.wikimedia.org/wiki/File:Autumn_Ginkgo_Leaf.jpg)；[原图 URL](https://upload.wikimedia.org/wikipedia/commons/4/4c/Autumn_Ginkgo_Leaf.jpg)。作者：Ninjatacoshell。页面双许可，选用 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)（另有 GFDL）。
- 拍法：2008-11-07，Brigham Young University 校园取得的秋季变色叶；Canon **CanoScan LiDE 70**；EXIF 600 × 600 dpi、自动 WB、Paint.NET v3.05；公开文件为 JPEG，实际嵌入 `sRGB IEC61966-2.1` ICC。**页面只确认扫描，未称透射模式**，因此不算已知透射扫描。
- 校准：无色卡、白参考测量、RAW、扫描色度标定文件或灯光 SPD。白底不等于可追溯透射白参考。
- 比例：没有实体尺。若 600 dpi 是未经缩放的真实采样分辨率，则每像素约 **0.0423 mm**、整幅约 65.7 × 82.3 mm；但文件经过编辑，未核实是否缩放，**只能有条件粗估，不是确定尺度**。
- 新鲜性与细节：来源说秋天变色叶，未提供采后时长、含水或是否干燥处理；**不能保证新鲜**。图像能看黄绿过渡、放射细脉、斑和较暗边缘，可作纹理/形态参考。

### 查过但未下载/未满足的候选

- [Leafsnap 官方数据页](https://leafsnap.com/dataset/)：说明 lab 叶片为 Smithsonian **pressed leaves**，含 controlled backlit/front-lit 两种，银杏有 120 张 lab + 21 张 field。页面未给出可核实开放许可，README 下载本次返回 HTTP 403；压叶也不等于新鲜秋叶，故没有为凑数下载约 977 MB 数据包。仅凭背景白色也无法证明光源/色度校准。
- [HALVS 作者仓库](https://github.com/WeizhenLiuBioinform/HALVS-Hierarchical-Vein-Segment)：大豆、甜樱桃、悬铃木未经化学处理的透射扫描；完整数据要求签用户协议并通过邮件申请。该来源没有可直接获取且许可明确的目标原图，不下载。论文/仓库只能作已知扫描方案线索，不能算已交付图像。
- [Gingo biloba leaves scan](https://commons.wikimedia.org/wiki/File:Gingo_biloba_leaves_scan.jpg)：作者明确是采集约两周后的 **dry** leaves，尽管有 CanoScan LiDE 25 / 300 dpi 记录和公有领域声明，不符合新鲜黄叶优先目标，未下载。
- [Public Domain Pictures 的 green ginkgo biloba leaves changing](https://www.publicdomainpictures.net/en/view-image.php?image=375672&picture=green-ginkgo-biloba-leaves-changing)：免费版本仅 1280 × 1920，4000 × 6000 原图须登录付费；无校准或尺度，未购买、未下载。



补充照片的支持文件：[`photos/supplementary/checksums.json`](photos/supplementary/checksums.json) 是上述三张Commons原图的SHA-1/SHA-256与字节数本地计算，许可随对应图像，非校准信息；[`photos/supplementary/notes.md`](photos/supplementary/notes.md) 是本次中文核查说明，来源如本节，非原始照片。

## 5. 如何用于这次渲染

1. **定量颜色范围**：从 `data/spectra/noda2014/*Betula*LICOR.csv` / `*Quercus*LICOR.csv` 选择一片黄叶的同一照明叶面R/T，或用 `data/morimoto/selected_spectra_derived.csv` 的 `dioscorea_yellow_20141105`。前者是积分球总量，后者是指定几何测量；按渲染器输出所对的物理量选择，不直接混平均。保留多个样本反映自然差异，不要选最饱和的一条当普遍真值。
2. **照明与输出**：明确约定照明谱（例如标准D65，而非仅“6500K”），用 `E(λ)T(λ)` 与标准观察者函数积分得到XYZ，再经正确色彩空间/曝光/显示变换比较。该结果只代表所选其他物种和测量几何。灯箱型号或相机WB数字本身不足以重建真实光源SPD。
3. **空间细节**：用Franz图看新鲜黄银杏透射的脉序、重叠阴影，用Famartin图看斑、条纹和局部褐边。Mander干叶可补形态，不能用于新鲜叶基色。扫描与样本缩略图的用途、比例限制见各项。
4. **仍缺的最终真值**：新鲜秋黄银杏的校准透射照片，或同一黄银杏叶的可见区R/T并附光源/几何/白暗参考。Matile1992全文和完整Dryad包在本环境受阻；没有将这些未取得材料算作已下载成果。

## 6. 文件验证与留盘范围

已实际解码全部10张JPEG原图（7张作者示例+3张Commons）；作者示例与作者GitHub blob一致，Commons三原图SHA-1与其页面一致，Morimoto五原件MD5与Zenodo一致。Noda20原件逐文件SHA-256已记录；350–750nm均401点完整，保留异常原值。Morimoto派生表243行，物种及日期匹配，黄银杏T明确留空。未修改原始图像/光谱数值。

`photos/mander/` 仅7张选定JPEG。没有留下Dryad完整ZIP（未取得）、作者镜像ZIP、Noda整ZIP或未选的Mander原图。3张 `photos/morimoto/*thumbnail.png` 是明确标注的样本识别裁片，原XLSX仍完整保留。逐源说明另见 `data/spectra/notes.md`、`data/morimoto/notes.md`、`photos/supplementary/notes.md`；根目录原有 `brief.md`、`log.txt` 未改动。
