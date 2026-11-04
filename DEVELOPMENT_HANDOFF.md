# 实时攻略查看器 Development Handoff

## Repository snapshot — GitHub synchronization, 2026-11-04

Target: private YAAAN-CYH/realtime-guide-viewer, branch main. The remote had no
main ref before this synchronization. Publish only this standalone repository,
including the complete 1.19.4 tank, infantry and aircraft content, bilingual
localisation, offline source/build tools and the isolated viewer with its drag
grip. The local commit history begins at 72d966b. Machine-local launcher backup
folders and the other mod copies are outside this repository.

The release snapshot contains 405 files; no individual file exceeds 3 MiB.
The isolation check passes 352 pages, 3521 UI transitions, 704 localized layouts,
937 keys per language and zero vanilla overrides/errors. Git whitespace checks
find only the existing terminal blank line in generated scripted localisation;
runtime bytes are preserved for this known-working snapshot. Two newly staged
Git blob objects were rebuilt from files matching their staged object IDs;
full Git object-integrity validation passes. README now records the
user-confirmed Workshop loading result and explains
duplicate local registration; it no longer describes a global event-window
override or an entirely untested launcher. The user-confirmed runtime evidence
remains limited to loading/checksum/button visibility. No new game test was run.

## Latest investigation — local 7e3d, Workshop f584, 2026-11-03

Latest direct user correction: the LOCAL mod displays correctly; only the
subscribed Workshop version fails. The user reports local checksum 7e3d and
Workshop-only checksum f584. Native launcher-settings.json identifies f584 as the vanilla
build checksum; checksum_manifest.txt includes common TXT recursively. This
strongly points to mod loading, not an absent/incorrectly positioned launcher
in the working local UI. Do not change GUI code to address this observation.

Workshop item 3797587103 was briefly removed/reinstalled during investigation.
After Steam reported installed/no-update/no-download, its descriptor and all
374 loaded runtime/resource files matched the local source. The launcher DB and original
dlc_load.json selected only Workshop. Two launcher .mod entries nevertheless
had exactly the same release name and remote_file_id, with different local
and Workshop paths. Following complete isolation, the user confirmed the
Workshop-only checksum changed to 7e3d and the button appeared. This confirms
a local-registration/copy loading conflict as a group; the combined check
does not identify which duplicate alone was decisive.

The previous attempted local-entry rename did not persist: at 01:35:11 the
launcher rewrote the .mod to the release name, matching both displayName fields
in its DB again. An unused local folder with the same descriptor/Workshop ID
also existed under the user mod directory. The registered working local path
still pointed to D:/cyh_use/codex files/mod/MengXin_Armaments_Guide.

Repair/check: backed up and moved the local .mod, .mod.disabled and unused local
folder to user data/.mmg-registration-backup/20261103-7e3d, outside mod scanning.
All source/target absolute paths and descriptor hashes were checked before the
same-shell moves; failures would roll back completed moves. Only the Workshop
entry now remains registered for this guide. The canonical D: source and Steam
copy are untouched. No GUI, gameplay script, release descriptor, playset, DB,
launch argument, save or subscription changed. No upload is needed for this
machine-local isolation. The local registration is recoverable for development.

Validation: D: source hashes unchanged before documentation updates; all 441
old-folder files preserved; all 374 loaded files still match Workshop. Registry
Personal resolves to the same OneDrive Documents folder as the launcher/logs.
Evidence, move plan/result and Restore-LocalGuideRegistration.ps1 are under
workshop_loading_7e3d_f584_20261103. The restore script's -WhatIf preflight passes
without restoring. Native desktop tools are unavailable; the user performed
the fresh restart and reported 7e3d with the guide button present. This manual
confirmation establishes the loading repair, not an AI-run game test.
The earlier 01:27 empty enabled_mods observation is superseded: the 01:35:15
dlc_load.json and active playset select only Workshop. GUI changes are outside
this loading repair. For local development/publishing, close the launcher and
use the recorded rollback script to recover the pre-isolation local setup.
Restoring local entries requires a new isolation before testing the subscribed
copy; a launcher-side display-name edit alone is fragile. No reupload is needed
for the current machine-local repair.

## Previous change — explicit in-game window attachment, 2026-11-03

