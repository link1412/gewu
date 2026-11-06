# 纹理:空间变化的表面

- S3 的顺序是材质 → 物体 → 光学 → 运动。材质要有空间变化的表面,所以适配器(`tools/rgbscene.py` 写 JSON,`tools/cycles_scene.py` 在 Cycles 里渲)要认纹理。
- 语法和语义照 pbrt-v4:同一个场景文件,在打过补丁的 pbrt(光谱参考)里照样能渲。
- 例外:`familymap` 是我们的扩展。S3 起打过补丁的 pbrt 也认它(按光谱取族的成员,`docs/coats.md`),所以带它的场景也有光谱参考;`nacreinlay` 仍然只有 Cycles。

## pbrt 自带的部分

### UV
- `plymesh`:读顶点属性 `u`,`v`(或 `s`,`t`,或 `texture_u/v`、`texture_s/t`),作 Blender 网格的 UV 图。
  - Blender 的 ply 导入把它们当普通属性,`cycles_scene.py` 再搬到 UV 图上。
- `bilinearmesh`:pbrt 的默认角点 UV:p00 (0,0),p10 (1,0),p01 (0,1),p11 (1,1);写了 `"point2 uv"` 就用它。
- `disk` 没有 UV:带纹理的材质贴在 `disk` 上,直接报错。

### 浮点图像纹理
- 语法:

  ```
  Texture "n" "float" "imagemap" "string filename" "f.exr" ["float scale" s] ["bool invert" b]
      ["string wrap" "repeat"|"clamp"] ["float uscale" a] ["float vscale" b]
      ["float udelta" c] ["float vdelta" d] ["string encoding" "linear"|"sRGB"]
  ```

- 语义(`FloatImageTexture`,默认 `uv` 映射):
  - s = a·u + c,t = b·v + d;图像的第一行在 t = 1(pbrt 的 t 向下数,Blender 的向上);
  - 值 = scale × 双线性取样;`invert` 时再取 max(0, 1 − 值);
  - 一个通道取它,三个通道取平均(pbrt 一样);
  - 四通道的图,pbrt 返回 alpha,我们不处理(取 RGB 平均,不看 alpha)。
- 文件:EXR(浮点,首选)、PFM、16 位 PNG。线性数据,不是颜色。
  - PNG 的默认编码是 sRGB(pbrt 一样),要线性值就写 `"string encoding" "linear"`。
  - 文件名相对场景文件,JSON 跟着目录走。
- 没做的:`filter` 不是 bilinear、`mapping` 不是 `uv`、`wrap` 是 `black` 或 `octahedralsphere`,都报错。
- 和 pbrt 不一样的地方:Cycles 没有 MIP 金字塔,总是双线性取样;pbrt 按光线微分选一级。贴图分辨率够高、远处不糊,这两个没有区别;没有单独量。
- 数据在 Cycles 里是一张 Non-Color 的浮点图(EXR 和 PNG 经 Blender 读,PFM 自己读),不过色彩管理。

### 凹凸贴图(bump)
- 语法:`Material "diffuse"|"dielectric"|"thindielectric" "texture displacement" "n"`,`n` 是上面的浮点纹理。
- 语义(`BumpMap`,`materials.h`):位移 d(u,v) 沿法线,单位是场景单位(mm);dpdu' = dpdu + ∂d/∂u · n。
- Cycles:Bump 节点。
  - 高度送 mm 值,`Distance` = 1e-3(mm → m)。**不能把高度先换成米再送、`Distance` = 1**:试过,高度只有 3e-8 m 的量级,Blender 的凹凸完全没有起作用(渲出来和没贴一样)。
  - 薄介质(`thindielectric`)把凹凸后的法线同时送进夹角余弦和镜面波瓣。
- 一块凹凸后的法线进 `Normal` 输入:diffuse、玻璃,薄介质的镜面。

### 粗糙度贴图
- 语法:`Material "dielectric" "bool remaproughness" false "texture roughness" "n"`。
- 和均匀的 `"float roughness"` 一样处理:`remaproughness` 必须是 false(适配器本来就是这条规矩),贴图的值就是 pbrt 的 α;Cycles 的 Glass 粗糙度 r 给出 α = r²,所以送 r = √max(0, α)。
- `uroughness`、`vroughness`(各向异性)、`normalmap` 报错。

## 我们的扩展:familymap

