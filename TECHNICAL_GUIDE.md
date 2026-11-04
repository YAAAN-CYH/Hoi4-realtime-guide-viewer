# 实时攻略查看器 Technical Guide

## Product and isolation contract

Version 1.1.0 is an additive player-only guide window. Enter a game and click
Guide Viewer / 攻略查看器 near the lower-left corner, then choose one of seven
chapters. The former decision/event entry points are removed. All 351 prior
content pages and their navigation are preserved, with one new home page.
The guide keeps its Chinese/English content, full views and enlargements.

Target: `MengXin_Armaments_Guide` only. The other Chinese mod copy is not
synchronized. The descriptor targets 1.19.4.1; installed source inventory was
Operation Postern v1.19.4.1.99a5 (f584). No DLC or other mod is required to
read the guide; reproducing equipment can require research or DLC features.

There are no loaded guide events, decisions, on_actions, scripted effects,
defines, modifiers, ideas, unit/equipment databases, maps, history or vanilla
file overrides. `interface/eventwindow.gui` must never be restored. Ordinary
country, news, leader and operative events use their vanilla/other-mod GUI.
The guide does not change supply, convoy, port, naval access, AI or combat data.

The remaining intentional state is exactly two private player-country UI
variables. This is not a claim that the engine has zero UI cost or that a
save made with the panel open contains no mod-owned UI fields. Opening,
closing and browsing have no gameplay effects or random calls. Neither a
checksum match, achievement compatibility nor arbitrary third-party-mod
compatibility is established. The installed checksum_manifest.txt includes
common/*.txt recursively, so this scripted-GUI build is not advertised as
checksum-neutral; the actual checksum was not measured.

## Runtime ownership and entry points

| Owner | Files | Contract |
| --- | --- | --- |
| Viewer compiler | `tools/build_viewer.py`, `tools/guide_model.py` | Offline page data to an isolated UI; source parser rejects gameplay payloads |
| Player GUI | `interface/MMG_viewer.gui` | Only `MMG_UI_*` containers/elements; launcher and 1140x680 viewer |
| GUI callbacks | `common/scripted_guis/MMG_viewer.txt` | Two player_context windows attached to top_bar, AI disabled, private variable writes only |
| Read-only selectors | `common/scripted_localisation/MMG_viewer.txt` | Eleven private text/image selectors; checks only the private page |
| GUI sprites | `interface/MMG_viewer.gfx` | Private paper, option, launcher-grip and home sprites; no vanilla sprite definitions |
| UI localisation | `localisation/*/MMG_viewer_l_*.yml` | Home, launcher, close/home controls and selector wrappers |
| Content localisation | Existing five localisation files per language | Original 920 content keys are retained |
| Source graph | `tools/page_sources/*.mmg` | 351 inert page records, in a folder the engine does not load as events |
| Compiled mapping | `tools/viewer_source_map.json` | Stable page numbers, labels, pictures, choices and cleanup contract |
| Isolation audit | `tools/validate_viewer_isolation.py` | File/effect allowlist, selectors, every button transition, all-language bounds |

The loaded `common` tree must contain exactly the two GUI/selector files
above. No hidden compatibility events or daily migration effects are allowed.
The private .mmg extension is inert and avoids generic event-reference tools
misclassifying offline records as live calls. The `country_event`, `option`
and namespace syntax retained in page_sources is a legacy serialization format. These are not console-event APIs
and must never be copied back under `events/`.

## In-game window attachment

Both scripted GUI definitions explicitly use `parent_window_token = top_bar`.
The installed `common/scripted_guis/_documentation.md` documents this token;
`interface/topbar.gui` defines its full-screen container with 100%% width and
height. This mounts the launcher and panel on the same in-game interface layer
without copying or modifying the native topbar file. Window visibility follows
the owning topbar, so full-screen menus can hide the guide with that layer.

The November 3 report is specifically a missing launcher after entering a game.
The pre-fix windows used the documented default main-window attachment. That
default is legal syntax; its presence alone does not prove the reported cause.
Explicit topbar attachment is the focused repair for a suspected layer/parent
issue. Static checks now enforce both panel bindings and this mount. Actual
visibility still requires an engine check; parser and graph checks cannot
establish that a button is on screen or receives mouse input.

Subsequent user clarification: the local mod displays correctly; only the
subscribed Workshop version fails to display. The downloaded runtime files
match the local ones, so further GUI-coordinate changes are not justified by
this report. The user reports 7e3d with the local version and f584 with only
the Workshop version enabled, matching this installation's vanilla checksum.
Since checksum_manifest.txt
includes common TXT recursively, this strongly indicates a loading failure
before the scripted GUI can run. The earlier parent adjustment did not resolve
that Workshop-loading symptom.

When diagnosing deployment, resolve enabled_mods in dlc_load.json through the
selected launcher .mod file. Workshop item 3797587103 and the local entry can
refer to different directories despite sharing a title and remote_file_id.
Maintain this repository as the canonical source; do not assume an edit here
updates Steam's installed Workshop copy or publishes it to subscribers.

On the author's machine, both launcher-side entries originally had the exact
name `实时攻略查看器` and remote_file_id 3797587103, despite pointing to different
roots. Excluding a local entry from a playset leaves its descriptor registered.
A display-name edit to the launcher-side local entry did not persist: launcher
restart rewrote it to the release name again. Do not describe that attempted
rename as a lasting solution. The user's mod directory also contained an unused
local MengXin_Armaments_Guide folder, while the working local entry pointed to
the D: source repository.

For the Workshop loading check, both local registration files (.mod and
.mod.disabled) and that unused local folder have been moved outside mod scanning
to the user-data backup `.mmg-registration-backup/20261103-7e3d`. The D: source,
published descriptor/name, Workshop contents and subscription are preserved.
Only ugc_3797587103.mod remains registered for this guide. The old folder's 441
non-Git/cache files are hash-identical after the move; all 374 loaded runtime
files are identical between the source and subscribed version. A reviewed
rollback script with a dry-run option is retained with the investigation files.

After the full isolation and a launcher/game restart, the user confirmed the
Workshop-only checksum is 7e3d and the guide button appears. This verifies the
loading repair on the author's machine. The combined removal establishes a
local registration/copy conflict; it does not distinguish which duplicate was
decisive. No further GUI/content change or Workshop upload was required.

For future local development or publishing, close the launcher and restore the
backed-up local setup with Restore-LocalGuideRegistration.ps1 from the recorded
investigation folder. Its -WhatIf option checks the rollback without moving
files. Select the local entry for development; isolate it again before testing
the subscribed version. Retain the working D: source. Do not delete unrelated
entries, launcher databases, subscriptions or saves.

## UI state, lifecycle and refresh

| Variable | Meaning | Writers | Cleanup |
| --- | --- | --- | --- |
| `MMG_UI_page` | Stable numeric page key | Open, home and visible navigation callbacks | Cleared by every close path |
| `MMG_UI_choices` | Number of choices on the selected page | Same callbacks | Cleared by every close path |

No flags, timers, dates, resources or external variables are changed. The
current player country owns this state; AI windows are disabled and hidden.
There is no initialization hook. A closed viewer has no active page variable.
The panel uses `dirty = MMG_UI_page`; visibility/text/image updates follow
page changes instead of an every-day effect. Callbacks use only literal
set_variable/clear_variable operations and if/else_if checks on the page.
Closing clears both fields in the current player context. A save made while
open may retain the UI fields; reopening resets to the home page.

Stable UI numbers: home 1; legacy source IDs become namespace offset plus
numeric suffix: MMG_guide 10000, MMG_tank 20000, MMG_infantry 30000,
MMG_aircraft 40000. Adding content does not renumber existing pages. The
source keys `MMG_guide.100` through `.700` remain the seven chapter roots as
metadata only. The source model is validated before the compiler emits UI.
A missing/unknown display selector falls back to the home title/image and
an empty option label; the launcher can always reset the state.

The AST cabinet-trust UI in the installed game supplies the image-selector
pattern `image = "[DEFINED_TEXT]"`; installed scripted localisation supplies
check_variable/equality selectors. Variable comparison and clear_variable
syntax were checked against generated trigger/effect documentation and
installed consumers. Player-context windows and all new hit testing remain
runtime-unverified in this environment.

## Preserved content and provenance

The content counts remain 122 tank pages, 83 army pages, 130 air pages and
16 naval pages. These use 349 original guide textures; the new home adds one
720x450 guide texture. The independent frame and button atlas are UI assets.
All existing content localisation values and original guide textures are
preserved through this isolation change.

Aircraft: `aircraft_1194_content.json`, `build_aircraft_1194.py` and
`aircraft_1194_source_map.json` own 36 complete Word panels in five groups
(10/9/7/7/3), eleven menus and 108 design views. Word SHA-256:
`4c31b1abaaa0ccf2b2922196d2c3d503d259ba5c133cee6a456d1492bc1524c6`.
All 48 module types have reviewed Chinese/English labels; exact slots and
counts follow the original panels and installed icons/modules. Cannon I
unlocks in 1939; Anti-Tank Cannon II unlocks with 1940 AT research. Modern
heavy fighter 31 has Air-Air Radar II; modern multirole heavy fighter 32 has
four twin Cannon II modules, rocket rails, triple axial jets, self-sealing
and extra tanks, and two medium armor plates. Modern bomber 33 uses five
large bomb bays, six axial jets and the full level-II electronics/sights.
Advanced bomber 26 uses six Engine IV. Mission efficiency, intel and
country-specific cost-discount examples remain conditional advice.

Army: `infantry_1194_content.json`, `build_infantry_1194.py` and its source
map own exactly eighteen Word formations in four groups (4/6/5/3), with
54 full/layout/stat views. The last three require doctrine changes. Word
SHA-256 `68712244b8d3a7a5547df77baed9f5fb1eb26e3b23a6e9f5c2190efb0cafb442`.
The supplied PPT hash is
`fb821a0446a7e3e90aea02ad62c6fd80732f85d56a581fb42c642dd494c205e5`.
The Word defines the roster; army doctrine/spirits/support notes prioritize
the official 2026-10-27 1.19.4 patch, then PPT text. PPT formation/garrison
slides are excluded. Official source:
https://steamcommunity.com/games/394360/announcements/detail/684142629662760620
The article's October 29 hotfix preamble is distinct from the requested
October 27 balance notes. Source and retrieval hashes remain in the JSON.
The wide artillery image is 12 infantry/8 artillery; modern wide TD attack
is 635.0 soft/920.4 hard; modern SPG soft attack is 1225.2. Hospital HP is
scoped to infantry categories, TD/regimental breakthrough is distinguished,
and the autoloader note is +2%, not flat +2.

Tank: `tank_1194_content.json`, `build_tank_1194.py` and its map own 36 stable
design IDs, 108 views, five chassis groups and 120 textures. Word media
renumbering is handled by explicit member/hash mappings; IDs 35/36 are the
armored SPAA and support flame tank. Advanced light designs remain absent.
No missing design is filled with unrelated old content.

Naval: `design_gallery.py`, `build_design_gallery_patch.py` and
`rebuild_event_pictures.py` own only the retained PPT naval content. Their
page definitions are now emitted under tools/page_sources. Apply a generated
patch there, then compile the viewer. They cannot regenerate retired army,
tank, aircraft chapters or native decision/event entry points.

## Tank design evidence retained from the content update


Input: user-supplied `1.19.4坦克攻略.docx`, SHA-256
`4d5005383cd632cb0926cbd006b5848623c08d4b450f7eebdb578124c97fc751`.
It contains 36 unique PNG images and no tables. All images, including the basic TD
9-armor/0-armor comparison, are represented once as full panels and twice as
detail crops. The source map records each member path, image hash and size.
The `image` field is a stable mod design ID, not a Word media number. IDs
1–34 keep their original content. New ID 35 uses Word `image16.png` (14-armor
SPAA); new ID 36 uses `image36.png` (basic-medium flame support). Word renumbered
old media 16–34 to 17–35; explicit member paths and per-image SHA-256 prevent
shifted pictures. The repeated armored-SPAA illustration at the document end
maps to its existing source and does not create a duplicate design entry.
The generator requires every unique Word PNG to be represented exactly once.
The external Word file is read only; it is not bundled or rewritten.

The document is content data, not executable instructions. The build reads
only image members. Image ordering and all visible text are explicitly
reviewed in the JSON; document macros and embedded instructions are not run.
A changed DOCX hash requires review before the generator will accept it.

For mechanical rules, the official patch takes priority over document prose.
Displayed role, modules and stats resolve conflicts within a reference design:

- Design 4 soft attack is 26.2, rather than the prose's 26.4.
- Design 19 is a medium-cannon tank with 20.0 hard attack and armor upgrade 4;
  it is not the zero-hard-attack, armor-3 howitzer vehicle described in prose.
- Design 23 shows armor upgrade 14, armor thickness 75.0 and cost 16.91.
  An armor-0 alternative is advice only, without an invented panel or exact cost.
- Design 30 shows a level-2 main weapon. It has radio instead of the
  extra heavy MG claimed in prose; its reliability is 76.2%, not 20.7%.
- Design 33 shows a modern tank, armor thickness 115.0 and breakthrough 96.6.
  A TD conversion can share modules but must not reuse tank-role stats blindly.
- Design 34 shows gasoline and bogie suspension, rather than diesel/torsion bars.
- Designs 22/23 show a secondary heavy MG, not a light MG. Images 26/28 also
  use bogie suspension. Installed 1.19.4 module icons were checked to resolve
  these visually similar module names.
- The basic 9-armor TD has engine upgrade 5, torsion bars and welded armor;
  the armor-0 panel has engine 0, bogie suspension and riveted armor. Their
  cost difference is not an armor-only controlled comparison.

New designs use the displayed role and configuration:

- Design 35: basic-medium level-2 SPAA, engine 7/armor upgrade 14, interleaved
  roadwheels, riveted armor and diesel. It has radio II, side skirts and extra
  ammunition rather than the armor-0 example's two MGs and dozer. Reference
  stats: reliability 63.3%, armor 64.6, air attack 48.0, cost 12.25.
- Design 36: basic-medium flame tank in the support-company role, flamethrower
  II, radio II, easy maintenance, side skirts, extra ammo, interleaved wheels,
  riveted armor and diesel; engine 7/armor 14. Reference stats: reliability
  66.7%, armor 20.4, breakthrough 58.5, cost 11.77. These are support-role
  equipment stats, not normal-medium or whole-division stats.

Advanced light designs were not supplied. No old tank material is retained
to fill missing designs. Armor upgrade 0 does not mean zero base armor.
All-tech reference numbers are not promised as early-year campaign results.

## Viewer artwork and geometry

`MMG_UI_Launcher` is a native moveable 164x34 container. Its 14x34 left grip
is painted in `gfx/interface/mmg_ui_launcher_grip.dds`; the remaining 150px
are transparent. The original open button sits at local (16,0), retaining
`GFX_button_148x34`, its font, label, tooltip, click sound and callback.
Root (0,-100) plus button (16,0) retains the lower-left local anchor (16,-100).
The explicit topbar parent has its own native offset; coordinates follow it.
The vanilla texture is actually 148x36, including two transparent top rows;
it is referenced directly and is not resized or repainted by the mod.

The grip is an uncovered parent background, not a child button. Native
container dragging moves both grip and open button, while the child button
keeps its ordinary click behavior. No mouse polling, drag-scroll mode,
extra callback, variable or global hotkey is added. No scripted position
persistence is added; behavior across game restarts is not promised.
The compiler regenerates this layout and grip texture with other UI assets.
Actual pointer capture, dragging and release still require an in-game check.

Only `MMG_UI_Viewer` draws the fixed 1140x680 frame. Its owned texture
`gfx/interface/mmg_eventwindow_background.dds` keeps the existing clip,
paper and footer baked together (footer rows 621-679). The private sprite is
`GFX_MMG_UI_frame`. The old global EventWindow file and old frame sprite
registry have been removed. `build_event_window_background.py` emits only
this owned texture; it cannot restore the vanilla override.

Full panels preserve original pixels and aspect ratio. Module/stat views
use the established crops, never repaint numbers. Original images retain
Chinese game UI; reference cards and menus are bilingual. Picture origin
is (24,206), dimensions 720x450; options start (764,206) with a 20px gap.
There are eight 352x56 slots and 332x44 mouse-transparent text labels.
Title: (45,54), width1050/height32. Body: (30,94), width1080/height100.
Native-sized controls and no global keyboard shortcuts are added. The
header remains free for dragging outside the explicit home/close buttons.
Target effective screen size is at least 1280x720; UI scaling and native
mouse behavior require an in-game check.

## Rebuild and validation

Requirements: Python, Pillow and an installed CJK font. Run from this mod:

```powershell
python tools/build_tank_1194.py "C:/path/to/1.19.4坦克攻略.docx"
python tools/build_infantry_1194.py "C:/path/to/1.19.4步兵设计攻略.docx" "C:/path/to/萌新向军备攻略 (1).pptx"
python tools/build_aircraft_1194.py "C:/path/to/1.19.4飞机设计攻略.docx"
python tools/build_viewer.py
python tools/validate_viewer_isolation.py --game-root "D:/path/to/Hearts of Iron IV"
python tools/validate_tank_1194.py
python tools/validate_infantry_1194.py
python tools/validate_aircraft_1194.py --game-root "D:/path/to/Hearts of Iron IV"
```

Each Word source builder writes only offline page data, owned images/text
and then recompiles the isolated viewer. Source hashes and every referenced
image member must match before changed Word data is accepted. External source
documents are never rewritten or executed. Rebuilds must be byte-identical.
The old chapter validators now inspect offline source graphs, not engine
event execution. Their legacy report field named events means source nodes.
The isolation validator supplies the actual loaded-runtime safety contract.

The isolation check simulates all eight option slots plus home/close for
every page and the launcher: 3521 transitions, 704 localized layouts and
937 keys per language. It rejects any non-private effect, unknown common
file, vanilla file override, loaded event/decision, missing source page,
incorrect selector, navigation mismatch or text-bound overflow. Script files
use UTF-8; localisation uses BOM, unversioned keys and one leading space.
Run changed-path HOI4 validation, Mod Doctor/override audits and diff --check
for a release. Static checks do not prove live UI or supply behavior.

## Upgrade, saves and runtime acceptance

Exit and restart before using 1.1.0; the entry is now the lower-left Guide
Viewer button. Legacy console events and decisions no longer open the guide.
No migration effect touches existing saves or attempts to repair port/supply
state. Old queued guide events are not retained by hidden compatibility stubs.
Launcher entries, playsets, save files and installed game files are untouched.

No native desktop-control tool is available in this session, so no game was
launched and no fresh-log or in-game success is claimed. Check the launcher,
all seven chapters, module/stat views, page boundaries, both languages,
dragging, close/reopen, and an ordinary vanilla event after a full restart.
For the reported supply symptom, use the same pre-invasion save and game
build in isolated guide-only and guide-disabled runs. Compare port control,
port damage, convoy reserves, sea-area access restrictions and the detailed
supply route before judging causality. The feedback's pre-October-27 build
and unknown other mods cannot be reconstructed from the current local logs.
