# 实时攻略查看器 Technical Guide

## Product Contract

- Player-facing purpose: a start-visible decision category named
  `学说与编制，设计推荐` with seven decisions (陆军学说 / 海军学说 / 空军学说 /
  陆军编制 / 坦克设计 / 飞机设计 / 舰船设计). Each decision opens an event
  menu; selecting an entry opens a detail event with a localized summary
  and a guide screenshot. Detail events offer `了解了` (close) and
  `我还想看看其他的` (return to the same chapter menu).
- Supported HOI4 build: 1.19.x (designed and statically checked against the
  installed 1.19 summer/open-beta build with current 1.19 schema).
- Required DLCs and dependencies: none.
- Standalone, submod, compatibility patch, or override: standalone add-on mod.
- Source content: 《萌新向军备设计攻略（1.19）》 by 食言者当受食炎之罚 /
  牢绯工坊; bundled screenshots are reused only inside this guide mod.

## Architecture

| System | Entry point | Owned files | Visible consumers |
| --- | --- | --- | --- |
| Decision category | `MMG_guide_category` | `common/decisions/categories/MMG_guide_category.txt` | Decision UI, shown from game start |
| Seven decisions | `MMG_*_decision` | `common/decisions/MMG_guide_decisions.txt` | Fire menu events 100/200/300/400/500/600/700 |
| Menu + detail events | `MMG_guide.100`-`MMG_guide.706`, plus gallery pages | `events/MMG_guide_events.txt` + `events/MMG_design_gallery_events.txt` | 62 events; chapter navigation and previous/next picture pages |
| Event pictures | `GFX_MMG_*` | `interface/MMG_eventpictures.gfx`, `interface/MMG_design_gallery.gfx` + `gfx/event_pictures/*.dds` | 61 event textures |
| Event window layout | `EventWindow` GUI override | `interface/eventwindow.gui` + `interface/MMG_eventwindow.gfx` | 1140x680 popup; title/description above a 720x450 picture and a separate option column |
| Localized text | all visible keys | `localisation/simp_chinese/*.yml`, `localisation/english/*.yml` | Simplified Chinese and English decision UI and event popups |

## State Contracts

| Identifier | Type and owner | Writers | Readers | Unit and lifecycle |
| --- | --- | --- | --- | --- |
| `MMG_guide_category` | decision category | this mod | game | persistent category; no state |
| `MMG_land/naval/air/..._decision` | decisions | this mod | player click | 0 PP; re-enabled after one day via `days_remove = 1` |
| `MMG_guide.*` | triggered country events | decision effects or parent-event options | game event system | no state written; safe to re-fire |
| `GFX_MMG_*` | event-picture sprites | this mod | event `picture` fields | static 720x450 RGBA DDS with transparent padding |

## Cross-File Contracts

- Decision category id and the seven decision ids match the category block in
  the decision file.
- Each decision `complete_effect` references the correct menu event id.
- Every menu event option references a detail event id that exists in the same
  event file.
- Every detail event back-option references its own menu event id.
- Every design detail displays exactly one image. Pages are semantically marked
  as complete designs, UI supplements, pre-conversion references, or related
  configurations. A reference whose visible role differs from the target is
  never presented as a finished design.
- Tank destroyer page 1 uses PPT media `image127`, the actual advanced
  high-velocity-cannon TD. `image126` and `image125` remain visibly labelled
  medium tanks and are only conversion references. Both SPG pages use
  `image119` and `image120` and are explicitly light SPGs; no medium-SPG image
  is claimed. The submarine topic states that the PPT provides no submarine
  screenshot and labels `image139`/`image140` as ASW-related configurations.
- Gallery page IDs are `base_event_id * 10 + page_number` for pages 2 onward.
  Existing base IDs remain unchanged. Previous/next links stay within a topic;
  close and chapter-return options remain available on every page. Every event
  file declares `add_namespace = MMG_guide` before defining namespaced IDs;
  omitting it makes HOI4 1.19 resolve navigation to `MMG_guide.0000`.
- `tools/design_gallery.py` owns the source/page mapping. Run
  `tools/build_design_gallery_patch.py` and apply its output with `apply_patch`
  to regenerate event, GFX and localisation definitions before rebuilding DDS.
- Every event title/desc/option key and every decision/category key exists in
  both `localisation/simp_chinese` and `localisation/english`; language key sets
  must remain identical.
