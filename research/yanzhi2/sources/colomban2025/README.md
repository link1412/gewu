# Colomban 2025 原文与可见发射谱

来源：[Colomban, Tang & Simsek-Franci (2025), Applied Sciences 15:12265](https://doi.org/10.3390/app152212265)。
原 PDF：[出版社下载地址](https://mdpi-res.com/d_attachment/applsci/applsci-15-12265/article_deploy/applsci-15-12265.pdf)。检索/下载日：2026-11-02。

|原文位置|可核对的数字|证据性质|
|---|---|---|
|PDF p.9，Fig.5b|ruby 标注峰 594.7 nm；pink 607.4 nm；glaze 标注598.7、623.2 nm|可见发射谱，纵轴 Intensity，无绝对辐射单位。不是透射、反射或吸收系数。|
|PDF p.11，Fig.6b 与正文|常见发射峰约545 nm；图中部分点偏到约564 nm|实测发射峰的位置；不能拿Fig.5b某缺陷点的峰代表全部样品。|
|PDF p.4–5，§2.3|Labram HR800；514.5/457.9 nm激发；50×长工作距物镜，NA0.45；每点约5×5µm²|激光显微谱，非白光测色条件。Fig.5图注另写457.8 nm，照原文保留。|
|PDF p.10–11，§3.3|未给清代Au颗粒TEM粒径；提到的10–50 nm来自铜红釉TEM|作者对Au粒径是类比推测，不是本组清代金红TEM测量。|

注意原文图注与图内标注不完全一致：Fig.5b图注明写glaze×10、ruby(defects)、green，但图内曲线标为glaze、pink、ruby。本次照图内名称采数，不另定其采样点身份或强度倍数；不把这些强度用于跨色定量比较。保留整页便于复核。

- `fig5b_visible_luminescence.png`：从原PDF提取的Fig.5b嵌入原图，未重画。
- `page_08.png`–`page_11.png`：相关原页渲染。
- `fig5b_digitized_emission.csv`：本轮从图像数字化ruby和pink曲线；520–645nm，5nm步长。原始实测曲线的二次采样，**不是作者原始数据**。低波长处两条曲线重合，pink分不出时留空，不插值。
- `digitize_fig5b.py`：复现数字化脚本，仅读本地PNG；坐标由原图刻度校准，按颜色取线。数值取整到100强度单位，估计读图不确定度约±0.5nm、±300图示强度单位，未包含原实验误差。用于查看曲线形状，不作为绝对发光效率。
- `fig6_peak_positions.png`：Fig.6原图。
- `fulltext.txt`：PDF文字抽取，定位以原PDF页图为准。