- 语法:

  ```
  Texture "n" "spectrum" "familymap" "string family" "f.npz" "string map" "c.exr"
      ["string wrap" ...] ["float uscale" ...] ...(同上的映射参数)
  Material "diffuse" "texture reflectance" "n"
  ```

- 含义:漫反射率走过一族光谱 R(λ; c),c 由一张浮点图给(c 就是图的值,不乘 `scale`、不反相)。
  - 用来放钴浓度(青花)、沁色的浓度(开片)、墨在纸上的浓度、珐琅的颜色。
- `f.npz`:`lambda_nm` (K,)、`c` (N,) 严格升序、`R` (N, K) 在 [0, 1]。
- `rgbscene` 把每个成员按现在处理反射率的办法投影:通道平均,权重是传感器 × 主光(`--key-K`)。写成 N×3 的表,放进 JSON(`reflectance_family`)。
  - 光谱范围盖不住传感器 × 主光的权重(外面超过 0.5%)就报错,不当成 0 悄悄算。
  - pbrt 的 PiecewiseLinear 语义,样本之外是 0。
- `cycles_scene` 在 c(u,v) 处查表:表是一张小浮点图,线性插值;c 在 [c₀, c_{N−1}] 之外取端点。
  - c 的行等间距时,表原样放进去,是精确的。
  - 不等间距时,重采样成 4096 行(分段线性函数,重采样误差只在拐点),最坏误差打印在日志里;测试里的一族是 1.4e-5。
- 这条路径一次反弹是精确的,和别的反射率一样(多次反弹的颜色误差见 DESIGN §5)。
- pbrt(S3,`patches/pbrt-v4-gewu.patch`,`FamilyMapSpectrumTexture`):读同一个 `f.npz`(numpy 的 `np.savez`,不压缩;zip64 也认)和同一张图;按采样的波长在 λ 上线性插值(表外为 0,和 PiecewiseLinear 一样),在 c 上线性插值,c 在两头外取端点。`scale`、`invert` 报错。验证:`tests/qinghua/check_coat.py` 的块 B(一族红色底罩吸收层)对 1-D 解析 0.999–1.011。

## 加一个新材质

- `rgbscene.material()` 里加一个分支,写它的 JSON;`cycles_scene.material()` 里加一个分支,搭节点。
- 要 UV 的材质,`cycles_scene` 里用 `float_texture()` 取值;`family_colour()` 是查表的例子。

## 测试

在 `tests/textures/`,用 `python3 -I` 跑;每个有 `gen_*.py`(场景)、`run_*.py`(推送渲染,排队,拉回)、`check_*.py`(数字)。渲染在 `out/textures/`。pbrt 在 CPU 上,Cycles 在 GPU 上。预览质量:960×540,64–128 spp。

### a. 凹凸(`gen_bump.py`、`check_bump.py`)
- 场景:平的、光滑的介质板(n 1.5),高度 h = A·sin(2πx/P),P = 4 mm,斜率幅度 A·k = 0.05(A = 0.0318 mm;图里存 sin,`scale` 给 A);小面光(60 mm 宽,1 m 远,偏离镜像 30 mm,所以条纹不对称);相机 300 mm 远,在镜面角附近,36 mm 宽。
- 对照有三个:pbrt、Cycles、几何光学(逐像素光线、凹凸后的法线、镜面方向、是否打到灯,4×4 子像素)。13 条条纹,周期 107 px。
  - 条纹中心:pbrt 对几何 平均 0.05 px,最大 0.16 px;Cycles 对几何 平均 0.06 px,最大 0.16 px;pbrt 对 Cycles 平均 0.02 px,最大 0.03 px。
  - 条纹宽度比(a/b):pbrt 对 Cycles 平均 1.001(0.996–1.004);Cycles 对几何 1.000(0.997–1.003)。
  - 剖面的相关:pbrt 对 Cycles 0.9999;均值比 1.001。
- 同一个测试里还有三个变体,都对几何光学:
  - 板换成带 `u`、`v` 的 plymesh:两个渲染器的条纹都和 quad 的一样(0.05–0.06 px)。
  - 贴图换成 16 位 PNG(0.5 + 0.5 sin,`scale` = 2A,`encoding` linear):pbrt 平均 0.08 px、Cycles 0.06 px;pbrt 的宽度比最差 0.956(PNG 量化的 1e-5 台阶影响了窄条纹的边)。
  - 零高度图和不贴:pbrt 逐像素相同(最大差 0);Cycles 最大差 2.4e-7(浮点)。