- Every event `picture` token is registered in `interface/MMG_eventpictures.gfx`,
  and every registered texture path exists under `gfx/event_pictures/`.
- The mod overrides vanilla `interface/eventwindow.gui`. All ordinary country
  events therefore use the wider `EventWindow`, not just MMG events. Other
  window definitions remain intact; the shared option entry now matches the
  installed 1.19 `300x47` container and `hoi_20bs` text contract. The guide's
  option grid provides wider 352x56 slots without changing other event types.
- Picture bounds within the bottom section are (24,16)-(744,466). Options
  start at (764,16), with 352x56 slots and room for eight entries. The 20px
  horizontal gap remains even when the engine adjusts section positions.
- The 1140x680 layout targets at least 1280x720 effective UI pixels. Higher
  UI scaling reduces the available logical area and needs a runtime check.
- HOI4 1.19 mouse-hit contract: `EventWindow` owns the only non-transparent
  full-size background (`GFX_MMG_event_root`) and is the only movable
  container. The three named child sections remain for engine bindings but
  have no interactive body backgrounds. Header artwork is a mouse-transparent
  root decoration; the title, description
  and event picture pass mouse input through to the root. Event-option buttons
  remain interactive and therefore are intentionally excluded from drag input.
- No `replace_path`, flags, ideas, modifiers, AI files, or persistent state.

## Lifecycle And Performance

- Initialization and cleanup: no country state, flags, ideas, or timers to
  clean up.
- Update cadence: all `allowed`/`visible`/`available` blocks are constant
  (`always = yes`), so there is no per-frame scan cost.
- Save/reload behavior: decisions and events carry no state; `days_remove = 1`
  cooldown and open popups are saved by the engine normally.

## Compatibility And Migration

- Dependency and DLC gates: none.
- Stable IDs and old-save migration: all IDs use the `MMG_` / `MMG_guide`
  prefix; no migration needed.
- Known engine limitations or workarounds: guide navigation uses chained
  country events instead of a scripted GUI because the request is a
  clickable decision/event flow; each chain terminates at the player choosing
  `了解了` or closing the menu.

## Validation

- Static checks: `validate-hoi4.ps1 -ModRoot ...` and targeted searches for
  stale IDs, duplicate definitions, missing localisation/GFX links, and
  encoding violations (see DEVELOPMENT_HANDOFF.md for current results).
- Minimal in-game scenarios:
  1. Start any country in 1936 and confirm the category and seven decisions
     are visible immediately.
  2. Click each decision, browse every option, and verify every detail page
     shows an event picture.
  3. From any detail page, click `了解了` (closes) and `我还想看看其他的`
     (returns to the same chapter menu).
  4. Reload the save and confirm all decisions can still be opened.
- Fresh-log expectations: no parser errors referencing MMG files, no missing
  sprite/localisation warnings for `GFX_MMG_*` keys.

## Development Conventions

- Prefix: `MMG_` for database/localisation ids, `MMG_guide` for the event
  namespace.
- Script files: UTF-8 without BOM, ASCII comments.
- Localisation files: UTF-8 with BOM, unversioned `key: "text"` entries. Keep
  Simplified Chinese and English key sets in parity.
- Event pictures: 720x450 RGBA uncompressed DDS, displayed at native scale.
  `tools/rebuild_event_pictures.py` extracts mapped `ppt/media` originals,
  trims continuous near-black exterior rows/columns (RGB <= 3), searches
  ordered row layouts, then resamples with Lanczos and mild sharpening.
  Interior dark tooltip backgrounds are content and are preserved. Unused
  space is alpha-transparent; screenshots keep their aspect ratio.
- Rebuild with Python and Pillow:

  `python tools/rebuild_event_pictures.py <source.pptx> --preview-dir <output>`

  The source PPT is read-only. The script builds all 61 DDS assets
  and writes PNG previews, contact sheets and `source-map.json` to the chosen
  output directory. The map records source image sizes and crop bounds.
- `tools/sources/tank_medium.png` preserves the user-supplied complete medium
  tank reference and overrides PPT media image122. All other images come from
  the PPT. Design pages use one source each; non-design guide pages may pack
  multiple related screenshots.
- Equipment originals generally exceed 1000px in width. Small source tooltip
  captures retain their original information limits; sharpening does not
  reconstruct missing characters or detail.
