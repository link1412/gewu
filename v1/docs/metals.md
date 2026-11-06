# 金属:pbrt 的 conductor 进两个适配器

- 片子里用到的金属(`docs/imagery.md`):
  - 朱门的鎏金门钉、掐丝珐琅的鎏金铜丝、金箔(27、7)、花丝(银,33);
  - 铜镜:高锡青铜(18)。
- 场景照 pbrt-v4 的写法,同一个文件在 pbrt(光谱参考)和 Cycles(`tools/cycles_scene.py`)里都能渲。
- 材质卡:鎏金铜,见 `docs/materials/gilt_copper.md`。

## 语法

```
Material "conductor" "spectrum eta" "metal-Au-eta" "spectrum k" "metal-Au-k"
    "float roughness" [ a ] "bool remaproughness" false
    ["texture roughness" "r"] ["texture displacement" "h"]
Material "conductor" "spectrum reflectance" [ λ r λ r ... ] ...
```

- `eta`、`k` 可以写成三种:
  - pbrt 自带的光谱名 `metal-X-eta/k`,X 是 Au、Ag、Al、Cu、CuZn、MgO、TiO2。
    - 从 pbrt 的源码里读(`util/spectrum.cpp`)。
    - 照 `FromInterleaved` 的语义,样本以外取端点的值。
  - 光谱文件:成对的 λ、值,`#` 起注释,路径相对场景文件。
  - 直接写数值。
  - 后两种照 pbrt 的 `PiecewiseLinear` 语义,样本以外是 0。
    - 传感器 × 主光的权重落在 0 上超过 0.5%,就报错。
- 不写 `eta`、`k`:用 pbrt 的默认值,也就是铜。
- `reflectance`:照 pbrt(`materials.h`)的算法,逐个波长取 eta = 1、k = 2√r / √(1 − r),r 夹在 [0, 0.9999]。
  - 和 eta、k 不能同时给(pbrt 也不许)。
- 粗糙度和 dielectric 一样:
  - `remaproughness` 必须是 false,值就是 GGX 的 α;
  - 可以给一张浮点纹理(`texture roughness`),Cycles 里送 √α。
- 凹凸贴图(`texture displacement`)照 `docs/textures.md`,要 UV。
- 报错的情况:
  - `uroughness`、`vroughness`(各向异性);
  - eta、k、reflectance 用纹理;
  - `rgb eta` 这类 RGB 写法。

## 光谱怎样变成三个通道(`rgbscene.conductor_channels`)

- **问题**:Cycles 按 RGB 算。金属的颜色来自 Fresnel 反射率随波长、随入射角一起变。
  - 把 n(λ)、k(λ) 直接按通道平均,得到的反射率和按光谱算再平均的不一样。
  - 金差得最多:ΔE*ab 5.7(下面 a 的数字)。
- **做法**:
  - 每个通道的目标是光谱 Fresnel 曲线的通道平均:
    F̄_c(θ) = Σ_λ w_c(λ) F(θ; n(λ), k(λ)) / Σ_λ w_c(λ)。
  - w 是传感器 × 主光(`--key-K`),和反射率的投影一样。所以主光照一次反弹,每个角度都是对的。
  - 再给每个通道找一对 (n_c, k_c),让 F(θ; n_c, k_c) 贴住 F̄_c(θ):
    - 最小二乘,θ 在 0–89.5° 上等距取;
    - 起点是 n、k 的直接平均。
- **结果写进 JSON**:
  - `eta`、`k`(每通道一个);
  - `fresnel_fit`:在 0、30、45、60、70、80、85、89° 上的光谱值和拟合误差,以及全程最大误差;
  - `source`:用了哪条光谱。
  - rgbscene 运行时也打印一行。
- **Cycles 这边**:
  - Metallic BSDF,`fresnel_type` 设成 `PHYSICAL_CONDUCTOR`,按通道给 IOR、Extinction。
  - 分布用 `GGX`。默认的 Multiscatter GGX 会多出 pbrt 没有的能量,不能用。
  - Roughness = √α,薄膜厚度 0。
  - 要先设 `fresnel_type`,再找 IOR、Extinction 两个口:没设之前,这两个口在 Blender 5.2 里按名字找不到。