User reports that the Guide Viewer launcher is absent after entering a game.
Initially dlc_load.json enabled Workshop item 3797587103. Its descriptor and
four relevant runtime/asset files matched the canonical local copy. During
investigation the user switched to mod/MengXin_Armaments_Guide.mod, pointing
to this repository, and later switched back to the Workshop entry. No
launcher/playset setting was edited by the agent.
The observed error.log only contains metadata errors for two unrelated mod
descriptors; it contains no MMG parser error. This is not proof of mounting.

Both player-context windows previously relied on the default main-window
parent. The installed scripted-GUI _documentation.md says that default is
valid and documents parent_window_token=top_bar. Native topbar.gui supplies
a full-screen 100%% container. Both windows now attach explicitly to that
in-game layer to address a suspected layer/parent visibility issue. Do not
call the missing token a syntax error or claim a reproduced root cause.

Owner: tools/build_viewer.py; generated runtime change is confined to
common/scripted_guis/MMG_viewer.txt. The validator enforces the two correct
window names and explicit topbar mounts. GUI geometry, button sprite/size,
drag grip, content, translations, selectors and callbacks are preserved.
There are still only two private UI variables and no vanilla overrides,
events, decisions, initialization effects or gameplay-data edits. The guide
now follows topbar visibility when full-screen menus hide the owning layer.

Checks: isolation validation passes 352 pages, 3521 transitions, 704 localized
layouts and zero overrides/errors. Changed-path validation passes the one
runtime script with zero errors/warnings. A second compiler run is byte-identical;
the 400 files outside this five-file repair are unchanged, as are all 187 files
in the other mod copy. The callback/condition AST matches the pre-fix script
exactly after removing the two new parent bindings. Evidence and original files
are under viewer_visibility_20261103 outside the mod. Native desktop tools are
unavailable; no game launch, console command, setting edit or engine success
claim is made. User was given a restart/entry check while final checks run.
Confirm the lower-left launcher appears after restarting with this local mod,
then click/open, close, and drag the left grip. The reviewed runtime script was
also copied to the installed Workshop item 3797587103 after backing up and
checking its original hash; its resulting hash matches this repository. Only
that runtime script was synchronized. The source repository remains canonical.
No Steam upload/publication occurred; Steam redownloads may replace local
Workshop changes until the author publishes this source update.

## Previous change — separate launcher drag grip, 2026-11-01

Only the canonical mod is updated. The left side of the Guide Viewer launcher
now has a 14x34 dot-pattern grip. MMG_UI_Launcher is a moveable 164x34 parent
with the original open button at local x16. Moving the parent from x16 to x0
keeps the main button's initial screen position unchanged. Its original sprite,
text, font, tooltip, click sound and callback are preserved. Vanilla's nominal
148x34 button uses a 148x36 texture with transparent padding; it is not resized.

Owner: tools/build_viewer.py. Generated changes: interface/MMG_viewer.gui,
interface/MMG_viewer.gfx and gfx/interface/mmg_ui_launcher_grip.dds. The grip
is the uncovered parent background; placing a button on it would intercept
native dragging. No new callback, localisation, country variable, position
polling, event or decision is introduced. Position persistence is not added.

Checks: original button properties and initial anchor match the pre-change GUI;
the grip texture is transparent behind the main button. Changed-path GUI/GFX
validation passes two files. Existing isolation checks pass 352 pages, 3521
transitions and 704 localized layouts with zero vanilla overrides. Gameplay
scripts and localisation remain byte-identical. An offline native-texture
preview and preservation/rebuild evidence are in launcher_drag_handle.

Runtime remains unverified: native desktop-control tools are unavailable and
no game was launched. Restart, drag the left grip to several positions, release,
click the original button, close/reopen the viewer and check both languages.
The original button should open the home page; dragging the grip should move
the whole launcher without changing the button's dimensions or appearance.

## Previous change — gameplay-isolated guide UI, 2026-10-31

User reports a pre-October-27 invasion with no sea-supply route and requests
no impact on other game data/mechanics. Other enabled mods and the affected
save are unknown. No direct supply/port/convoy/sea-access/unit/AI data edits
were found. The supply symptom is not reproduced or causally attributed.
Current local 05:12 logs are old, not this report's reproduction.

