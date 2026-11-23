# How the port was made

A log of the steps, the decisions and what went wrong. It follows the NFS Underground 2 port
([nfsu2-xbox-port](https://github.com/sanyokkua/nfsu2-xbox-port), its `docs/PORTING.md`), which was made first with the same
engine; this file says where NFSU1 differs.

## Sources (pinned)

| What | Where | Pin |
|---|---|---|
| Base | [antoxa2584x/nfsu1-sw](https://github.com/antoxa2584x/nfsu1-sw), branch `main` | `d597e08f` (v0.4.0, Linux and Switch; a fork of nfsu2-sw) |
| Apple host, Metal renderer | [myUdav4iik/nfsu2-ios](https://github.com/myUdav4iik/nfsu2-ios), branch `ios` | `85d2cbf` |
| Engine patches, overlay menu, installer | [sanyokkua/nfsu2-xbox-port](https://github.com/sanyokkua/nfsu2-xbox-port) | v0.1.0 (NFSU2Deadware's patches inside) |
| Disc | Xbox USA, `default.xbe` title `0x45410047`, XDK 5558, entry `0x164356`, `.text` 1,819,996 bytes | section digests in `mac/xbe_check.py` |

No NFSU1 Mac, Metal or iOS port existed when this started (2026-11-19): nfsu1-sw runs on Linux and the Switch with OpenGL or
Vulkan. reUndr-ps5 (bystritskiy) is a PS5 port of the same tree; only its disc check idea is used here.

## 1. The disc

- The ISO is a stripped XISO: `python -m tools.xiso unpack` (xboxrecomp's) or `mac/xiso.py` extract it.
- **Whole-file hashes don't identify the disc.** This disc's `default.xbe` has a different SHA-256 than reUndr-ps5's reference,
  but all ten stored section digests match it. Its `.text` doesn't match its own stored digest: a few bytes were patched by the
  tool that made the image (extract-xiso's media patch). So the check (`mac/xbe_check.py`, after reUndr's `xbe_check.c`) compares
  the title ID, each section's size and stored digest, and the data of every section but `.text`; it reports `.text` as
  pristine or media/region-patched. The NFSU2 executable is refused (another title), as is any other build.

## 2. Lift and build (first day)

- **Lift:** nfsu1-sw's `tools/regen.sh` needed nfsu2-ios's hunk that writes the XBE parser's analysis JSON before the disassembly
  (patch 0001; without it: "Analysis JSON not found"). Then: 82 s on the M1 Pro, 12,899 of 12,901 functions, 0 failed, 52 C files
  (81 MB), 77 unresolved call targets stubbed. Run it with `bash` (the file wasn't executable).
- **Apple host and Metal (patch 0002):** nfsu1-sw is a fork of nfsu2-sw and keeps its renderer interface
  (`kernel/nv2a_backend.h` is identical), so nfsu2-ios's generic delta over nfsu2-sw (`git diff d3bbc30 85d2cbf`, without iOS
  files) applied directly; `src/main.c` and `CMakeLists.txt` were edited by hand (NFSU1's entry point kept). First build: 12 s.
- **Boot:** menus on Metal at once; a scripted Quick Race (nfsu1-sw's `RECOMP_PAD_SCRIPT`) rendered correctly at a steady 60 fps
  (nfsu1-sw's flip-interval wrapper: `[fps] flip interval 2 -> 1 vblank`). The user then played with a gamepad: fine.

## 3. The NFS Underground 2 port's engine (patch 0007)

The NFSU2 port, released meanwhile, had NFSU2Deadware's Metal work, an overlay settings menu, a player folder and the installer.
The two trees were compared file by file (nfsu1-sw's `xboxrecomp/` against the NFSU2 port's `engine/xboxrecomp/`, 46 files):

- **The lifter differs and stays nfsu1-sw's.** nfsu2-ios and the NFSU2 port never changed `xboxrecomp/tools`; nfsu1-sw has
  NFSU1's own fixes there (D3D push-buffer immediates taken for function starts, jcc targets taken for gap prologues).
- **The runtime got both.** The NFSU2 port's changes since `85d2cbf` (rebuilt as a commit on `85d2cbf` from its `engine/`) were
  applied with `git apply --3way` on nfsu1-sw: generic paths only (`xboxrecomp/src`, `src/apple`, `src/overlay` but its options
  table, `third_party`). Two conflicts: `kernel_bridge.c` (nfsu1-sw locks the vblank to the display's vsync; NFSU2 added a fine
  timer wait: both kept, the wait in the timer branch) and `usb_gamepad.c` (two different hooks: both kept).
- **Not taken, because they hook NFSU2's own code** (addresses in its `.text`/`.data`): 120 fps (the title's vblank counter and
  step floor), the game step locked to the display, draw distance, car LOD distances, the six reflection faces every frame, hold A
  to skip movies, HUD moved to the visible edges (`hud_wide.c`), PlayStation button glyphs (texture hashes). Each needs NFSU1's
  equivalents found first.
- **NFSU1's options:** nfsu1-sw already had NFSU2's Video rows on its Options > Camera screen (Car Reflections, Resolution Scale,
  Anti-Aliasing, Anisotropic, Square Pixels), for its Vulkan build only. Metal reads the same variables, so they are on for Metal
  too, with a 4x step (the Metal default, as in NFSU2) and `nfsu1_option_get/set` for the menu (`src/overlay/nfsu1_options.c`).
- **Mach-O and weak references:** the NFSU2 code declares two hooks weak (`xbox_after_vblank_dpc`, `nfsu2_skip_progress`) and NFSU2
  defines them; with no definition the link fails ("Undefined symbols"), so the runtime now has weak no-op definitions.
- **16:10 screens:** NFSU2's presenter fills a 16:10 Mac screen by cutting the 16:9 picture's sides and moves NFSU2's HUD inward.
  NFSU1's HUD reaches the picture's edges (laps top left, speedometer bottom right) and has no mover, so NFSU1 shows the whole
  picture with thin bars by default (`NFSU2_SCREEN=fit`); the menu's Display > Picture switches to Fill.
- A first Settings window (patch 0006, an AppKit panel) taught one thing: SDL's menu already has a **Settings…** item that does
  nothing, so adding one gives two, and Cmd+, goes to SDL's. The NFSU2 port takes SDL's item over; so does the menu here.

## 3b. Lifter: x87 80-bit operands (2026-11-23)

From the Harry Potter Chamber of Secrets port: `fld xword ptr [m80]` was lifted as a 4-byte float (`fp_push(MEMF(..)); /* fld */`)
and `fstp m80` as a no-op. The C runtime's asin/acos load π/2 that way for |x| = 1 and got ≈ 0 (in CoS the player's heading came
out 90° off). The lifter now emits `recomp_ld_f80` / `recomp_st_f80` (`recomp_types.h`, after `MEMF`/`MEMD`; this tree has no
`recomp_cvt_si`), with a unit test. NFSU1: 12 loads changed to `/* fld tbyte */`, no m80 stores. Relift, build, `tools/smoke.sh`
and a scripted Quick Race (`RECOMP_PAD_PRESS=0x10,2500,200` plus `a` every 2.5 s from 21 s in `RECOMP_PAD_SCRIPT`) pass.

## 3c. Engine fixes from the Chamber of Secrets port (2026-11-23, not released)

From `hpcos-xbox-port` (its notes: XBOX360_PORTING_NOTES.md section 14), commits a7c6fd4, de1e35e, 2587e78, e8c7e09,
eaa3bff, cbcb224:

- **Texture border colour in the shader** (CoS `ca756e0`): border addressing (mode 4) samples clamp-to-edge and the fragment
  shader returns the stage's `SET_TEXTURE_BORDER_COLOR` outside [0, 1] (`nv2a_samp`, `Nv2aMslFs.bc/bm`). A `[metal] border
  addressing` line names each stage and colour a title uses. Checked: a scripted Quick Race (START every 2.5 s, then A every
  2.5 s from 21 s, 100 s): no stage with border addressing (the old sampler gave transparent black); race frames before and
  after are the same picture at a different moment of the race.
- **LB = White, RB = Black** and the **press latch** (CoS `dcc5179`, `12f88fc`): the bumpers were swapped in
  `xinput_device.c` in every port of this engine; the keyboard keeps Q = White, E = Black (`apple_keyboard.c`). Presses are
  latched from SDL's controller events between two reads (`RECOMP_PAD_LATCH=0` off) and held for `RECOMP_PAD_MIN_READS`
  reads (default 2). `RECOMP_PAD_SCRIPT` does not go through SDL events, so scripted runs do not exercise the latch; needs a
  pad in a play test.
- **Runtime** (CoS `dcc5179`, `f38f328`, `cf6d9c2`): the handle table under a spinlock; a read on a handle closed within 2 s
  returns `STATUS_END_OF_FILE`; `NtSetEvent` waits (2 ms at most) until the waiter it releases has queued for the guest lock
  (`RECOMP_WAKE_HANDOFF=0` off, `RECOMP_EVT_TRACE=1`).
- **No feedback copy** for a render target bound on a stage no combiner reads (CoS `9178756`, `nv2a_psh_reads_tex`).
- **Not ported:** NFSU1 uses no W-buffer depth; it enables the fog unit only as linear fog with params 1, 1, where the fog
  factor is the coordinate the vertex program writes, as drawn already. The CoS fog unit is not ported. This tree counts
  event waiters already (`ev_waiters`, its PulseEvent fix), so `w32_event_waiters` reads that. The InsertCallback latch hold
  is not needed: this tree has no clear-value latch (only CoS's XDK 5028 calls back through it). Viewport constants 58/59
  from `SET_VIEWPORT_*`: this XDK writes the constants itself. The worker wait, loader callbacks, file-cache hold,
  DirectSound address tag, 2D tile seams, cutscene skip and left-stick range are CoS's own code or tuning.
- Verified: `cmake --build build/release`; `tools/smoke.sh` OK; the Metal shader test (448 shader pairs, 48 recorded by the
  run, 0 failures (the NFSU2 port's test built against this tree)); frame throughput as before. The runtime's own unit tests
  (`engine/xboxrecomp/tests/kernel_*`) need `pkg-config`, not installed on this Mac: not run.

## 4. A self-contained repository and the installer

As for NFSU2: the patched tree is `engine/` (`git archive`), the patches are kept in `docs/upstream-patches/` as the record
(0007 without `third_party/`, which is Dear ImGui and Roboto unchanged), `tools/fetch.sh` is gone, `engine/gen/` is ignored.
nfsu1-sw's `CLAUDE.md` is `engine/docs/NFSU1_SW_AGENT_NOTES.md`.

The release kit is the NFSU2 port's, renamed (app `NFS Underground.app`, executable `nfsu1`, folder
`~/Library/Application Support/NFS Underground`, installer variables `NFSU1_*`), with three NFSU1 changes: the disc check above
(the import and the installer's "already installed" test), regen's `NFSU1_XBE`/`NFSU1_GEN_DIR`, and the DMG test's disc names
(`*.BUN`, `*.mad`, `*.abk`, `TRACKS`, `FRONTEND`). SDL is the same pinned build for macOS 15.

## Verification

- `tools/smoke.sh`: 75 s, the menu opened and closed, the last frame not black: OK.
- Scripted menu shots (`NFSU2_OVERLAY_SCRIPT` + `NFSU2_OVERLAY_SHOT`): every page.
- Scripted Quick Race at 4x with bloom, in a window: 54-60 fps on the M1 Pro, the picture correct.
- `tools/make_dmg.sh`: DMG 5.2 MB, `tests/dmg_no_game_code.sh` PASS (361 disc files, 64 windows of 2.3 MB of code).
- A headless install from the DMG into a clean HOME (`NFSU1_NO_UI=1 NFSU1_IMPORT_ISO=… NFSU1_INSTALL_DIR=…`): copy 1.8 GB +
  check + lift + compile + link + icon = **2 min 17 s** on the M1 Pro; the installed app started from its player folder
  (`game/` with the saves in `UDATA/`, `player/`, `saves/`, `cache/`, `logs/nfsu1.log`), found the controller and ran 60 s.
- `tools/publish_check.sh`: PASS.

## Pitfalls (each cost a run)

- **The disc's `default.xbe` hash:** see 1.
- **`regen.sh` isn't executable** in nfsu1-sw: run it with `bash`.
- **A binary file in a diff:** `git apply` aborts the whole patch on a binary hunk without a full index; `git diff --binary`.
- **zsh doesn't split `$VAR` into words** (again): `perl -pi … $F` got one file name with spaces. Run such loops with `bash -c`.
- **A patch with Dear ImGui is 3.6 MB:** the publish check's 2 MB limit; the record leaves `third_party/` out.
- **Renaming `NFSU2_` to `NFSU1_` by pattern** also renamed CMake's `-DNFSU2_GEN_DIR` in `build_release.sh`: the engine keeps
  `NFSU2_*` names (nfsu1-sw's shared glue), only regen's and the installer's are `NFSU1_*`.
