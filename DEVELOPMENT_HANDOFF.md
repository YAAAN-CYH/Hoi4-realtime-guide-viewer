# 实时攻略查看器 Development Handoff

## Current Change

- Goal (2026-09-09): rebuild the image-to-topic mapping from the supplied PPT's
  slide text and media relationships, correcting the mislabeled tank destroyer
  and the SPG scope, and add accurate page-specific descriptions.
- Evidence and result: slides 48-80 and media `image116`-`image154` were audited
  from OOXML text, shape positions, and image relationships. The true TD on
  slide 56 (`image127`) is now first; slide-55 `image126`/`image125` are marked
  as medium-tank conversion references. `image119`/`image120` are both labelled
  light SPGs, matching slides 50-51. Missing aircraft designs `image146`,
  `image151`, and `image152` were restored, and mechanized/recon pages reordered.
- Goal (2026-09-09): fix gallery navigation resolving to
  `invalid event with id: MMG_guide.0000`, suppress navigation where no real
  adjacent image exists, and re-audit the event-window display and drag model.
- Root cause: `events/MMG_design_gallery_events.txt` used namespaced event IDs
  without declaring `add_namespace = MMG_guide` in that file. HOI4 1.19 logged
  every extra-page ID as a malformed token, so valid-looking next buttons
  resolved to the namespace's zero fallback.
- Repair: register the namespace in the generated extra-page file and its
  generator; retain boundary-aware previous/next generation; move the header
  artwork out of the engine-bound child section onto a transparent root-layer
  decoration so the single movable root owns all non-button drag input. The
  shared event-option entry was restored to the installed 1.19 contract so
  operative, leader, news, and ordinary event buttons are not globally resized.

- Goal (2026-09-08): add complete English localisation and rename the launcher
  display name to `实时攻略查看器` without changing the stable folder or IDs.
- Status: all 212 Simplified Chinese keys now have English counterparts across
  the main guide and design gallery. Both launcher descriptors use the new
  display name. English strings were shortened for the existing event layout.

- Goal (2026-09-08): rebuild the event images from the original
  `萌新向军备攻略 (1).pptx`, remove exterior black margins, and fit pictures,
  descriptions and every event option without overlap. The follow-up requires
  tank, ship and aircraft designs to display as complete individual panels.
- Status: original PPT media extracted and rebuilt; 1140x680 two-column event
  layout implemented. Static validation and offline preview checks pass;
  Design topics now have 21 additional previous/next pages, for 62 events and
  61 textures in total. No in-game run has been performed.
- Supported build and playset: HOI4 1.19 (installed game root used for schema
  checks); no DLC gate, standalone mod.
- Affected systems: decision categories, country decisions, triggered country
  events, event-picture GFX/DDS assets, an EventWindow GUI override, Simplified
  Chinese and English localisation.

## Change Map

| File | Reason | Contract or identifier affected |
| --- | --- | --- |
| `common/decisions/categories/MMG_guide_category.txt` | start-visible category | `MMG_guide_category` |
| `common/decisions/MMG_guide_decisions.txt` | seven chapter decisions | `MMG_*_decision` |
| `events/MMG_guide_events.txt` | menu/detail event chains | `MMG_guide.100`-`MMG_guide.706` |
| `interface/MMG_eventpictures.gfx` | custom sprite registry | `GFX_MMG_*` |
| `gfx/event_pictures/*.dds` | 61 event pictures from the guide/reference | texture files |
| `interface/eventwindow.gui` | 1140x680 popup with separate picture/option columns | `EventWindow` and shared option entry |
| `interface/MMG_eventwindow.gfx` | stretchable vanilla paper backgrounds | two MMG-only GFX definitions |
| `tools/rebuild_event_pictures.py` | reproducible PPT extraction, exterior trim, ordered packing and resampling | all 61 picture IDs |
| `tools/design_gallery.py`, `tools/build_design_gallery_patch.py` | PPT-verified semantic mapping, one image per page, stable IDs and navigation | 17 design topics and 21 extra pages |
| `events/MMG_design_gallery_events.txt`, `interface/MMG_design_gallery.gfx`, `localisation/simp_chinese/MMG_design_gallery_l_simp_chinese.yml` | generated extra pages and captions | previous/next/close/chapter-return |
| `tools/sources/tank_medium.png` | complete user-supplied medium tank screenshot | source override for image122 |
| `localisation/simp_chinese/MMG_guide_l_simp_chinese.yml` | all Chinese UI text | all visible keys |
| `localisation/english/MMG_guide_l_english.yml`, `localisation/english/MMG_design_gallery_l_english.yml` | full English UI text | all 212 visible keys |
| `descriptor.mod`, root `.mod` | launcher metadata | mod name/path |
| `README.md`, `TECHNICAL_GUIDE.md` | user + maintainer docs | this handoff |

## Decisions And Assumptions

- Category and decisions are global (`always = yes`) so the guide appears for
  every country from game start, matching the request.
- All seven decisions cost 0 PP and use `days_remove = 1`; the player can
  reopen a chapter one in-game day after clicking it.