Confirmed architecture issues: a global EventWindow override and seven
country decisions without explicit AI exclusion, routing into 351 country
events. Removed the global GUI file, both decision/category files and loaded
events. Exact legacy files are preserved as audit evidence outside the mod;
five content files moved to tools/page_sources with a private .mmg extension,
becoming inert graph data.

Version 1.1.0 adds MMG_UI_Launcher/MMG_UI_Viewer, two player-only scripted
GUI contexts, eleven read-only text/image selectors and a home page. It
preserves all 351 content pages, 349 original textures and 920 existing
localisation values. There are 352 GUI pages and 937 keys per language.
Only MMG_UI_page and MMG_UI_choices may be written; every close path clears
both. No flags, timers, random effects, on_actions, costs or game effects.
The panel refreshes on dirty=MMG_UI_page. Open-state UI fields may be saved;
no claim of checksum/achievement/multiplayer equivalence is made.

New owners: tools/guide_model.py (strict offline parser), build_viewer.py
(compiler), validate_viewer_isolation.py (runtime allowlist, resources,
selectors and transition simulation). The three Word builders and legacy
naval patch generator now target tools/page_sources; Word builds recompile
the viewer automatically. The background helper emits only a private texture.
Existing chapter validators inspect content source graphs, not live events.
No content or other-copy edits were intended.

Evidence: isolation check covers 352 pages, 3521 actual-callback transitions,
704 localized layouts and zero vanilla overrides, with no errors. Changed-path
validation passes six files; final Mod Doctor reports zero errors/warnings
without suppressions. The engine checksum manifest includes common TXT, so
this is not advertised as checksum-neutral. Rebuild
and chapter regression, Mod Doctor, protected-content hashes and offline
previews are recorded in mechanics_isolation. The audit report explains the
supply-causality limit and a controlled same-save comparison.

No native desktop automation is exposed, so no Steam/game launch, new game,
fresh-log claim, save edit, launcher change or gameplay reproduction occurred.
Restart and use the lower-left Guide Viewer button; test seven chapters,
enlargements, boundaries, both languages, close/reopen, dragging and an
ordinary vanilla event. A supply A/B test still needs the affected save and
exact old build. This local update was not published to the Workshop.

## Previous change — Word aircraft designs and complete module descriptions, 2026-10-31

Only `MengXin_Armaments_Guide` is updated. Replaced the old aircraft gallery
with the 36 designs from `1.19.4飞机设计攻略.docx`, SHA-256
`4c31b1abaaa0ccf2b2922196d2c3d503d259ba5c133cee6a456d1492bc1524c6`.
Every design now lists all weapon groups, engine count/level and special
modules, including the previously undescribed carrier fighter, modern heavy
multirole and modern strategic bomber. All 36 original panels were inspected
alongside the installed module-icon catalogue. Source documents are data;
their file-management instructions were not executed or used to alter presets.

Delivered: five groups (10/9/7/7/3), eleven group-menu pages, 108 design views,
five mission/module/research notes and four reconciled air-doctrine pages.
Air doctrine and aircraft decision routes `.300` and `.600` are retained.
Exact module lists use 48 module types and distinguish module groups from
gun counts. Modern heavy fighter 31 has Air-Air Radar II; modern multirole
27 has one extra tank; advanced bomber 26 has six Engine IV. Source prose
ambiguities are resolved by the actual panels and installed module/tech data.
Efficiency, intel and discount examples are conditional. The old claim that
heavy/strategic aircraft are always useless is replaced with mission-based
choices, consistent with the supplied designs.

Owners: `tools/aircraft_1194_content.json`, `tools/build_aircraft_1194.py`,
`tools/aircraft_1194_source_map.json` and `tools/validate_aircraft_1194.py`.
Generated outputs are the consolidated air event/GFX/two-language YML files
and 130 DDS textures. The legacy gallery/texture builders now own only naval
content. Retired air events, sprites, assets and keys are removed. Tank,
army, naval guide bodies, shared event-window geometry and decision scripts
are preserved. The other mod copy and original source documents remain intact.