- 薄介质上的凹凸只在 Cycles 里试了一次,条纹对几何光学最大差 0.15 px,和 pbrt 没比。
- 只测了斜率 0.05 这一档,没测大斜率。
- 图:`out/textures/bump/stripes.png`。

### b. 粗糙度图(`gen_rough.py`、`check_rough.py`)
- 场景:同样的板,α 的阶跃图,x < 0 一半 0.03,x > 0 一半 0.10;灯 120 mm 宽,镜像位置。变体:阶跃图、均匀 0.03、均匀 0.10。
- 逐列剖面(行平均),阶跃两边各 3 mm 不算,只算高光在亮处的列(373 列):
  - Cycles:阶跃的每一半对相应的均匀渲染,比值 1.0000(均方差 0.0000);pbrt 一样。同一个种子,两边的采样一样,所以是逐位相同,不是噪声里的一致。
  - 检验有分辨力:拿错的均匀 α 去比,比值 0.28 和 3.8。
  - pbrt 对 Cycles(三个变体、两半):总和比 1.0012,逐列比值的均方差 0.0004–0.0016。(这 0.12% 是两个渲染器的差,不是纹理的。)
- 图:`out/textures/rough/profiles.png`。

### c. 族(`gen_family.py`、`check_family.py`)
- 场景:两块平的漫射板,两盏侧灯,相机正上方。每块的反射率是一族光谱:R = 0.9·exp(−c·κ(λ)),κ 是 600 nm 的吸收带(编的一族,不是实测材料)。
  - 板 A:c 的行不等间距(9 行,0–2),斜坡存成 EXR(半精度),从 −0.3 到 2.3,两头超出;
  - 板 B:c 等间距(11 行,0–1),斜坡存成 PFM,从 −0.2 到 1.3,两头超出。
- 逐列:族的渲染除以同光照、反射率 0.5 的渲染(同一个种子,光照的噪声在比值里消掉),乘 0.5,应当等于表在 c(u) 处的插值。c(u) 从存下的斜坡文件读回来。
  - 对 JSON 里的表:板 A 绝对误差均方 R、G、B = 2e-5、1e-5、0,最大 3.1e-4;板 B 1e-5、1e-5、0,最大 1.5e-4。相对最大 0.04%。
  - 对本测试里从光谱重算的表(传感器 × 5500 K 黑体,独立于 `rgbscene` 的函数):数字相同,所以投影也对。
  - 两头被夹住的列(板 A 各 38 列,板 B 45 和 72 列)也对。
  - 换一个种子(噪声不消):均方 0.0012–0.0020,偏差 ≤ 4e-5,即只有噪声。
  - 沿斜坡的信号变化:板 A R、G、B 0.73、0.51、0.31;板 B 0.54、0.34、0.18。
- 图:`out/textures/family/ramps.png`。

### d. 回归(`run_regress.py`、`check_regress.py`)
- 旧的 `cycles_scene.py`(git HEAD)和新的,同种子、同 spp(32)、480×270,在 GPU 上:
  - 第 19 镜 `out/19/shot2/f05.cycles.json`(`lobe.ply`、`inlay.npz`):同种子的差最大 3.6e-7(均值 4.7e-9),图均值 0.12;
  - 第 6 镜 `out/06/shot3/common/scene_f3.cycles.json`:最大 1.4e-4(均值 2.7e-8),图均值 2.2(这一帧有很亮的像素);
  - 对照:换一个种子,均方差是均值的 19%(第 19 镜)和 118%(第 6 镜,萤火虫)。
- 同种子的差是浮点级的(GPU 求和顺序),约 47–64% 的像素有 1e-7 量级的差,没有系统差(带符号均值 1e-10 量级)。没有测旧的跑两次是不是逐位相同。
- 相同的 JSON:旧的 `rgbscene.py` 和新的对 `out/19/t1/scene.pbrt`、`out/06/lk_150s/scene.pbrt` 写出的 JSON 逐字节相同。

## 没做的

- MIP 级的选择(见上)、`remaproughness` 为 true 的玻璃、各向异性粗糙度、法线贴图、圆盘的 UV、非 `uv` 的映射。
- 带 `displacement` 的材质不能同时用 `nacreinlay`。
- Blender 的 Bump 节点的 `Filter Width` 用默认值,没有调。