- `坦克设计` opens a menu whose entries are exactly the guide's vehicle
  classes; every detail event's second option re-fires `MMG_guide.500`, which
  is the requested “回到第一项选择其他项” behavior. The same pattern is
  applied consistently to the other six chapters.
- Event pictures are 720x450 RGBA DDS files rebuilt directly from the source
  PPT at `D:/my program/1553960563/FileRecv/萌新向军备攻略 (1).pptx`.
  Continuous near-black exterior padding is trimmed. Interior dark tooltips
  are preserved. Images keep their aspect ratio and use transparent padding.
- Non-design multi-image pages use ordered row packing instead of a wide strip.
  Sources include full equipment panels previously cut off in legacy exports.
  Tank, ship and aircraft details now each use a single source image. Complete
  designs, partial UI illustrations, pre-conversion references, and related
  configurations have distinct labels and page descriptions.
  Tank, aircraft and ship complete-design examples were inspected in offline
  layout previews, with module rows, statistics and bottom costs preserved.
- The picture is (24,16), size 720x450, within the bottom section. The options
  start at (764,16); eight 352x56 slots fit without touching the picture.
  The guide grid uses 352x56 slots around the shared vanilla 300x47 option
  entry; labels retain the installed `hoi_20bs` font and 340x40 text bounds.
- Dragging contract (revised after 1.19 runtime report): merely disabling child
  `moveable` was insufficient because their backgrounds still captured mouse
  selection while the root used a transparent sprite. The root now owns a
  non-transparent 1140x680 hit background. Child section backgrounds were
  removed, the header artwork is now a transparent root decoration,
  decorative text/picture layers pass input through, and only
  the root remains movable. Option buttons remain clickable rather than
  draggable. This requires a fresh full game restart to validate because GUI
  hot reload can preserve stale controls.
- Ordinary non-MMG country events also use this global window override.
  Other window definitions are preserved, but share the resized option entry.
- Effective UI resolution should be at least 1280x720. Static previews use
  conservative YaHei font metrics and do not prove engine positioning or
  font rendering at arbitrary game UI scaling.
- Simplified Chinese and English localisation are bundled with identical key
  sets. Screenshots remain in their source language because text inside DDS
  pixels is not controlled by localisation files.

## Validation Evidence

- Pre-fix runtime evidence: the 2026-09-08 `error.log` contains 17
  `Malformed token` errors, one for every extra gallery-page ID in
  `MMG_design_gallery_events.txt`. This directly explains the observed
  `MMG_guide.0000` fallback. A fresh post-fix game log is not yet available.
- Event graph audit: 62 definitions and 131 jump targets; no missing targets.
  Every first/last-page boundary matches `tools/design_gallery.py`. The three
  single-page topics (`502`, `602`, `603`) have no paging controls.
- Generator idempotency: `build_design_gallery_patch.py` emits an empty patch
  after the fix, proving the generated source and checked-in files agree.
- Static checks: decision/event syntax was checked against installed
  `common/decisions/_documentation.md`, current vanilla decision files,
  `eventwindow.gui`, and `eventpictures.gfx`; `validate-hoi4.ps1 -ModRoot`
  reported 0 errors and 0 warnings.
- DDS assets: 61 files, all open as 720x450 RGBA; uncompressed pixel data and
  alpha are retained. Original images and modified assets are kept separately
  in the session visualization directory for comparison.
- Current validator: 12 script/GUI/GFX/localisation files, 0 errors, 0 warnings.
- Mod Doctor with installed game resources: 0 errors and 0 warnings.
- Offline bounds check: all 62 event titles, descriptions and up to eight
  options fit in both Simplified Chinese and English using the restored 1.19
  shared option metrics; picture and options have a 20px horizontal gap. This
  is static evidence, not an in-game screenshot or runtime guarantee.
- Localisation parity: 212 Simplified Chinese keys and 212 English keys, with
  no missing or extra keys. UTF-8 BOM and language headers were verified on
  both English files; English values contain no residual CJK characters.
- Stale-ID, collision, GFX, and localisation cross-reference audit: no missing references found.
- In-game scenarios and fresh-log result: not yet run - game launch requires
  user approval.

## Runtime Status

- Confirmed in game: no.
- Pre-fix failure confirmed from runtime log; post-fix behavior is statically
  validated only.
- Not tested: clicking every decision/option, event picture rendering, one-day
  decision re-enable, reload behavior, and any font/line-length clipping of
  long Chinese descriptions.

## Risks And Next Actions

- Remaining risk: low-resolution tooltip originals cannot gain new detail
  through sharpening. Actual engine section sizing, fonts, high UI scaling
  and interactions with other eventwindow overrides need an in-game check.
- Exact reproduction or manual test: enable the mod, start any 1936 country,
  open the category, then walk every decision and detail page; verify the two
  detail-page buttons behave as requested.
- Next runtime checks: restart HOI4 with this mod, open MMG_guide.500 (eight
  choices), MMG_guide.100 (long labels), MMG_guide.103 (tall pictures), and
  MMG_guide.502 (equipment panel); also check a normal country event. Confirm
  close/back navigation and inspect a fresh error.log. Game launch and playset
  changes have not been performed.