Current totals: 351 events and 349 guide DDS; the air subsystem owns 130 of
each. Air integration validates 36 source panels, 48 installed module types,
all navigation and 260 localized layouts, with no errors. Army and tank
regressions pass (83/122 events and 166/244 localized layouts). Changed-path
HOI4 validation covers 16 files, with 0 errors and 0 warnings. Source and
offline output previews, key checks, protected-file hashes, naval-body
comparison and deterministic-rebuild evidence are in `aircraft_update_1194`.
The full localisation audit finds 920 matching keys per language and 702
localized event layouts without overflow. All 244 protected target files and
all 187 files in the other copy are unchanged; sixteen retained naval event
bodies match the Git baseline. The completed target contains 395 files.

Runtime and fresh game logs remain unverified. Manual acceptance: restart,
open 飞机设计 · 1.19.4 / Aircraft Designs: 1.19.4, browse all five groups,
especially 36/40 carrier variants and modern heavy/bomber modules, exercise
both enlargement views and boundary previous/next/menu returns, then check
air doctrines and the existing army/tank/naval chapters in both languages.

## Previous change — English localisation review, 2026-10-31

Only `MengXin_Armaments_Guide` is updated. Reviewed the 227 army-chapter
English keys covering eighteen templates, doctrine requirements, army spirits,
support, occupation and navigation. Replaced literal phrasing with readable
English and aligned names with installed 1.19.4.1 localisation, including
Bayonet Strength, Elevated Engineer Corps, Operational Reserves, Mobile Recon
& Assault and the distinct light-tank/armored-car recon company names. TD,
SPAA and SPG abbreviations are introduced in the patch note. Original numeric
values, roster, doctrine switches and unit roles are preserved.

Owners: `tools/infantry_1194_content.json` for English prose and
`tools/build_infantry_1194.py` for navigation. Regenerate the English army YML
and bilingual reference/menu cards from these sources. Original Word image
views retain the Chinese UI; the English descriptions explain their content.
Chinese localisation, event/GFX routes, tank content and the shared window
must remain byte-identical to the start of this English review. The other
mod copy remains untouched.

Validation: English static validation covers all four English YML files,
with no errors or warnings. Army integration covers 83 events, 18 formations,
83 textures and 166 localized layouts with no errors. Full key parity,
English layout previews, deterministic rebuild and protected-file hashes are
recorded in the `english_localisation` evidence folder. Runtime rendering and
fresh game logs remain unverified. In-game acceptance: restart in English,
open Division Templates: 1.19.4 and Army Doctrine: 1.19.4, check all four
groups, both enlargements, final-three doctrine requirements and support/
spirit pages, then exercise return/previous/next buttons.

## Previous change — Word infantry and official-patch army notes, 2026-10-31

Scope: only `MengXin_Armaments_Guide`, as explicitly requested (called
MengXingGuide in the request). `实时攻略查看器` was read/hash-checked and not
modified. No launcher entry, playset, game process or source document changed.

Delivered: exactly eighteen Word formations in four groups (4/6/5/3), each
with full/battalion-support/stat-cost views. Default doctrine is explicit and
the last three variants carry doctrine-switch requirements. Old formation and
garrison templates, old land tooltip collages and their generator mappings are
removed. Support companies, regimental support, occupation laws and army
spirits are retained as reviewed notes, not as extra formation templates.

Source priority: October 27 official 1.19.4 log, then supplied PPT text for
army notes; the Word defines the formation roster and pictured configurations.
The official article was fetched directly from Valve's Steam News API after
browser rendering was unavailable. Metadata identifies PDX Chakerathe and
2026-10-27 14:05:09 UTC. The post has a distinct October 29 hotfix preamble;
October 27 a783 balance/gameplay is used for the requested priority. Source
hashes, per-page evidence and official URLs are in infantry_1194_content.json.

Notable corrections: line versus regimental TD breakthrough (-75% / -90%),
width/milestone changes, logistics/organization/HP effects and reliable armor
HP. Word image18 is 12 infantry/8 artillery; modern TD soft/hard attack and
45.8-width values follow the panel. The tank-version note's autoloader value
is +2%, rather than a flat +2; the owning tank generator is corrected too.

Files: new infantry content JSON, generator, source map and validator; new
army event/GFX/two-language localisation outputs and 83 DDS assets. The old
guide event/GFX/localisation files lose the retired army definitions. The
legacy PPT texture builder excludes army/tank content. README and technical
contracts are current. Existing tank picture assets and the unified window
remain unchanged; the existing decision entry IDs `.100` and `.400` are kept.