- **Cycles 和 pbrt 的公式是一样的**(查的 Blender 5.2 源码):
  - Fresnel:`fresnel_conductor`(`closure/bsdf_util.h`)是复折射率的精确公式,和 pbrt 的 `FrComplex` 是同一个函数,写法不同;
  - 遮挡:Smith 的高度相关形式 1/(1 + Λ_i + Λ_o)(`bsdf_microfacet.h`),和 pbrt 的 TrowbridgeReitz 一样;
  - 粗糙度:α = roughness²(`svm/closure.h`)。

### 拟合误差(`tests/metals/check_fit.py`,5D Mark IV × 5500 K)

各角度的绝对误差,全程最大:

| 金属 | R | G | B | 直接平均 n、k 的最大误差 |
|---|---|---|---|---|
| Au | 0.0017 | 0.0035 | 0.0029 | 0.019(B,0–60°) |
| Ag | 0.0002 | 0.0002 | 0.0003 | 0.003 |
| Cu | 0.0023 | 0.0011 | 0.0005 | 0.007 |
| CuZn | 0.0012 | 0.0016 | 0.0015 | 0.012 |
| Al | 0.0004 | 0.0004 | 0.0004 | 0.002 |

- 误差最大的地方在 60–70° 和 85°:曲线下凹、再回升的那一段。
- 法向入射时,金的拟合误差是 +0.0006、+0.0010、+0.0006。

### 多次反弹的误差(RGB 渲染本身的限制,拟合补不了)

- 光在金属上反射 n 次,真值是 F(λ)ⁿ 的通道平均,RGB 算的是 (F_c)ⁿ。
- 法向入射时(`check_fit.py`),相对误差如下:

  | 金属 | 2 次 | 3 次 | 5 次 |
  |---|---|---|---|
  | Au(R, G, B) | −1.5%, −6.7%, −9.2% | −3.9%, −17.5%, −26.6% | −10%, −42%, −65% |
  | Cu | −2.0%, −1.7%, −1.1% | −6.0%, −5.5%, −3.6% | −17%, −19%, −14% |
  | CuZn | −0.7%, −2.2%, −5.3% | −1.9%, −6.3%, −15% | −5%, −18%, −40% |
  | Ag | 0, 0, −0.02% | −0.01%, −0.03%, −0.1% | −0.05%, −0.1%, −0.4% |

- 都偏低:RGB 渲染的多次反射比真的暗,G、B 更暗,所以颜色比真的更饱和、更红。
- 银几乎没有误差,花丝(33)的颜色不怕多次反弹;金在两三次反弹时就差得多。
  - 金箔飘落(27)、泥金(7)、鎏金的凹处,先渲一帧和 pbrt 比;差得多,就按 DESIGN §5 分波段渲。[待做:这几镜还没有建]
- 金映金(光谱上算的,不是 RGB 的误差):单次 R/G 1.31、B/G 0.44,两次 R/G 1.72、B/G 约 0.19 [D]。
  - 鎏金卡的照片(Cleveland 1970.149.1)比单次饱和(R/G 1.57)。在照片只映白灯的高光肩部量，也是 R/G 1.54–1.70 [M],所以照片的饱和不是金映金(`docs/materials/gilt_copper.md`「颜色」)。

## 验证

`tests/metals/`,用 `python3 -I` 跑:
- `gen_*.py`:写场景;
- `run_*.py`:推送渲染,排队,拉回;
- `check_*.py`:算数字。
- 渲染:
  - pbrt 走 CPU;
  - Cycles 优先走 GPU。
- 渲染在 `out/metals/`。

### a. 入射角和颜色(`gen_fresnel.py`、`check_fresnel.py`)

- **场景**:
  - 一排 8 块平板,同一种金属。
  - 每块倾斜到让相机看它的入射角是 8、30、45、60、70、80、85、88°。
    - 相机 3 m 远,光线几乎平行;
    - 每块投影后都是 12 × 12 mm。
  - 每块的镜面方向上有自己的小面光(24 mm,400 mm 远,5500 K)。
  - 一行下面有一块朝相机的同样的面光,当白参照。
