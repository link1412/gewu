# 黄/衰老叶成对反射与透射光谱研究记录

检索与下载日期：2026-11-02。

## 结论与建议

已实际取得 Noda 等（2014）的 20 个原始黄/衰老叶光谱 CSV，来自 5 个物种。每个文件都同时包含同一样本向轴面和背轴面各自的反射率 R、透射率 T。原始附录对全部 20 项明确标为衰老黄叶，因而不是凭低叶绿素或颜色曲线猜测。**没有银杏**。用于黄银杏材质的替代参考时，优先看阔叶的 **Betula ermanii（岳桦）和 Quercus crispula（水楢）**，特别是 `LICOR` 数据；可以约束黄叶可见区光谱的一般范围，不能当作黄银杏的精确真值。[数据论文 DOI](https://doi.org/10.1007/s11284-013-1096-z)，[原始测法](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/metadata/)，[逐样本附录](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/appendix.csv/at_download/file)。

数据版权以 2025-07-05 迁移后当前记录中的明确声明为据：**CC BY 4.0**。此声明已保存在本地 `noda2014/metadata.xml` 的 `intellectualRights` 中；作者署名见文末。[当前记录](https://jalter.diasjp.net/view/urn%3Auuid%3A103510db-c32a-4dec-b1e3-502cba05e7c2)。完整 ZIP 约 8.1 MB，仅临时下载并选择解出 20 个黄叶 CSV；整包与绿色样本均已删除。

## 测法、单位、校准与用途

- 文件第 3 行为 `#wl,R(adaxial),T(adaxial),R(abaxial),T(abaxial)`。首列是 nm，其余为无量纲比例，0.5 表示 50%，不应再除 100。向轴面、背轴面描述照明/测量所对的叶面；不是颜色空间通道。
- 原始光谱为 350–2500 nm，每 1 nm 一个采样值；**采样间隔不等于仪器光谱分辨率**。R/T 是积分球测得的叶片光学比率，适合计算给定照明 SPD 下的透射色。它不是相机 RGB，也不包含透射光的完整角分布，不能单独定义双向透射分布函数。
- 每个保留样本使用 FieldSpec FR 光谱辐射计。`LICOR` 是 LI-COR LI-1800-12 积分球，`ASDIS` 是 ASD RTS-3ZC 积分球。附录将阔叶列为 B-1 测法；落叶松针叶与芒草窄叶列为 B-2，涉及窄叶/针叶的端口填充处理。叶片采下数小时内在实验室测量，因而是新鲜采集的衰老黄叶，不是烘干材料。
- 原始测法说明 FieldSpec FR / FieldSpec 3 **每年校准**，积分球内表面/白参考涉及 BaSO4 / PTFE；引用了 Noda 等（2013）的标准测法。**未找到每个黄叶测量文件的独立白/暗参考读数、光源 SPD、色温、校准证书或测量不确定度**。因此可称有仪器与测法校准信息的光谱，不能声称有逐样本可追溯的绝对标定文件。[测法与仪器说明](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/metadata/)。
- 原作者指出 RTS-3ZC 的近红外 R+T 有时超过 1，故 `ASDIS` 与 `LICOR` 的同一样本不应无区别合并。LI-1800 在 1650–1740、1890–1950、2050–2500 nm 使用 `-9.999` 表示不可用数据；不能把这个占位值当物性。
- 这里的 R/T 没有给光源颜色或曝光；比渲染时，必须给真实或约定的光源 SPD 和观察者函数，计算 `SPD × T(λ)` 后再积分为 XYZ/RGB。透射率本身不是背光像素亮度；也不能把 R 颜色直接用作透射色。若材质不模拟荧光，这组普通 R/T 仍不等于对银杏荧光贡献的校准。

## 原始文件清单

下表每项许可均为 **CC BY 4.0**，拍法/测法、校准信息同上。每项来源均为[原始 ZIP 下载 URL](https://jalter.diasjp.net/metacat/d1/mn/v2/object/urn%3Auuid%3Af8bfce94-e567-4002-a966-44c4cc070d51)，成员路径前缀为 `ERDP-2013-02/`；本地 CSV **逐字节保留原始内容**，未裁剪、平滑、归一化或钳位。表内物种/衰老状态、B-1/B-2 测法来自附录；每项的完整 URL、归档成员路径、字节数和 SHA-256 另列于 `manifest.json`。

| 本地文件 | 物种 | 测量日 | 仪器/测法 | 黄/衰老证据 |
|---|---|---|---|---|
| [`Betula_leaf_yellow_2010_1006_1_ASDIS.csv`](noda2014/Betula_leaf_yellow_2010_1006_1_ASDIS.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Betula_leaf_yellow_2010_1006_1_LICOR.csv`](noda2014/Betula_leaf_yellow_2010_1006_1_LICOR.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Betula_leaf_yellow_2010_1006_2_LICOR.csv`](noda2014/Betula_leaf_yellow_2010_1006_2_LICOR.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Betula_leaf_yellow_2010_1006_3_LICOR.csv`](noda2014/Betula_leaf_yellow_2010_1006_3_LICOR.csv) | Betula ermanii Cham. | 2010-10-06 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_1_LICOR.csv`](noda2014/Larix_leaf_yellow_2011_1030_1_LICOR.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_2_ASDIS.csv`](noda2014/Larix_leaf_yellow_2011_1030_2_ASDIS.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + ASDIS / B-2 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_2_LICOR.csv`](noda2014/Larix_leaf_yellow_2011_1030_2_LICOR.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Larix_leaf_yellow_2011_1030_3_LICOR.csv`](noda2014/Larix_leaf_yellow_2011_1030_3_LICOR.csv) | Larix kaempferi (Lamb.) Carri_re | 2011-10-30 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Miscanthus_leaf_yellow_2010_1102_1_LICOR.csv`](noda2014/Miscanthus_leaf_yellow_2010_1102_1_LICOR.csv) | Miscanthus sinensis Andersson | 2010-11-02 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Miscanthus_leaf_yellow_2010_1102_2_LICOR.csv`](noda2014/Miscanthus_leaf_yellow_2010_1102_2_LICOR.csv) | Miscanthus sinensis Andersson | 2010-11-02 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Miscanthus_leaf_yellow_2010_1102_3_LICOR.csv`](noda2014/Miscanthus_leaf_yellow_2010_1102_3_LICOR.csv) | Miscanthus sinensis Andersson | 2010-11-02 | FieldSpec FR + LICOR / B-2 | 附录明确：衰老黄叶 |
| [`Pleioblastus_leaf_yellow_2013_0109_1_LICOR.csv`](noda2014/Pleioblastus_leaf_yellow_2013_0109_1_LICOR.csv) | Pleioblastus chino (Franch. et Sav.) Makino | 2013-01-09 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Pleioblastus_leaf_yellow_2013_0109_2_LICOR.csv`](noda2014/Pleioblastus_leaf_yellow_2013_0109_2_LICOR.csv) | Pleioblastus chino (Franch. et Sav.) Makino | 2013-01-09 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Pleioblastus_leaf_yellow_2013_0109_3_LICOR.csv`](noda2014/Pleioblastus_leaf_yellow_2013_0109_3_LICOR.csv) | Pleioblastus chino (Franch. et Sav.) Makino | 2013-01-09 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_1_ASDIS.csv`](noda2014/Quercus_leaf_yellow_2010_1007_1_ASDIS.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_1_LICOR.csv`](noda2014/Quercus_leaf_yellow_2010_1007_1_LICOR.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_2_ASDIS.csv`](noda2014/Quercus_leaf_yellow_2010_1007_2_ASDIS.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_2_LICOR.csv`](noda2014/Quercus_leaf_yellow_2010_1007_2_LICOR.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_3_ASDIS.csv`](noda2014/Quercus_leaf_yellow_2010_1007_3_ASDIS.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + ASDIS / B-1 | 附录明确：衰老黄叶 |
| [`Quercus_leaf_yellow_2010_1007_3_LICOR.csv`](noda2014/Quercus_leaf_yellow_2010_1007_3_LICOR.csv) | Quercus crispula Blume | 2010-10-07 | FieldSpec FR + LICOR / B-1 | 附录明确：衰老黄叶 |

## 元数据与派生文件逐项清单

| 本地文件 | 来源 URL / 许可 | 内容、校准与处理 |
|---|---|---|
| [`noda2014/metadata.xml`](noda2014/metadata.xml) | [当前 JaLTER 原始 EML](https://jalter.diasjp.net/metacat/d1/mn/v2/object/urn%3Auuid%3A103510db-c32a-4dec-b1e3-502cba05e7c2)；文件声明 CC BY 4.0 | 2025 年迁移记录，含作者、数据集介绍、版权、原始附件定义。保留原文。不是校准证书。 |
| [`noda2014/appendix.csv`](noda2014/appendix.csv) | [原始附录](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/appendix.csv/at_download/file)；归属于同一 CC BY 4.0 数据集 | 全部样本的物种、叶类型、仪器与测法索引。其 `File_name` 用 `.txt` 后缀，而 ZIP 实物为 `.csv`；按同名主干匹配，未改原附录。 |
| [`yellow_leaf_RT_350_750nm.csv`](yellow_leaf_RT_350_750nm.csv) | [同上 ZIP](https://jalter.diasjp.net/metacat/d1/mn/v2/object/urn%3Auuid%3Af8bfce94-e567-4002-a966-44c4cc070d51)；CC BY 4.0，派生整理 | 20 文件 × 401 波长 = 8020 行。统一列名并补源文件名与物种；仅裁取 350–750 nm，**保留所有原始数值**。有 `has_negative` 和 `R_plus_T_exceeds_1` 标志。 |
| [`validation.csv`](validation.csv) | 同上原始 CSV 的本地计算；CC BY 4.0 派生 | 逐文件记录完整点数、350–750 nm 极值、R+T 最大值、负值个数及波长范围。用于识别噪声，不是作者提供的误差估计。 |
| [`manifest.json`](manifest.json) | 原始 ZIP、[附录](https://db.cger.nies.go.jp/JaLTER/ER_DataPapers/archives/2013/ERDP-2013-02/appendix.csv/at_download/file)与本地校验；CC BY 4.0 派生 | 每一原始光谱的独立文件路径、来源 URL、ZIP 成员路径、许可、SHA-256、样本元数据。 |
| [`notes.md`](notes.md) | 本次研究记录；来源逐处标注 | 中文使用说明；非原始研究数据。 |

## 实际验证结果与限制

20 个原始 CSV 均成功解码/解析为 2151 个连续整数波长点（350–2500 nm）。350–750 nm 各有 401 点，无缺点、无 `-9.999` 占位值。此范围内所有样本、两面均 **R+T≤1**，所有文件中的最大值为 0.97384。Betula、Quercus、Pleioblastus 的四个 R/T 通道均非负。Larix 的 4 个文件与 Miscanthus 的 2 个文件在短波边缘出现负值，最坏为 Larix 的 ASDIS 样本 -0.0615091，负值最长延伸至 422 nm；说明该部分测量噪声/基线误差不可忽略。没有偷偷裁零或按光谱外形筛除不合意曲线。详细波长与数量见 `validation.csv`；优先使用桦木和栎树的 LICOR 曲线，并保留样本间差异。

这里只验证数据结构与基本物理范围，没有重新验证仪器校准，也没有把曲线数字化自论文图片。没有叶片对应照片、空间纹理或比例尺。

## 未取得的目标与检索记录

1. **黄银杏成对 R/T 数值光谱：本次未找到可公开直接下载的原始测量数据。** Noda 数据物种清单中没有银杏。
2. **Matile, Flach & Eller (1992) 全文：未下载成功。** 正确题名为 *Autumn Leaves of Ginkgo biloba L.: Optical Properties, Pigments and Optical Brighteners*，*Botanica Acta* 105(1):13–17，[DOI](https://doi.org/10.1111/j.1438-8677.1992.tb00261.x)。核查了[出版社正文入口](https://onlinelibrary.wiley.com/doi/10.1111/j.1438-8677.1992.tb00261.x)、[出版社 PDF 入口](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1438-8677.1992.tb00261.x)、[Crossref DOI 记录](https://api.crossref.org/works/10.1111/j.1438-8677.1992.tb00261.x)以及仓储检索。出版社访问受阻；Crossref 仅列出 Wiley 的出版版/文本挖掘链接和普通使用条款，没有开放许可或开放全文地址。没有绕过访问控制、没有发送索取邮件，也没有从文摘猜测其仪器/光源/黄叶光谱数值。
3. **EcoSIS ANGERS 2003**：[数据集 API](https://data.ecosis.org/api/3/action/package_show?id=angers-leaf-optical-properties-database--2003-) 可读，资源明确有 276 叶样的反射、透射 XLSX 和生化元数据，许可仅写 `Other (Open)`。但采集时间是 2003 年 6 月，不能作为秋黄叶证据；得到更直接的 Noda 黄叶资料后，未下载保留该整套候选。这样也避免将绿色/黄叶状态未知的样本混入交付。
4. **LOPEX93**：[EcoSIS 页面](https://data.ecosis.org/dataset/leaf-optical-properties-experiment-database--lopex93-) 可读，属于夏季经典叶片 R/T 数据库；本次未据此声称得到黄叶，也未另存一套冗余数据。

## 建议署名

Hibiki M. Noda, Takeshi Motohka, Kazutaka Murakami, Hiroyuki Muraoka, Kenlo Nishida Nasahara (2014), *Reflectance and transmittance spectra of leaves and shoots of 22 vascular plant species and reflectance spectra of trunks and branches of 12 tree species in Japan*. Ecological Research 29:111. DOI: [10.1007/s11284-013-1096-z](https://doi.org/10.1007/s11284-013-1096-z). 数据来自 JaLTER，CC BY 4.0；使用本项目派生 CSV 时注明仅选黄叶且截取 350–750 nm、原值未修改。