Current totals: 236 events, including 83 army and 122 tank events; 234 guide
textures, including 83 army and 120 tank textures. The army chapter covers
18 formation panels, one Word doctrine overview and 54 detailed formation
views. No new AI, timers, country state or actual game balance is introduced.

Validation: changed-path HOI4 validation covers 12 files with 0 errors and
0 warnings. Army integration checks 83 army events, eighteen formation
sources, 83 textures and 166 localized layouts with 0 errors. Tank regression
checks 122 tank events, 120 tank textures and 244 layouts with 0 errors.
Resource links, graph reachability, namespace registration, previous/next and
return links, BOMs, duplicate keys and conservative text bounds pass.
Old land/army assets and `.401`–`.406` are absent. The inputs were preserved;
source and generated views were inspected. Deterministic regeneration and
unaffected-copy/content preservation are checked with hashes.
Final evidence: deterministic regeneration preserves all 272 target files;
the old gallery generator returns an empty patch; all 187 files in the other
copy are unchanged. The 125 protected tank-picture/window/decision files match
the pre-update hashes, and all 31 retained sea/air event bodies match their
prior definitions. Offline composite previews are in `infantry_update_1194`.

Runtime remains unverified; no fresh game-log success is claimed. Fully
restart, open 陆军编制 · 1.19.4, browse all four groups and enlargement views,
check the final three doctrine warnings, then open support notes and
陆军学说 · 1.19.4 → 陆军精神. Existing tank navigation should remain available.

## Previous change — flame support and armored SPAA, 2026-10-31

Updated both copies from the revised `1.19.4坦克攻略.docx`, SHA-256
`4d5005383cd632cb0926cbd006b5848623c08d4b450f7eebdb578124c97fc751`.
The Word document is read-only source data. It now has 36 unique PNGs; its
last armored-SPAA illustration reuses the same image as the earlier entry.

- Added stable design 35: basic-medium level-2 SPAA with armor upgrade 14.
  Full/module/stat events are `MMG_tank.135`, `.235`, `.335`. It sits beside
  the retained armor-0 SPAA (design 15) in basic menu `.22` (page 3/5).
- Added stable design 36: basic-medium flame tank, explicitly in the support
  company role. Events `.136`, `.236`, `.336`; basic menu `.24` (page 5/5).
- Both show complete original panels plus enlarged modules and stats/cost.
  Descriptions match pictured modules, role and numbers. The armored AA has
  reliability 63.3%, armor 64.6, AA 48.0, cost 12.25. Flame support has
  reliability 66.7%, armor 20.4, breakthrough 58.5, cost 11.77.
- Basic menus now cover 17 designs over five pages. Totals: 36 full panels,
  108 design views, fourteen notes/menus, 122 tank events and 120 tank textures.
- Existing stable IDs 1–34 were matched by the old source hashes. Word's
  insertion renumbered its old media 16–34 to 17–35. The content JSON now
  explicitly owns each member path and expected image hash. Generation fails
  if a source hash changes or any unique Word PNG is omitted/duplicated.
  Event/texture counts are derived from the reviewed content rather than 34.

Changed files: tank content JSON, generator, source map, integration validator,
tank event/GFX/localisation outputs, seven additional DDS, basic/index cards
and the existing documentation. Previous complete-frame GUI repair is preserved.
Both copies retain all 102 original design-view DDS byte for byte; all
unrelated files were checked against the pre-update hashes before doc edits.

Validation: changed-path HOI4 checks report 0 errors/0 warnings (4 files in the
Git copy, 3 in the Chinese-only copy). Tank integration checks report 0 errors:
Git copy 167 total events / 244 localized tank layouts; Chinese copy 164 events /
122 layouts. Source coverage, namespaces, event graph, return routes, duplicate
keys, GFX/texture links, RGBA dimensions and conservative text bounds pass.
Both added original images and their module/stat enlargements were inspected.
Deterministic rebuild, cross-copy equality and unchanged Word hash are checked
alongside these outputs. No in-game run or new runtime-log comparison is claimed.

Manual entry: 坦克设计 · 1.19.4 → 基础底盘 → 第3页（14甲防空） / 第5页（喷火支援）.
Restart HOI4 after updating; actual rendering and clicks remain unverified.

