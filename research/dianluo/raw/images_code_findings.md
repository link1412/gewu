# Reference photographs and code metadata (incremental findings)

Tags: [M] museum-record dimensions/first-party metadata; [D] secondary-source statement or visible-photo reading; [I] inference. No optical measurements are implied by museum metadata.

## Confirmed high-relevance image references

| Museum/object | Title/date | Dimensions | Rights | Image/download status | Layout |
|---|---|---|---|---|---|
| The Met, 91.1.672 | Box with Geometric Designs; China; late 17th century, Qing [M] | H 2.9 cm; diameter 7 cm [M]. Separate body and lid heights: not found. | Object page labels image Public Domain [M]; Met Open Access policy confirms CC0 for public-domain collection images. | Largest offered image endpoint located: https://collectionapi.metmuseum.org/api/collection/v1/iiif/60912/140857/main-image . Download blocked by execution environment network restriction; no image file saved. | Museum explicitly describes five geometric patterns of exceptionally small thin shell fragments on black lacquer [D]. Visual doming/layout not verified from pixels. |
| The Met, 64.32a,b | Round Box; China; Ming dynasty (1368–1644) [M] | H 10.2 cm; diameter 28.6 cm [M]. Separate body and lid heights: not found. | Public Domain on object page [M]. | Largest offered image endpoint located: https://collectionapi.metmuseum.org/api/collection/v1/iiif/60978/130217/main-image . Download blocked by execution environment network restriction; no image file saved. | Round box is confirmed by title [M]; thin-shell attribution, detailed motif and doming: not found in parsed museum record. |

Sources opened and verified:
- https://www.metmuseum.org/art/collection/search/60912 (The Met collection record; includes note that pearl fragments were sometimes tinted or painted on their reverse to enhance pink/green, a general historical statement rather than technical examination of this object [D]).
- https://www.metmuseum.org/art/collection/search/60978 (The Met collection record).
- https://www.metmuseum.org/hubs/open-access (policy page reached through museum object record).

## Other institutions attempted

- Cleveland Museum of Art https://www.clevelandart.org/art/1975.10 : Chest for Storing Garments, China, Ming, 1400s; lacquered wood with mother-of-pearl inlay; overall 43 × 56 × 54.7 cm [M]. Rectangular chest rather than target round box [I]; not selected for download before network blocker.
- Smithsonian NMAA https://asia-archive.si.edu/object/S1987.407a-b/ : Octagonal Box (Ba jiao bang he) [M]; archive page explicitly says “Usage conditions apply” [M]. CC0 status not confirmed, so not treated as an open image.
- Rijksmuseum search returned AK-MAK-179, but record identifies it as Korean, 1400–1500, so excluded from Chinese-object reference set [M]: https://www.rijksmuseum.nl/en/collection/object/Box--ebc4dd12079fa512dfb119577e8653cd .
- Palace Museum lead 黑漆嵌螺钿五子夺魁图圆盒: https://www.dpm.org.cn/collection/lacquerware/232052.html . Full page timed out; not confirmed beyond search result, so do not use as verified object metadata.

## Download blocker

No claim that images were downloaded.

## Code metadata only

- Steven J. Byrnes, **tmm**: PyPI latest release **0.2.0**, uploaded **26 November 2024**, **MIT licence** [M: first-party package metadata]. Opened https://pypi.org/project/tmm/ and https://github.com/sbyrnes321/tmm . Package describes planar multilayer transfer-matrix calculations of interference, reflection, transmission and position-dependent absorption, and combinations of coherent thin and incoherent thick layers [M: package description]. No package/code downloaded or run.
- A verified public code release for a **nacre- or pearl-specific appearance model**: **not found** in the allocated search. The first-party article page for Wakabayashi, Asai & Yamakita, *Numerical Analysis of Structural Coloration of Dark Color Pearls by Nacre Crystal Multilayers*, JASSE 12(1), 152–163 (2025), DOI https://doi.org/10.15748/jasse.12.152 , exists at https://www.jstage.jst.go.jp/article/jasse/12/1/12_152/_article/-char/en ; the abstract describes a 4×4 Maxwell matrix using permittivity tensors [A]. Public code/license/release: not found; do not equate article availability with code availability.

### Later checks / correction

- Met Open Access policy was fully opened: it explicitly assigns CC0 to public-domain artwork images and basic object data [M].

- **Image resolution caveat:** the two Met URLs above are the museum page's offered `main-image` links, not downloaded byte streams; the largest available dimensions could not be confirmed. Interpret “largest offered” in the earlier rows as “main-image endpoint”, not a verified resolution.
- Cleveland page explicitly permits copying, modification and distribution without permission [M]; its own supplied image description says the lid is rounded, and front/top/sides show scholar scenes, with metal-stud borders [D].
- Smithsonian archive S1987.407a-b: China, Qing, 17th–18th centuries; lacquer on wood with mother-of-pearl, silver and gold; H × W × D = 25.2 × 25.1 × 24.7 cm [M]. Page labels scholars, garden and children scenes on lid top and lower side panels, scholarly implements on raised foot [D]. The parsed page includes both CC0 and restrictions text, apparently shared UI blocks; active heading and SI Usage Statement say Usage Conditions Apply [M]. Therefore licence unresolved; do not silently label CC0.