- **变体**,960×540、128 spp:
  - Au、Ag、Cu(pbrt 的光谱名)× α 0、0.02、0.1;
  - 再加一个 `reflectance` 的(一条编的上升反射谱,α 0)。
- **对照**:按像素的解析预测,在测试里独立算,不调 rgbscene 的函数:
  - 光滑:F(θ) × L,θ 是这个像素的入射角;
  - 粗糙:GGX(D、高度相关 G、F)乘 L cos,在所有面光上积分(每块光 32×32 中点);
  - 给 pbrt 的预测用光谱 F 的通道平均,给 Cycles 的用 JSON 里的每通道 eta、k。
  - 只算离板边 2 mm 以内的像素(每块约 230 个)。
  - 读数是板 / 白参照。
- **光滑的结果**(Au、Ag、Cu、reflectance,8 个角度):
  - pbrt / 光谱预测:0.9999–1.0009。剩下的是 pbrt 按波长抽样的噪声。
  - Cycles / 拟合预测:1.0000(四位小数)。
  - Cycles / pbrt:
    - 金 0.9966–1.0040,银 0.9998–1.0003,铜 0.9980–1.0025,reflectance 0.9964–1.0037。
    - 剩下的差就是上面的拟合误差。
  - 颜色,ΔE*ab(相机链的色卡矩阵,白 = 参照光):
    - pbrt 对 Cycles 0.00–0.28;
    - pbrt 对光谱预测 0.00–0.08。
  - 检验有分辨力:直接平均 n、k 的预测离光谱预测,金 ΔE 5.7(8°)到 0.2(88°),铜 1.5,reflectance 1.6,银 0.2。
- **粗糙的结果**(α 0.02、0.1,三种金属,8 个角度):
  - Cycles / pbrt:0.995–1.007;
  - pbrt / 预测:0.992–1.003;
  - Cycles / 预测:0.996–1.004;
  - ΔE pbrt 对 Cycles 0.04–0.38。
  - 88° 时两个渲染器都比预测低 0.4–0.8%,三个通道一样。这是预测的积分误差(掠射时光的投影很窄),不是颜色。
  - 两个 α 之间,板的读数差 10–15 倍;对预测的偏差不超过 0.8%。
- **白参照**:pbrt 0.4577、0.9620、0.6864,Cycles 0.4568、0.9611、0.6856,JSON 里的 emission 0.4568、0.9611、0.6856。pbrt 高 0.1–0.2%,上面的比值都是对各自的白参照。
- 数字:`out/metals/fresnel/numbers.json`。

### b. 拟合和多次反弹(`check_fit.py`)

- 只算数,不渲染。数字见上面两张表。
- `--extra NAME=eta.spd,k.spd` 可以加别的光谱(比如以后的青铜)。

## 合金和镀层的数据(调研 2026-10-29)

| 要的 | 找到的 | 用法和标记 |
|---|---|---|
| 金、银、铜、黄铜、铝 | pbrt 自带 | [I] |
| 火镀金(金汞齐烧过) | 没有 n、k。有:<br>Joshi 2022 的 400–700 nm **相对**反射谱(只有图);<br>层厚 2–10 µm;<br>Hg 2.6–17.4 wt%;<br>AFM 的 rms 6.6–34 nm | 用纯金代替,标 [I],代用 [A];层厚、Hg 只作范围,写进 `materials/gilt_copper/material.json` |
| 高锡青铜(铜镜) | **没有数值表**:<br>Callet & Zymla 2006 用椭偏量过 Cu80Sn20、Cu90Sn10、Cu70Sn30,公开的只有 400–750 nm 的图;<br>他们的 κ 是 Born 的记号,k = nκ;<br>Tolansky 1947,约 45% Sn 的 speculum:R(450 nm) = 0.63,R(650 nm) = 0.75,只有摘要里这两个点 | 缺数据,先不做铜镜;可以走的路见下 |
| 赤铜矿 Cu2O、黑铜矿 CuO | Palik 手册表的公开转录,300–1000 nm,每 50 nm 一个点;<br>Tahir 2012 的 REELS 数字表(Zenodo,没下下来) | [I];手册有版权,不进 git |
| 金银合金 | Rioux 2014 的解析模型(椭偏拟合),refractiveindex.info,CC0,Au 0–100% 每 10%,270–1200 nm | [I],模型值,不是每个配比都量过;金箔含银时用 |