## Previous change — unified event frame, 2026-10-31

User-reported runtime symptoms: a bottom strip appears at the top, and holding
left mouse darkens title and content as separate pieces. The active playset
listed `mod/MengXin_Armaments_Guide.mod`; installed raw version is 1.19.4.1.
The current error.log contained unrelated launcher descriptor errors, with no
MMG GUI error. No game launch, playset change or native input was performed.

Applied to both previously authorized copies:

- `interface/MMG_eventwindow.gfx`: replace runtime cornered tiles with one
  ordinary, single-frame `GFX_MMG_event_root` sprite.
- `gfx/interface/mmg_eventwindow_background.dds`: one 1140×680 RGBA frame,
  including header hardware, paper body and footer at rows 621–679.
- `interface/eventwindow.gui`: remove separate header artwork and retain only
  the root background. Keep engine-bound title/body/picture/options sections,
  fixed content geometry, clickable minimize/options and a single movable root.
- `tools/build_event_window_background.py`: reproducible composition from the
  installed vanilla header/body/footer DDS. Mirrored body repetition prevents
  grain stretching; the center clip retains its width.

Evidence: both changed GUI/GFX pairs pass the bundled validator (2 files per
copy, 0 errors, 0 warnings). Focused structural checks confirm one background,
one movable root, all original native control names, no header sprite consumer,
correct RGBA size, identical frame bytes between copies and deterministic
rebuild. Other GUI window definitions are byte-equivalent after newline
normalization. SHA-256 checks preserve 168 / 162 existing content files
(events, decisions, localisations and pictures). Scoped git diff whitespace
check passes. Offline background/preview and validation JSON are in the session
visualization directory under `eventwindow_fix`.

The split rendering is a source-supported explanation, not an engine trace.
The structural repair is implemented; actual pressed tint, dragging and bottom
placement are not yet verified in game. Fully exit and restart HOI4 before
rechecking; GUI hot refresh can retain old controls. Open the tank index, hold
left mouse on title/body blank space, drag, and inspect the footer; test one
normal country event and confirm option/minimize buttons still work.

## Tank chapter update — 2026-10-31

Goal: replace the entire old tank chapter with the user-supplied
`1.19.4坦克攻略.docx`, adding event pages, choices and enlarged views as needed.
The user explicitly chose to update both local copies:
`MengXin_Armaments_Guide` (Git, Chinese/English) and `实时攻略查看器` (Chinese).
Status: implemented and statically verified; game interaction remains unverified.

Installed game inventory was read locally: Operation Postern
`v1.19.4.1.99a5 (f584)`, raw version `1.19.4.1`. No Steam, launcher,
playset or game process was started or changed. No new game logs were produced.
The available tools did not include native game-window control.

## Delivered behavior

- Existing decision entry `MMG_guide.500` now opens the new 1.19.4 tank index.
- All 34 Word image panels are covered in five groups: interwar 4, basic 15,
  improved 6, advanced 6, land cruiser/modern 3.
- Each panel has full, module and stat/cost views: 102 design views in total.
- Index + two explanatory notes + ten paginated chassis menus = thirteen more
  event windows. Each copy has 115 tank events and 113 new tank textures.
- Full designs browse across the entire chassis group. Return-to-menu restores
  the menu page containing the design. Enlargements return to their own design.
- At most eight choices per event; existing 1140×680 GUI and drag contract remain.
- Reference limitations and all-tech values are explicit. Image roles/modules/
  numbers resolve prose conflicts. Unsupported designs are not fabricated.

## Changed ownership and files

| Files | Change |
| --- | --- |
| `events/MMG_tank_1194_events.txt` | New tank events and both namespace declarations |
| `interface/MMG_tank_1194.gfx`, `gfx/event_pictures/mmg_tank_1194_*.dds` | 113 new sprites/textures |
| `localisation/*/MMG_tank_1194_l_*.yml` | New tank decision, menus, design summaries, navigation |
| `tools/tank_1194_content.json` | Reviewed source order and bilingual prose |
| `tools/build_tank_1194.py`, `tools/tank_1194_source_map.json` | Reproducible DOCX generation and provenance |
| `tools/validate_tank_1194.py` | Focused offline integration/layout validator |
| Existing guide/gallery event, sprite and localisation files | Removed all old tank definitions and text |
| `tools/design_gallery.py`, `tools/rebuild_event_pictures.py` | Removed old tank gallery mappings and obsolete source override |
| `README.md`, `TECHNICAL_GUIDE.md`, this handoff | Updated behavior, source precedence, build and validation contracts |

