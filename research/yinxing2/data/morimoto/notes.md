# Morimoto 自然物光谱：样本核查与使用说明

来源：[Zenodo 5217752 v1.2](https://zenodo.org/records/5217752)，许可 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。署名：Takuma Morimoto, Cong Zhang, Kazuho Fukuda, Keiji Uchikawa；配套论文 *Spectral measurement of daylights and surface properties of natural objects in Japan*，Optics Express 30:3183–3204 (2022)，[DOI](https://doi.org/10.1364/OE.441063)。[全文测法 §2.1](https://pmc.ncbi.nlm.nih.gov/articles/PMC7612288/)。

## 决定性发现

- 有黄色银杏的**反射 R**：2014-12-10，反射原 CSV 第 306 行（含标题行计数）；原工作簿内照片明显黄色。
- 有银杏成对 R/T：2014-08-21，反射原 CSV 第 230 行、两份透射原 CSV 第 28 行；工作簿内照片为**绿叶**。
- **黄色银杏没有相同日期的 T**。不可把 12 月黄叶 R 与 8 月绿叶 T 拼成黄银杏真值。
- 有 *Dioscorea japonica*（山药属）黄色叶成对 R/T：2014-11-05，反射原 CSV 第 303 行、两份透射原 CSV 第 19 行。黄色来自对工作簿样品图的目视确认，日期与物种在三表一致；不是原作者专门给出的衰老诊断。它能作为其他物种黄叶的定量透射参考。
- 采后含水量/储存时长未给，不能对每片材料的新鲜程度作额外保证。物种名来自校园名牌或植物识别软件，未见样本逐项鉴定记录。

## 测法与校准

反射：X-Rite **SpectraLight QC** 灯箱设 D65，漫射顶光；Topcon **SR-2A**，1°视场、45°仰角接收；用平坦白校准板测得的入射光谱相除。透射：叶片展平放在 **FUJICOLOR LED Viewer ST-A4** 灯箱上，以黑纸开孔限制杂光；同一仪器测透射光，再除以单独测量的裸灯箱光谱。全部在暗室进行。`FrontSideUp` 表示正面朝接收器、光从叶背入射，`BackSideUp` 则相反。380–780 nm，5 nm 步长，81 个波长；数值为无量纲比例，0.4 即 40%，不要再除 100。来源：上述原始论文 §2.1.2–2.1.3。

有明确灯箱型号、光源比值和反射白参考，**没有逐样本原始裸光源 SPD、校准证书/误差条或照片色卡**。工作簿照片是样本识别缩略图，不是校准照片。该测法用有限视场接收，不是 Noda 积分球的总半球 R/T，二者不可无条件混作同一种散射参数，也不能用这组方向 R/T 的和强行推吸收率。380 nm 附近 T 有明显量化/低信号现象，不能把每一位小数都当相同精度。

## 文件清单

所有原始文件均为 Zenodo 原字节下载，MD5 与源 API 的 `checksum` 全部吻合；SHA-256、字节数、来源见 `manifest.json`。以下许可均为 CC BY 4.0，派生文件注明了变动。

| 本地路径 | 来源 URL | 内容与校准 |
|---|---|---|
| [`data/morimoto/Reflectance_v1-2.csv`](Reflectance_v1-2.csv) | [原始文件](https://zenodo.org/api/records/5217752/files/Reflectance_v1-2.csv/content) | 359 自然物原始 R 数值表，含113叶，测法同上。 |
| [`data/morimoto/Transmittance_FrontSideUp_v1-2.csv`](Transmittance_FrontSideUp_v1-2.csv) | [原始文件](https://zenodo.org/api/records/5217752/files/Transmittance_FrontSideUp_v1-2.csv/content) | 75叶正面朝上的原始 T 表，测法同上。 |
| [`data/morimoto/Transmittance_BackSideUp_v1-2.csv`](Transmittance_BackSideUp_v1-2.csv) | [原始文件](https://zenodo.org/api/records/5217752/files/Transmittance_BackSideUp_v1-2.csv/content) | 相同75叶背面朝上的原始 T 表，测法同上。 |
| [`data/morimoto/Reflectance_v1-2.xlsx`](Reflectance_v1-2.xlsx) | [原始文件](https://zenodo.org/api/records/5217752/files/Reflectance_v1-2.xlsx/content) | 原始 R 工作簿，内嵌359样品照片；照片无色卡/比例尺，仅用于核对样品。 |
| [`data/morimoto/Transmittance_FrontSideUp_v1-2.xlsx`](Transmittance_FrontSideUp_v1-2.xlsx) | [原始文件](https://zenodo.org/api/records/5217752/files/Transmittance_FrontSideUp_v1-2.xlsx/content) | 原始 T 工作簿，内嵌75样品照片；无色卡/比例尺。 |
| [`data/morimoto/source_metadata.json`](source_metadata.json) | [原始 API](https://zenodo.org/api/records/5217752) | 选存题名、说明、许可、文件下载/校验信息，未保存作者联系字段。 |
| [`data/morimoto/selected_spectra_derived.csv`](selected_spectra_derived.csv) | 上述三份原始 CSV | 本次派生，3样本×81波长=243行；只转置/提取、按物种及日期匹配，原值未平滑/归一化，黄银杏 T 留空。保留源CSV行号。 |
| [`data/morimoto/manifest.json`](manifest.json) | 上述源文件与本地 SHA-256 计算 | 逐文件路径、字节数、校验、许可与原件/派生标志，非校准证书。 |
| [`data/morimoto/notes.md`](notes.md) | 本次核查，上述来源 | 使用说明，非实测数据。 |
| [`photos/morimoto/ginkgo_green_20140821_thumbnail.png`](../../photos/morimoto/ginkgo_green_20140821_thumbnail.png) | `Reflectance_v1-2.xlsx` 内 `xl/media/image1.png`，样本229 | 从原嵌入长条图按359个等高样本切出，无调色；约65×65像素，原图索引见源CSV行230。绿色，不能当黄叶。 |
| [`photos/morimoto/ginkgo_yellow_20141210_thumbnail.png`](../../photos/morimoto/ginkgo_yellow_20141210_thumbnail.png) | 同工作簿，样本305 | 同样派生，仅支持黄叶外观，原图索引见源CSV行306。无 T、无实体尺。 |
| [`photos/morimoto/dioscorea_yellow_20141105_thumbnail.png`](../../photos/morimoto/dioscorea_yellow_20141105_thumbnail.png) | 同工作簿，样本302 | 同样派生，目视黄色；原图索引见源CSV行303。可关联同日R/T，非高清纹理或校准图。 |

源反射 CSV 含尾部空行，透射 CSV 也含空行，实际有效样本分别359和75；不要把空行当新样本。所有选出光谱在380–780nm完整，R和两份T均在0–1。下列只为快速核对，不能代表全谱：山药黄色样本 T（FrontSideUp）450/550/650nm 为0.11038/0.40247/0.47045；夏季绿银杏对应为0.00044/0.05333/0.00784；黄银杏只有 R，450/550/650nm为0.07163/0.39051/0.47710。
