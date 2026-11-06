# 本轮空间透射检索：新增 HyperspecI 候选，未取得目标立方体

日期：2026-11-02。先读了 `../yinxing2/report.md` 和 `../yinxing3/report.md`，未重复下载 HyperART、LeafVAE 或 Thomas2022。

## 1. 新的近似材料：HyperspecI 2024，只有论文图和任意单位光谱

原始来源：Bian 等，*A broadband hyperspectral image sensor with high spatio-temporal resolution*, Nature 635:73–81，DOI [10.1038/s41586-024-08109-1](https://doi.org/10.1038/s41586-024-08109-1)。[原始全文 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11541218/fullTextXML)，[作者数据仓库](https://github.com/bianlab/Hyperspectral-imaging-dataset)。这是前两轮没有记录的线索。

**已实际打开 Fig4：** 图4b有被照亮的三片叶和光源，图4d展示三片叶的传射观测及合成RGB：最左为浅黄/米黄色，中间黄绿，右片绿。不是银杏外形。原文未给物种、采收日期、秋季/衰老状态；因此不能声称“已找到秋黄叶”。图4d的RGB参考与重建图之间有明显显示差异，不能直接取样本像素当颜色真值。

拍法与校准：原补充材料§7.1（PDF第34页、印刷页30）为遮光箱、散射板及LED/宽谱双模式系统；叶片模式由LED从叶后照明。未说明叶片模式LED型号、实测SPD、色温、色卡、白/暗参考或RGB相机RAW。§4.2（PDF第15页）用Omno151单色仪及Thorlabs S130VC/S132C功率计校准传感器响应矩阵；这是传感器光谱标定，不能替代逐叶透射率或RGB色度标定。补充材料已抽取相关页文字并渲染目视核对，全文PDF不留在交付目录。

| 本地文件 | 精确原件URL | 许可、内容与可用性 |
|---|---|---|
| `data/spatial_new/HyperspecI_2024_Fig4_original.png` | [出版社原图4](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-024-08109-1/MediaObjects/41586_2024_8109_Fig4_HTML.png) | **CC BY-NC-ND 4.0**（论文明确声明）；原字节完整论文图，非独立原始照片；无裁切调色。保留它仅为核查黄/绿叶及透射布置的证据，不能作颜色真值或数值cube。 |
| `data/spatial_new/HyperspecI_2024_SourceData_Fig4.xlsx` | [出版社Source Data Fig4原件](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08109-1/MediaObjects/41586_2024_8109_MOESM5_ESM.xlsx) | **CC BY-NC-ND 4.0**（随论文，未见该附件另行许可）；原始工作簿3表。Fig4b为光源、叶片各61点，400–1000nm、10nm间隔，列头是Intensity(a.u.)；Fig4d为三叶的重建/仪器比较光谱，同为a.u.。不是标明T(λ)的数据。 |
| `data/spatial_new/sciencedb_access_evidence.json` | [ScienceDB源页面](https://www.scidb.cn/en/detail?dataSetId=f9a0d077d12d478d81df5ec0358c6a0f) | 本次选择性保留JSON-LD字段，非原始实验数据；其license字段为空，不能把GitHub的MIT许可扩展给ScienceDB全部数据。 |
| `data/spatial_new/validation.json` | 上述工作簿本地解析 | 本次生成；记录维度/单位/值域核查，无校准效力。 |
| `data/spatial_new/manifest.json` | 本地SHA-256计算 | 本次生成；列出目录内其余文件大小、校验和及来源。 |

**数值限制已核查：** Fig4b的光源曲线和叶片曲线最大值都恰为1，正文图还把该组坐标写成Reflectance，工作簿列头却是Intensity(a.u.)。没有共同曝光/增益/归一化系数证明，不能把两条曲线直接相除恢复绝对T；这种未获依据的商最大约1.04243也不能当有效透射率。Fig4d虽有图中点1对应最左浅色叶的GT1数值，但仍是任意单位出射谱，并且采样点不具秋黄状态标记。**未导出冒充T的CSV，也未计算所谓黄银杏真值颜色。**

**立方体路径确实受限：** 作者README要求向数据所有者索取下载链接；其链接的ScienceDB DOI为[10.57760/sciencedb.18287](https://doi.org/10.57760/sciencedb.18287)，本次实际读取页面JSON-LD明确 `conditionsOfAccess: RESTRICTED`，185,494,139,893字节，license空。没有发申请，也没有下载整库。论文“数据在公开仓库”的表述不等于匿名可下载；未取得对应Fig4的数值空间cube。

## 2. 其它新增空间路线的明确排除证据

- [Li等2023 LeafSpec-Dicot原论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10098794/)：有白参考逐像素校正、双卤素灯，确为大豆整叶透射高光谱；Data Availability明确作者不分享数据。没有开放cube，不把装置介绍当数据交付。
- [Wei等2023 Dutch elm disease原论文](https://www.fs.usda.gov/nrs/pubs/jrnl/2023/nrs_2023_wei_001.pdf)，DOI[10.1016/j.aiia.2023.09.003](https://doi.org/10.1016/j.aiia.2023.09.003)：561片榆叶的高/多光谱cube是新空间透射线索，但Data availability明确upon reasonable request。未找到匿名原cube，未联系作者；病叶也不等于秋黄叶。
- [Reis Pereira等2024番茄透射数据I](https://zenodo.org/records/10498387)：LED背照、叶上9随机点采谱，记录明确Files Restricted；本来就是点光谱，不能称空间立方体。未下载。
- [Chloroplast movement的公开图像](https://www.bio-protocol.org/en/bpdetail?id=5541&pos=q&type=0)虽然给[Figshare30402409](https://figshare.com/articles/dataset/Hyperspectral_images_of_Arabidopsis_thaliana_and_Nicotiana_benthamiana_leaves/30402409)，原始方法将超光谱相机用于反射成像，另用660nm光度计测透射变化；是拟南芥/烟草绿叶，不能混称秋黄透射cube。未下载。

本分支没有取得能当颜色真值的黄秋叶照片，也没有新增可用的黄色秋叶空间T(λ)立方体；HyperspecI仅是比普通背光照片多了仪器校准线索的可核查近似材料。
