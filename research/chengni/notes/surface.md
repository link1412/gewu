# 表面粗糙度与光泽核查

检索日期：2026-11-02。未找到目标鳝鱼黄澄泥砚的Ra/Sa、GU或BRDF公开实测。以下均为替代或方法依据。

## 无釉造型黏土：同一实验中的粗糙度与光泽

Hur等，2026，JKSPE 43(10):1027–1036，DOI [10.7736/JKSPE.026.00056](https://doi.org/10.7736/JKSPE.026.00056)。[官网全文](https://www.jkspe.or.kr/journal/view.php?number=7316)，[原始PDF](https://www.jkspe.or.kr/upload/pdf/JKSPE-026-00056.pdf)，本地 `papers/surface_Hur_2026_unglazed_clay_polishing.pdf`。

材料是市售造型黏土（东营陶瓷，含砂高），850°C素烧；上釉对照另1250°C复烧。不是澄滤细泥，不以Ra代表澄泥砚。原文p.1030/PDF4：SJ-310接触式轮廓仪，参考ISO4288，未列具体cutoff；YG60S光泽计60°、ISO2813，5独立试片各8次测量。p.1031/PDF5图6给Ra轮廓值，图7给GU均值与标准差。图6原始/磨削/抛光轮廓横轴约12mm，上釉约4mm，Ra不能被表述为有同样带宽的群体统计均值。

|工序|Ra/μm（图6）|60°GU均值±SD（图7）|
|---|---:|---:|
|850°C素烧Raw|8.015|1.91±0.07|
|磨削Grinding|5.327|4.03±1.21|
|SiC逐级湿抛至2000目Polishing|3.060|7.11±0.99|
|上釉1250°C复烧Glazing|1.143|53.31±14.58|

正文把上釉光泽约写53GU，以图7精确表为准。数字均为本实验材料；禁止转为鳝鱼黄实测或通用粗糙度范围。读图确认于PDF5。

## 蜂蜡/油与陶器表面

Rueff等2021，DOI [10.1016/j.jasrep.2021.103021](https://doi.org/10.1016/j.jasrep.2021.103021)；[HAL作者稿](https://hal.science/hal-03468734v1)，[PDF](https://hal.science/hal-03468734/document)，本地 `papers/surface_Rueff_2021_reading_ceramic_surfaces.pdf`，19页。自然黏土加相当黏土质量25%的<1mm碳酸盐料，750°C 4h；蜂蜡熔化后涂到预热、已烧陶片。共焦测量25mm²、横向分辨率2μm，采用SMa小波幅值，不是统一Ra。图4–5表明涂层减少凸起、压光与涂层组合表面更平整。作者稿PDF10原文将蜂蜡/乳/橄榄油处理样品水接触角汇总为50–70°，未处理0–30°；是分组概述而非蜂蜡独立精确值，更不是GU或IOR。报告仅用机理，不硬提取图线替代Ra。

## 单位与渲染

[BYK白皮书](https://media.byk-instruments.com/shop/Misc/Whitepaper/White_Paper_Gloss_Measurement_EN_20221114.pdf) PDF5：GU为一定孔径、角度的镜向反射相对黑玻璃标准的比值，标准折射率1.567赋100GU；不是反射率百分数。曲面测量有限制。 [Blender官方Principled说明](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html)：roughness是微表面参数，coat可单独设roughness/IOR/normal；无需把高度Ra强行映射为0–1。自拟渲染起点须标明经验假设，非文献参数。
