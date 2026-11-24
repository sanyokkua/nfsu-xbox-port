# Changelog

## Unreleased

Engine fixes from the Harry Potter Chamber of Secrets port:

- Renderer: textures with border addressing get the stage's own border colour (the fragment shader returns
  `SET_TEXTURE_BORDER_COLOR` outside [0, 1]); Metal samplers only have black or white borders.
- Controller: **LB is White, RB is Black** (they were swapped; as on the original controller and in xemu). The keyboard keeps
  Q = White, E = Black. A press shorter than one of the game's frames is still seen, and held for at least two reads.
- Runtime: the file handle table is locked (two threads opening files at once could share a slot); a read on a handle that
  was just closed ends the file instead of failing as a disc error; an event set hands the CPU to the thread it wakes, as
  on the Xbox (a lost wake-up hung CoS at a loading screen).
- Renderer: no copy of a render target that stays bound on a stage no shader reads (CoS: 24 -> 60 fps).
- Log: one `[metal]` line each for border addressing, W-buffer depth and fog-unit use.
  NFSU1 uses no W-buffer depth; its fog is linear with params 1, 1 (factor = coordinate, as drawn
  already), so the CoS fog unit is not ported.
- Lifter: **79 missed functions seeded** that were empty stubs. The lifter gives every jump or call target it did not
  find as a function an empty body (a bare `ret`); 41 of this game's 77 such stubs were real code, many of them a function's
  shared exit (`pop edi; pop esi; ret`), so the caller got its stack and registers back wrong (in CoS this froze the game).
  `tools/stubcheck.py` classes every stub; `tools/relift.sh` and `tools/build_release.sh` fail when one is real code.
- Runtime: a skipped wild indirect call at a site that pops its own arguments (`add esp, N` after the call) pops only the
  return address (esp was left N bytes high). Reads, writes and waits hold their object, so a close on another thread
  no longer frees it in use; a handle closes once; reads and writes at an offset are one `pread`/`pwrite` (two threads on
  one handle got each other's bytes); handle tokens are handed out next-fit; 65536 handle slots and 256 timers. A Ke
  object shadow whose memory now holds the guest's own event is dropped. A heap request larger than the heap is refused
  (it rounded to 0).
- Input: the app no longer aborts when a controller disconnects. sdl2-compat keeps its pad list without a lock, and the
  game's thread looked for pads again while the main thread did the same. Pads are now opened and closed on the main thread
  only; the game's thread just reads them (from the CoS port). Dev: `NFSU2_PAD_HOTPLUG_TEST=<ms>` attaches and detaches a
  virtual pad that often.

## 0.1.1 (2026-11-23)

- Lifter: x87 80-bit operands (`fld`/`fstp` of a 10-byte value) were read as 4-byte floats and not stored at all. The C
  runtime's asin/acos load π/2 that way, which in the Harry Potter Chamber of Secrets port turned the player 90° when the stick
  pointed straight along an axis. Now converted exactly (`recomp_ld_f80` / `recomp_st_f80`); 12 loads in this game.

## 0.1.0 (2026-11-19)

First release: the Xbox USA disc of *Need for Speed: Underground*, built on the player's Mac.

- Base: nfsu1-sw `d597e08f` (v0.4.0) with nfsu2-ios's Apple host and Metal renderer (`85d2cbf`).
- The NFS Underground 2 port's engine changes that don't hook NFSU2's own code: NFSU2Deadware's Metal patches (resolution scale up
  to 4x, FXAA, anisotropic filtering, full mip chains, bloom, ambient occlusion, gamma, motion blur, pacing, pad input without
  focus); not its HD textures and translation, nor its NFSU2-only hooks (120 fps, draw distance, car LOD, HUD mover).
- 60 fps races (nfsu1-sw's flip-interval wrapper), Hor+ 16:9 (nfsu1-sw); on 16:10 screens the whole picture with thin bars by
  default (Display > Picture: Fill cuts the sides).
- In-game settings menu (Back + Start, F1 or Cmd+,), the same as the NFS Underground 2 port's: Display, Graphics, Audio, Input
  and Advanced pages, live where the engine allows (Picture, Frame Rate and Keyboard as Controller at the next start, marked
  "restart"), Reset page, Quit Game. The game's Options > Camera rows (nfsu1-sw's) work on Metal and share their values with it.
- Everything the port is built from is in the repository (`engine/`): no download at build time.
- The app keeps everything in `~/Library/Application Support/NFS Underground`; logs in `logs/`.
- Installer DMG (no game code): imports the disc image, checks `default.xbe` by its section digests (images differ in a few
  media-patched bytes), lifts and compiles the game with Apple's Command Line Tools, puts the app in Applications. macOS 15+.
