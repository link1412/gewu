# Narasimhan et al. 2006：原始表格核对

来源：[作者项目页](https://graphics.ucsd.edu/~henrik/papers/acquiring_scattering_properties/)；[作者托管的原始论文 PDF](https://graphics.ucsd.edu/~henrik/papers/acquiring_scattering_properties/acquiring_scattering_properties.pdf)。本地保存 `sources/scattering-project.html` 与 `sources/acquiring_scattering_properties.pdf`。核对日期：2026-11-06。

原论文 **Table 1（PDF 第 7 页）只直接列出消光系数 σ 与散射系数 β，没有直接列出吸收系数 κ**。Figure 2（PDF 第 2 页）定义 σ = β + κ：对应本任务常用记法，σ_s = β，σ_a = κ = σ − β。不能把原表的 σ 误当作 σ_a。以下把原抄值与推导值明确分开。

原表有 **Lemon Tea Powder（柠檬茶粉）**，所以不能写“没有茶”；但没有普通冲泡茶叶茶的单独测量行。酒类列出三种葡萄酒与三种啤酒；咖啡及相关冲调粉列出四行。

## 原表数字（原样抄录）

RGB 顺序均为 R、G、B；系数单位照原表为 **×10⁻² mm⁻¹**。例如表中 `0.3400` 表示 `0.003400 mm⁻¹`。Volume 保留原表拼写与单位；tsp/cup 等没有擅自转成毫升。

| 类别 | Material Name（原表） | Volume（原表） | 消光 σ，RGB（原抄） | σ_s = β，RGB（原抄） |
|---|---|---|---|---|
| 茶粉 | Lemon Tea Powder | 5tsp | (0.3400, 0.5800, 0.8800) | (0.0798, 0.0898, 0.1073) |
| 葡萄酒 | Wine (chardonnay) | 3300ml | (0.1577, 0.1748, 0.3512) | (0.0030, 0.0047, 0.0069) |
| 葡萄酒 | Wine (white zinfandel) | 3300ml | (0.1763, 0.2370, 0.2913) | (0.0031, 0.0048, 0.0066) |
| 葡萄酒 | Wine (merlot) | 1500ml | (0.7639, 1.6429, 1.9196) | (0.0053, 0.0000, 0.0000) |
| 咖啡 | Coffee (espresso) | 8ml | (0.4376, 0.5115, 0.6048) | (0.2707, 0.2828, 0.2970) |
| 咖啡 | Coffee (mint mocha) | 6ml | (0.1900, 0.2600, 0.3500) | (0.0916, 0.1081, 0.1460) |
| 咖啡冲调粉 | Cappuccino Powder | 0.25tsp | (0.2574, 0.3536, 0.4840) | (0.0654, 0.0882, 0.1568) |
| 摩卡冲调粉 | Suisse Mocha Powder | 0.5tsp | (0.5098, 0.6476, 0.7944) | (0.3223, 0.3583, 0.4148) |
| 啤酒 | Beer (budweiser) | 2900ml | (0.1486, 0.3210, 0.7360) | (0.0037, 0.0069, 0.0074) |
| 啤酒 | Beer (coorslight) | 1000ml | (0.0295, 0.0663, 0.1521) | (0.0027, 0.0055, 0.0000) |
| 啤酒 | Beer (yuengling) | 2900ml | (0.1535, 0.3322, 0.7452) | (0.0495, 0.0521, 0.0597) |

表注说明这些是稀释样品：材料体积 V 加入 (23 − V) 升水，使最终总体积为 23 升（V 用升代入）；原样品浓度不同，不能直接把系数当作日常杯中未稀释饮料的系数。原表说可依 V_n/V 比例缩放至其他材料体积，报告不作额外浓度换算。[依据：Table 1 表注，PDF 第 7 页。](https://graphics.ucsd.edu/~henrik/papers/acquiring_scattering_properties/acquiring_scattering_properties.pdf)

## 吸收系数（计算值，不是原表直接列值）

以下对原表印出的四位小数逐通道相减：**σ_a = σ − β**；单位同样是 **×10⁻² mm⁻¹**。这些数值只能称为“由原表推导”，不能称为“吸收系数原样抄表”。散射仍是原表直接列值，且没有换算成 reduced scattering σ_s′。

| Material Name（原表） | σ_a，RGB（计算值） | σ_s，RGB（原抄） |
|---|---|---|
| Lemon Tea Powder | (0.2602, 0.4902, 0.7727) | (0.0798, 0.0898, 0.1073) |
| Wine (chardonnay) | (0.1547, 0.1701, 0.3443) | (0.0030, 0.0047, 0.0069) |
| Wine (white zinfandel) | (0.1732, 0.2322, 0.2847) | (0.0031, 0.0048, 0.0066) |
| Wine (merlot) | (0.7586, 1.6429, 1.9196) | (0.0053, 0.0000, 0.0000) |
| Coffee (espresso) | (0.1669, 0.2287, 0.3078) | (0.2707, 0.2828, 0.2970) |
| Coffee (mint mocha) | (0.0984, 0.1519, 0.2040) | (0.0916, 0.1081, 0.1460) |
| Cappuccino Powder | (0.1920, 0.2654, 0.3272) | (0.0654, 0.0882, 0.1568) |
| Suisse Mocha Powder | (0.1875, 0.2893, 0.3796) | (0.3223, 0.3583, 0.4148) |
| Beer (budweiser) | (0.1449, 0.3141, 0.7286) | (0.0037, 0.0069, 0.0074) |
| Beer (coorslight) | (0.0268, 0.0608, 0.1521) | (0.0027, 0.0055, 0.0000) |
| Beer (yuengling) | (0.1040, 0.2801, 0.6855) | (0.0495, 0.0521, 0.0597) |

## 核对记录

- 先提取原 PDF 全文到 `sources/acquiring_scattering_properties.txt`，再渲染并肉眼查看第 2 页符号表与第 7 页完整数据表、表头和表注，逐项核对上述 11 行的名称、Volume、六个系数和单位。
- 保存的可视核对页：`sources/scattering-notation-p2.png`、`sources/scattering-table-p7.png`。使用 PDFKit 提取与渲染，没有修改原始 PDF。
- 作者服务器的 HTTPS 证书当前与 `graphics.ucsd.edu` 主机名不匹配。下载时仅为此作者来源关闭证书校验，保留原 HTML 和 PDF，未借用二手转录资料。
