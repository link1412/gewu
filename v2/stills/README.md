# v2/stills

每镜一个脚本。说明是脚本开头第一句,原样摘的。逐镜的做法见 `docs/FILM.md`。试一镜:`python3 v2/stills/sNN_名字.py preview|mid|final`,结果在 `out/v2/sNN_名字/`。要和片子一样的帧,用 `python3 v2/render_film.py 镜名`:每镜进片时的参数写在那里,见 `docs/RENDER.md`。

脚本名带 `_v1` 的是进片时的版本,同名不带 `_v1` 的是后来改的,不进片。备选和没进片的镜头留着脚本,它们的渲染结果不在仓库里。

## 进片的镜头和它们用到的模块(70)

| 脚本 | 镜 | 说明 |
|---|---|---|
| `chanzhi_v1.py` | 珐琅 | 缠枝 (scrolling vine) ornament for cloisonne, in flat cm around a centre: reusable by any dish or by a jar's fla |
| `diancui_shader.py` | 点翠 | Kingfisher feather and old silver-gilt on one mesh (s55). The feather's colour is an angle-dependent reflectio |
| `falang_shader.py` | 珐琅 | Enamel, gilt wire, open air and glass that light comes through, in one surface. |
| `glaze_shader_v1.py` | 曜变、豇豆红 | Shaders for glazed ware with a real medium, as they were when s11_jiangdou's frame was rendered. |
| `yohen_shader_v1.py` | 曜变 | Shaders for the yohen glaze, as they were when s02_yaobian's frames were rendered. |
| `glazekit.py` | 钧窑 | Geometry helpers for glaze in a real medium (shots 29, 6, 11, 26, 28). |
| `nacre_shader.py` | 螺钿 | Shell inlaid in lacquer, under a polished coat. The colour of the shell is not painted: it is interference, an |
| `pearl_shader.py` | 南珠 | A pearl's skin, in three parts (see s36_nanzhu.py for the numbers and where they come from): |
| `s02_yaobian.py` | 曜变 | Shot 2: yohen tenmoku, 曜变天目, close on the far wall: the rim is the arc, the wall a night sky under black glass |
| `s05_yinni.py` | 印泥 | Shot 5: cinnabar seal paste (朱砂印泥) heaped in a white porcelain box; the top of the heap is the arc. |
| `s06_flow.py` | 钧窑 | The glaze of shot 6 as it fired: a raw layer that cracked as it dried, a loaded copper stroke on top, and then |
| `s06_junyao.py` | 钧窑 | Shot 6: Jun ware (钧窑), the inside of a bowl close up, over its near side. The far rim is the arc, the glaze ru |
| `s07_cijing.py` | 磁青 | Shot 7: 磁青纸泥金写经. Gold paint on indigo paper: real small regular script, the Heart Sutra in Xuanzang's translat |
| `s09_ginkgo.py` | 银杏 | Shot 9, moving: a golden ginkgo leaf against low sun, a breath of wind goes through it. The old still and its  |
| `s09_leaf.py` | 银杏 | Shot 9, the leaf itself: tissue and sheet for the moving ginkgo. Used by s09_ginkgo.py; nothing here renders.  |
| `s09_shader.py` | 银杏 | The ginkgo blade: a thin sheet that scatters most of the light forward, tinted by its pigment (the path throug |
| `s09_yinxing.py` | 银杏 | Shot 9: a golden ginkgo leaf against low sun, dark trees far behind. The fan's margin is the arc. |
| `s11_jiangdou.py` | 豇豆红 | Shot 11: the low dome of a peachbloom (豇豆红) seal box lid, Kangxi: the crest of the dome is the arc. |
| `s14_datiehua.py` | 打铁花 | Shot 14: 打铁花, from inside the sparks. No people, no ground: only flying iron and the night. 24 frames. |
| `s15_open.py` | 折扇 | Shot 15, the fan opening: the motion of the sticks and the skin that hangs the same paper, gold and sticks fro |
| `s15_zheshan.py` | 折扇 | Shot 15: a whole folding fan, sprinkled with gold, standing open with the light behind it. Its top edge is the |
| `s16_lizhi_v1.py` | 荔枝 | Shot 16: a lychee against the light; the top of the fruit is the arc. |
| `s19_luodian.py` | 螺钿竹 | Shot 19: mother-of-pearl inlay in black lacquer (黑漆嵌螺钿): bamboo on a round tray. The rolled rim of the tray is |
| `s20_denglong.py` | 红灯笼 | Shot 20: the shoulder of a red silk lantern at night, glowing from inside. The silhouette of the shoulder is t |
| `s20_shader.py` | 红灯笼 | A stretched silk: most of the light from inside is scattered through it, and it scatters forward. |
| `s21_lib.py` | 折扇、油纸伞、油纸伞·黑 | Helpers shared by shots 21, 15, 34, 39, 40, 31, 16. |
| `s21_youzhisan.py` | 油纸伞 | Shot 21: a whole oil-paper umbrella, open, tipped towards the sun, seen from underneath in a bamboo grove. Its |
| `s24_jianzhi.py` | 剪纸 | Shot 24: a white paper-cut (团花) lying on indigo home-woven cloth; its round edge is the arc, its shadow falls  |
| `s24_wind.py` | 剪纸 | Shot 24: a light wind skims the blue cloth and the paper-cut answers. Writes a displacement stack for kit/stud |
| `s27_jinbo.py` | 金箔 | Shot 27: a sheet of gold leaf (金箔) lying over a soft mound, its torn far edge the arc, the edge trembling in a |
| `s28_dehua.py` | 德化白瓷 | Shot 28: Dehua white porcelain (德化白瓷, blanc de Chine), the drapery of a Guanyin at the shoulder: the shoulder  |
| `s28_shader.py` | 德化白瓷 | Dehua glaze for shot 28: glaze_shader's closed shell with a real medium, plus glaze pooled in the recesses: th |
| `s30_huali.py` | 黄花梨 | Shot 30: oiled huanghuali (黄花梨) with its "ghost faces" (鬼脸): rings swirling around knots. The curve of a turne |
| `s35_kuangcao.py` | 狂草 | Shot 35: one stroke of wild cursive (狂草) on gold-flecked paper (洒金笺); the outer edge of the stroke is the arc. |
| `s36_nanzhu.py` | 南珠 | Shot 36: a South Sea pearl from Hepu (合浦南珠): the sphere's edge is the arc. Grey-black room, a window, slow. |
| `s37_jinyu.py` | 金鱼 | Shot 37: the tail of a red goldfish, lit from behind in black water. Its rays fan out towards the sunrise of s |
| `s37_shader.py` | 金鱼 | A goldfish fin: a thin sheet that scatters a little of the light and lets the rest through, tinted by its pigm |
| `s38_richu.py` | 墨晕、日出 | Shots 1 and 38: an ink painting of a dawn on xuan paper, photographed on a light table. The lamp behind it ris |
| `s39_cand.py` | 荷花 | Shot 39, the candidate: a lotus half open against the sun, in the leaf field, opening a little. s39_hehua.py i |
| `s39_hehua.py` | 荷花 | Shot 39: a lotus half open against the sun, in the leaf field. The top of the flower is the arc. |
| `s39_petal.py` | 荷花 | One lotus petal for s39_cand.py: a coarse surface that can be posed, and its maps, drawn in the plan of the pe |
| `s39_wind.py` | 荷花 | The flower opens a little, for s39_cand.py. Nothing here renders. (The file keeps its name: it began as wind,  |
| `s45_flick.py` | 孔雀羽 | Shot 45, the breeze: one light, steady air along the barbs, in one direction, and they lie over with it. Used  |
| `s45_kongque.py` | 孔雀羽 | Shot 45: the eye of a peacock's train feather. The tips of its barbs make the arc against black. |
| `s45_shader.py` | 孔雀羽 | Barbules of a peacock feather: coloured mirror on a dark melanin ground (shot 45). |
| `s46_luopan.py` | 螺钿 | Shot 22: a black lacquer dish inlaid in thin mother-of-pearl (薄螺钿), magpies on a flowering plum, seen from abo |
| `s49_falang_v1.py` | 珐琅 | Cloisonné (景泰蓝) plate from above: a turquoise ground, a scrolling vine of fan-lotus heads round a medallion, i |
| `s50_qinghua.py` | 青花 | Blue and white (青花), a large early Ming dish seen at a slant: the far lip is the arc, a window lies on the cav |
| `s50_shader.py` | 青花 | The glaze of s50: the same model as s52_shader (written there by the ru group), a copy here because shader_py  |
| `s52_shader.py` | 钧窑 | The glaze of s52: as glaze_shader's `glaze` (closed shell, transparent + Fresnel gloss, real scattering and ab |
| `s54_zoumadeng.py` | 走马灯 | Shot 14: a trotting-horse lantern (走马灯) seen from below, its top rim the arc; the shadows of paper horses gall |
| `s55_diancui.py` | 点翠 | Shot 17: diancui (点翠), macro. The rim of a flat gilt plaque is the arc; below it the tips of kingfisher-feathe |
| `s59_silk.py` | 苏绣 | Shot 59: Suzhou embroidery as a good hand does it: peonies, leaves, a butterfly on indigo satin stretched in a |
| `s59_suxiu.py` | 苏绣 | Shot 59: Suzhou embroidery (苏绣): a round silk fan (团扇) with a peony, a bud and a butterfly, lying flat and til |
| `s61_tihong.py` | 剔红 | Shot 61: tihong (剔红), a Yongle-style carved red lacquer dish with one big peony. Its far lip is the arc. |
| `s63_chain.py` | 南红 | The strand's dynamics for shot 63 (南红念珠): a real simulation in numpy, no key frames. Units: cm, s, grams. One  |
| `s63_nanhong.py` | 南红 | Shot 63: a strand of southern red agate (南红念珠) let down on black lacquer by two hands out of frame. It hangs a |
| `s66_xieyang.py` | 油纸伞 | Shot 66: the oil-paper umbrella from below and to one side, turning, the sun coming through its paper. Its far |
| `s68_flow.py` | 一滴 | Shot 68, the flow: concentrated tea sinking in still hot water. 3D incompressible Boussinesq flow, pseudo-spec |
| `s69_crack.py` | 木炭 | Shot 69 (charcoal): the cracks, grown instead of drawn. Variational phase-field fracture of a shrinking skin,  |
| `s69_heat.py` | 木炭 | Shot 69 (charcoal): the temperature is solved, not painted. A surface energy balance on a coarse mesh of every |
| `s69_mutan_raw.py` | 木炭 | Shot 69: a heap of burning charcoal, through a long lens, wide open. Replaces s67_mutan. One piece alone could |
| `s69_pile_bpy.py` | 木炭 | Run inside Blender: pour the coals with Bullet and write where they came to rest. s69_mutan.py calls it. |
| `s69_shader.py` | 木炭 | Shader for s69_mutan: Principled driven by vertex attributes, no light sampling of the emissive surface. |
| `s69_shell.py` | 木炭 | Shot 69 (charcoal): a piece of charcoal as a real solid. An implicit field in shell coordinates, meshed with s |
| `s73_heisan.py` | 油纸伞·黑 | Shot 73: the oil-paper umbrella in a dark room, lit from behind, seen from inside the dome at the v1 camera. I |
| `s76_yidi.py` | 一滴 | Shot 76, 一滴: one drop of ink opening in clear water, as when a brush is rinsed in a brush washer, seen from th |
| `translib.py` | 折扇、油纸伞、油纸伞·黑 | What the light-through shots (s21, s16, s15, s40) share: smooth tubes and strips as triangle soups, bamboo and |
| `yohen.py` | 曜变、豇豆红 | The yohen glaze, shared by s02 (close) and s47 (from above). Everything is painted in a Dish's flat coordinate |
| `yohen_shader.py` | 曜变 | Shaders for the yohen glaze (s02, s47). Selected by params["kind"]. |

## 备选,撤出了片子(15)

| 脚本 | 说明 |
|---|---|
| `s03_tianhuang.py` | Shot 3: a pebble of tianhuang (田黄), honey-coloured field stone. Rebuild: the old version had nothing in fo |
| `s04_zisha.py` | Shot 4: the shoulder of an old zisha teapot, pear-skin clay (梨皮), with the seam of the lid running in from the |
| `s08_qingtingyan.py` | Shot 8: a Warring States eye bead (蜻蜓眼琉璃珠). Rewritten against photographs (the earlier version read as rolled  |
| `s13_guqin.py` | Shot 13: the top of an old qin (古琴) with its crackle (断纹): snake-belly bands, silk strings and a |
| `s18_jiagu.py` | Shot 18: an oracle bone (甲骨): a turtle plastron, its swell the arc, with burn marks, cracks and cut signs. |
| `s23_jingtailan.py` | Shot 23: cloisonné (景泰蓝) as a macro: nothing but a few gilt wires and the worn enamel between them, on the dom |
| `s26_qinghua.py` | Shot 26: blue and white (青花), early Ming, a jar's shoulder: the shoulder's crest is the arc, one strong spray  |
| `s34_canjian.py` | Shot 34: a silk cocoon against the light. The shoulder of the ellipsoid is the arc. |
| `s40_chanyi.py` | Shot 40: a cicada's fore wing close to its base, where the veins are dense, against the leaves in the sun; the |
| `s41_feicui.py` | Shot 41 (spare): an imperial-green jadeite cabochon (翡翠蛋面, 玻璃种帝王绿): the dome's crest is the arc. |
| `s42_yaohuo.py` | Shot 42: the door of a wood-fired kiln (柴窑窑门) at full fire: the static plate of the masonry. The fire itself i |
| `s47_yaobian.py` | Yohen tenmoku (曜变天目), a whole tea bowl from above, standing on linen: its far lip the arc, most of the inside  |
| `s52_ruyao.py` | Ru ware (汝窑), a shallow six-lobed washer from above: it rises from the bottom of the frame, the crown of its f |
| `s56_yunjin.py` | Shot 19: Nanjing brocade (云锦) laid flat, a roundel of pearls (联珠团窠) woven into an indigo satin; the gold borde |
| `s64_heye.py` | Shot 64: one lotus leaf floating on pond water in the midday sun, seen from nearly straight above (荷叶). The na |

## 没进片的镜头和旧版本(66)

| 脚本 | 说明 |
|---|---|
| `chanzhi.py` | The ornament of the later s49_falang.py. |
| `s49_falang.py` | A later cloisonné plate. The film's is s49_falang_v1.py. |
| `s06_copper.py` | The purple of Jun ware as what it is, shot 6: copper brushed on the raw glaze, which then melts and runs. Sets |
| `s08_shader.py` | Shaders for shot 8. params["kind"]: shell is the skin of clear glass above the pattern: Fresnel gloss over a s |
| `s10_tixi.py` | Shot 10: tixi (剔犀): a round box of layered lacquer carved in scrolls (屈轮). The far rim of the box is the arc. |
| `s12_mirror.py` | Shot 12: the back of a Western Han 'light of the sun' bronze mirror (日光镜), rim and inscription band. |
| `s16_lizhi.py` | Shot 16: a small bunch of lychees on the tree, close enough to read the peel. The top of the near fruit is the |
| `s16_peel.py` | The peel of a lychee, shot 16 only. Built from what photographs show at 100% (leidus_lychee_fruits_and_seed, l |
| `s17_diancui.py` | Shot 17: diancui (点翠): kingfisher feather set in gilt filigree. The rim of the ornament is the arc. |
| `s21_sheets.py` | Shared shader_py for shots 21, 15, 34, 39, 40, 31, 16 (make(name, params), run inside Blender by studio_bpy). |
| `s22_yunjin.py` | Shot 22: Nanjing brocade (云锦): gold and silk floats, thread by thread, over a bolster whose swell is the arc. |
| `s25_nanhong.py` | Shot 25: southern red agate (南红玛瑙), persimmon red: a polished pebble, its crest is the arc. Rebuild with t |
| `s27_float.py` | Shot 27, third version: one sheet of gold leaf (金箔) borne up on rising air, edges curled, slowly undulating. R |
| `s27_shader.py` | Gold leaf for s27 (make(name, params), run inside Blender by studio_bpy): a real conductor with complex IOR, p |
| `s29_ruyao.py` | Shot 29: Ru ware (汝窑), a shallow dish seen over its near side: the far rim is the arc, the wall below it the s |
| `s31_piying.py` | Shot 31: a piece of a shadow puppet's robe, pressed against the lit white screen. Its curved hem is the arc. |
| `s32_zhu.py` | Shot 32: a transverse section of bamboo culm under a bright-field microscope, safranin and fast green. The fie |
| `s33_chensha.py` | Shot 33: cinnabar (辰砂) crystals on white dolomite. The tops of the cluster make a rough arc. |
| `s39_shader.py` | A living petal, for s39_cand.py: reflected light with a velvet sheen, light scattered through the tissue, and  |
| `s40_shader.py` | A cicada's wing close to its base, shot 40. Runs inside Blender. Membrane and veins are one sheet, as they are |
| `s42_fire.py` | Shot 42: real moving fire. A 3D buoyant reacting flow solved on the GPU, then ray-marched through the shot's c |
| `s42_geom.py` | Shot 42: the door and the camera, shared by the plate (s42_yaohuo.py, Blender) and the fire (s42_fire.py, torc |
| `s43_heye.py` | Shot 43: water on a lotus leaf (荷叶水珠). The rim of the leaf is the arc; the beads are real refractive water. |
| `s44_lizhi.py` | Shot 44: lychee, frame-filling macro. A crimson jewelled crust as the arc, glowing cream flesh in great soft s |
| `s46_close.py` | Shot 22: a black lacquer dish inlaid in thin mother-of-pearl (薄螺钿), close: a magpie on a plum branch, the dish |
| `s47_close.py` | Yohen tenmoku (曜变天目), the second time in the film: close on the far wall like s02, from higher and further int |
| `s48_jiangdou.py` | Peachbloom (豇豆红), a shallow brush washer from above: it rises from the bottom of the frame, its far lip the ar |
| `s49_juancao.py` | s49, scrolling leaf (卷草) in openwork cloisonne: the old plate's gilt lip, wire and enamel, no flower heads, no |
| `s49_yulin.py` | s49: plique-a-jour (空窗珐琅) carp flank, macro. No body, no backing: gilt wire and glass, light from behind. |
| `s52_cand.py` | Ru ware (汝窑), a shallow six-lobed washer from above, second version: a real medium with the crackle as sheets  |
| `s54_shader.py` | Two materials for the lantern. |
| `s57_huali.py` | Shot 30: a turned huanghuali (黄花梨) dish seen from above, its ghost faces (鬼脸) across the well; the far lip is  |
| `s58_heye.py` | Shot 58: a lotus leaf floating on the pond (荷叶), seen from nearly straight above. The navel sits at the foot o |
| `s59_he.py` | Shot 59: one spread wing of a crane, Suzhou embroidery on dark satin, seen near. The wing's leading edge is th |
| `s59_silk_shader.py` | Silk floss, thread by thread, and its satin ground. |
| `s60_lizhi.py` | Shot 16: a lychee cut through, frame-filling: a thin crimson crust is the arc, below it glassy white flesh in  |
| `s62_quanyi.py` | Shot 62: the round back of a Ming armchair in huanghuali (黄花梨圈椅), three-quarters and a little above: the whole |
| `s62_shader.py` | Polished old wood, shot 62: runs inside Blender. |
| `s62_wood.py` | Huanghuali as a solid: what a straight log of it shows where a surface cuts it. Used by s62_quanyi only. |
| `s63_shader.py` | Shaders for shot 63. Selected by params["kind"]. Everything is evaluated per pixel in the bead's own frame, so |
| `s64_water_shader.py` | Pond water seen from above: a mirror by Fresnel on the real, rippled surface, over the light that comes back o |
| `s65_shader.py` | Shaders for shot 65. params["kind"]: |
| `s65_zhuansan.py` | Shot 65: the oil-paper umbrella from above, turning in the hand. A long lens from an upper floor looks down on |
| `s67_mutan.py` | Shot 67: burning hardwood charcoal, through a macro lens. Stands in for the kiln fire. |
| `s67_shader.py` | Shaders for s67_mutan. |
| `s68_align.py` | Shot 68: does the compositor's refraction agree with Cycles? Black beads under the water in a render (s68_chas |
| `s68_chase.py` | Shot 68: tea going into water, in a backlit eggshell-thin white cup. The only fluid in the film. |
| `s68_comp.py` | Shot 68: tea particles through the flat water surface, to the screen. Torch; runs on the GPU. |
| `s68_geom.py` | Shot 68, tea into water: the numbers shared by the cup, the flow and the compositor. Numpy only; 1 unit = 1 cm |
| `s68_shader.py` | Shot 68: the cup and the water, in the two passes that the compositor needs. |
| `s68_tea.py` | Shot 68: what tea does to light, per wavelength band. eps = relative absorbance, 1 at 450 nm; K_abs (composito |
| `s69_air.py` | Heat shimmer over the burning heap, on the take's scene-linear frames. NOT IN THE PIPELINE: at the bending est |
| `s69_mutan.py` | Shot 69: a heap of burning charcoal, through a long lens, wide open. Replaces s67_mutan. One piece alone could |
| `s70_chatang.py` | Shot 70: tea spreading in a clean white bowl, from low down and lit from behind. Replaces s68_chase (white cup |
| `s70_flow.py` | Shot 70, the flow: tea leaving lumps of pressed tea, just out of frame, in a bowl of hot water that is still t |
| `s70_shader.py` | Shot 70: the water's surface and the tea. |
| `s70_vdb.py` | Shot 70: the solver's grids to an OpenVDB file, run by Blender's own Python (its openvdb is the one Cycles rea |
| `s71_liuli.py` | Shot 71: tea bleeding into clear water in a glass tea bowl, seen nearly from the side with the liquid lit from |
| `s71_shader.py` | Shot 71: the glass, the water and the tea. Interfaces are told apart by the side a ray hits, so one mesh can h |
| `s72_chawan.py` | Shot 72: tea leaving a chip of pressed Pu'er in a white porcelain tasting bowl, from above, in hard sun. The s |
| `s74_flow.py` | Shot 74's flow: a viscous film running down the ball. Thin-film (lubrication) equation on the ball's surface,  |
| `s74_shader.py` | Shot 74's two surfaces. Selected by params["kind"]. |
| `s74_steam.py` | Shot 74's steam: added to the scene-linear image behind the ball, before developing. No render, no GPU. |
| `s74_tangyuan.py` | Shot 74: a boiled tangyuan that has split at the shoulder, a tongue of black sesame filling running down its s |
| `s75_shader.py` | Shot 75: the sugar. A clear solid that absorbs by how far light crosses it, so that it stays pale where thin a |
| `s75_tanghulu.py` | Shot 75: 糖葫芦, a still. SHELVED after the last version: not in cut.json, not in the film. |

## 其他公共模块和着色器(12)

| 脚本 | 说明 |
|---|---|
| `dishkit.py` | Dishes and bowls seen from above: paint in flat coordinates, then lay the paint on a turned surface. |
| `gem_shader.py` | A clear crystal with a real medium (shot 33): a closed solid, true refraction and absorption per channel, sigm |
| `glaze_shader.py` | Shaders for glazed ware with a real medium (shots 29, 6, 11, 26, 28). Selected by params["kind"]. |
| `lotuslib.py` | What the lotus shots share: the sheet shader, the sky over the pond, the far leaves and the water. All far out |
| `plastron_shader.py` | Water standing on a lotus leaf: smooth on top, rough underneath, with dirt in its underside. |
| `plique_shader.py` | Shaders for the plique-a-jour carp (s49_yulin). |
| `softsheet_shader.py` | A translucent sheet that may also let some light straight through: oiled paper, a thin leaf, a wing. |
| `stonelib.py` | Translucent stones as a stack of real depth layers, baked per vertex (石、珠、果组; used by s03, s25). |
| `thinsheet_shader.py` | A thin living sheet, a petal or a leaf: a surface that reflects (`col`, with its own gloss and sheen) mixed wi |
| `vessel.py` | Helpers for the vessel stills (shots 4, 5, 6, 11, 23, 26, 28, 33): turned profiles, framing on the arc, g |
| `water_shader.py` | Clear water: a real refracting surface, smooth shaded. Used for drops. |
| `wing_shader.py` | An insect wing's membrane: clear, so the blurred world shows through it, with a gloss on top that carries a th |