The old tank chapter is removed from runtime assets and from the PPT generation
mapping. The obsolete medium reference PNG was deleted. No compatibility event
stubs preserve old design advice. Close old tank popups before updating, restart
HOI4, and reopen the decision. No country flags or variables need migration;
pre-existing queued retired tank events are not migrated.

The Chinese-only copy's retained gallery event file lacked a namespace declaration.
Added `add_namespace = MMG_guide` to that file and its generator. This ancillary
one-line registration fix preserves its aircraft/ship page IDs and event bodies.

## Source and content review

Source SHA-256:
`c269b65455894f8f0954e20ce5972caac6bba025b15d6ee4eb957538410191e4`.
The Word file remained unchanged. Its 34 PNG member hashes and dimensions are
recorded in `tools/tank_1194_source_map.json`. Input instructions/macros were not
executed; the document was read as source content.

All 34 full images were visually reviewed alongside module/stat/control strips.
Ambiguous suspension and secondary-gun icons were compared with the installed
1.19.4 `interface/tank_modules_icons.gfx`, actual module DDS and Chinese names.
Examples corrected include the basic cannon tank's nonzero hard attack, the
improved TD's pictured 14 armor, the armor-20 heavy's 76.2% reliability, the
modern tank's 115.0 armor, and the modern SPG's gasoline/bogie configuration.
Full source-precedence details are in TECHNICAL_GUIDE.md.

## Tank chapter validation evidence (before the frame repair)

1. Bundled HOI4 static validator, `-ModRoot <copy> -All`:
   - Git copy: 16 files, 0 errors, 0 warnings.
   - Chinese-only copy: 13 files, 0 errors, 0 warnings.
2. `python tools/validate_tank_1194.py`:
   - Git copy: 160 total events, 115 tank events, 34 source panels,
     113 tank RGBA textures, 230 localized tank layouts, 0 errors.
   - Chinese-only copy: 157 total events, 115 tank events, 34 source panels,
     113 tank RGBA textures, 115 localized tank layouts, 0 errors.
   - Checks include unique IDs, in-file namespace registration, all event
     references, root reachability, return paths, keys in supported languages,
     duplicate keys, BOMs, picture/sprite/texture links, source coverage,
     720×450 RGBA decoding, option counts and conservative text bounds.
3. Both tank rebuilds were run again and all non-Git/non-cache file hashes
   compared before/after: byte-for-byte identical (185 files / 178 files).
4. Both non-tank gallery generators emit empty apply_patch patches.
5. `git -c core.autocrlf=false diff --check` passes in the Git copy.
6. Git HEAD comparison: all 45 retained non-tank event bodies and all non-tank
   entries in the four existing language files are identical.
7. Before/after SHA-256 comparison: 48 Git-copy and 45 Chinese-copy non-tank
   assets/decision/window files unchanged, including both existing GUI/GFX
   window files and every retained non-tank texture.
8. Tank-owned generated outputs match between copies; only the Git copy adds
   English localisation. No old tank events, keys or texture consumers remain.

Offline source strips, generated PNGs, layout previews and detailed validation
JSON were saved outside the mod roots in the session visualization directory.
These are inspection artifacts and are not gameplay screenshots.

## Runtime limitations and next check

No in-game run was performed. Actual font rendering, section repositioning,
mouse clicks/dragging, arbitrary UI scaling, save/reopen behavior, compatibility
with another EventWindow override and fresh runtime logs remain unverified.

Minimal manual path: fully restart with one copy enabled, then open
“决议 → 学说与编制，设计推荐 → 坦克设计 · 1.19.4”. Browse the two notes and
all five groups, including the middle basic menu page (eight choices), full
view and both enlargements. Check design return, group boundaries, the basic
9/0 armor comparison, close/reopen, another guide chapter and a normal event.
Console shortcuts for focused inspection: `event MMG_guide.500`,
`event MMG_tank.21`, `event MMG_tank.112`, `event MMG_tank.212`,
`event MMG_tank.312`. Static success is not runtime certification.