- 铜镜的数据,可以走的路:
  1. 跟 Callet 要原始表,或者数字化他的图(要标 [D],带读图误差);
  2. 先用 Tolansky 的两个点,以 `reflectance` 写法做一块「接近」的镜面,标 [A]。
- 青铜不能拿黄铜(CuZn)或纯铜、纯锡的混合来冒充(调研也这么说)。

## 以后做:金箔透绿光(Faraday 1857)

- **现象**:
  - 金箔约 0.1 µm 厚,对着光看是绿的。
  - 透过率 T(λ) ≈ (1 − R)² e^(−4πkd/λ) × 干涉项。
  - 金的 k 在 500 nm 附近最小(约 1.9),到 650 nm 约 3.6。
    - d = 100 nm 时,e^(−4πkd/λ) 在 500 nm 约 0.8%,650 nm 约 0.1%:透出来的是绿光。
  - 这是估算 [D],没有算干涉,也没有对实测。
- **做法**:空气 | 金膜 d | 空气的薄膜:
  - 用特征矩阵(和 `shots/19-luodian/nacre.py` 同一套)算 r、t,分 s、p 两种偏振,复折射率直接进矩阵;
  - 得到 R(θ, λ)、T(θ, λ);透射光方向不变(两边都是空气)。
- **pbrt**:要加一个我们自己的 BxDF,比如 `Material "thinconductor" "spectrum eta" ... "spectrum k" ... "float thickness" d`:
  - 像 `ThinDielectricBxDF`:镜面反射 R、直穿 T,按 R/(R + T) 选;
  - 粗糙的版本以后再说。
  - 改 `materials.h/.cpp`、`bxdfs.h`,再重新生成补丁;跑 `tests/rnee/`。
- **适配器**:
  - rgbscene:在 `material()` 加一个分支。
    - 用特征矩阵算 R、T 对 cos θ 的表(比如 64 个点),按通道平均(传感器 × 主光),写进 JSON。
    - 和 `nacreinlay` 的表一样;一次反弹是精确的。
  - cycles_scene:
    - 按 |cos θ| 查表,得到 R_c、T_c;
    - Mix(Transparent,颜色 T;Glossy,颜色 R),和 `thin_dielectric()` 一样,只是 R、T 来自表,不是公式。
    - Cycles 的 Metallic BSDF 带的「薄膜」是金属上面的介质膜,不是悬空的金属膜,用不上。
  - 青花在 thindielectric 上加了 `transmittance`(一层膜,eta = 1)。可以看能不能直接用它的接口:那条路只要每通道的 T,不随角度变。
- **验证**:
  - 和 pbrt 的新 BxDF 比;
  - 和闭式解比:法向入射时,单层膜的 T 有解析式;
  - 和实测的金膜透射谱比:比如 Johnson & Christy 的样品厚度。

## 没做的、近似的

- 各向异性粗糙度、纹理的 eta、k:报错。
- 多次反弹的颜色误差(上面那张表):RGB 的限制,只有分波段渲才能消。
- Cycles 里拟合给出的 eta(比如 reflectance 写法拟合出 0.96–0.99)是等效值,不是这种材料真的 n。它只保证 Fresnel 曲线对。
- 金属上的薄膜(锈、漆):pbrt 的 conductor 没有。Cycles 的 Metallic 有薄膜参数,但两边对不上,没接。
- 合金的数据缺口(上面「合金和镀层的数据」):火镀金(Au–Hg–Cu)、高锡青铜没有 n、k 表。鎏金卡用纯金代替 [A]。[待做]

