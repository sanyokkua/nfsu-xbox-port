# Changelog

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
