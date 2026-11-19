# How engine/ was made

`engine/` is [antoxa2584x/nfsu1-sw](https://github.com/antoxa2584x/nfsu1-sw) at `d597e08f` (v0.4.0, Linux and Switch) with
these patches applied in order (`git am`), imported on 2026-11-19 so that the port builds from this repository alone. Later
changes to `engine/` are in this repository's git history.

- `0001`: `tools/regen.sh` writes the XBE parser's analysis JSON before the disassembly (from nfsu2-ios).
- `0002`: the Apple host (`src/apple/`) and the Metal renderer (`xboxrecomp/src/nv2a_metal/`) of
  [myUdav4iik/nfsu2-ios](https://github.com/myUdav4iik/nfsu2-ios) `85d2cbf`: its generic changes over nfsu2-sw (`git diff
  d3bbc30 85d2cbf`, no iOS-only files), with NFSU1's entry point kept in `src/main.c`.
- `0003`, `0004`: NFSU2Deadware's (LeoDeadware, MIT) macOS baseline and Metal-only build, without their `CMakeLists.txt` and
  `src/main.c` hunks (written by hand into 0002).
- `0005`: the window title.
- `0006`: a first Settings window (Cmd+,); replaced by 0007's menu.
- `0007`: the engine changes of the [NFS Underground 2 port](https://github.com/sanyokkua/nfsu2-xbox-port) v0.1.0 that don't
  hook NFSU2's own code (NFSU2Deadware's Metal effects, pacing, mip chains and 4x scale; the overlay settings menu; the player
  folder), with NFSU1's options table and Options > Camera rows on Metal. Without `third_party/` (Dear ImGui 1.92.9
  and Roboto Medium, copied unchanged from the NFS Underground 2 port's `engine/third_party`).

The upstream agent notes (`CLAUDE.md` of nfsu1-sw) are in `engine/docs/NFSU1_SW_AGENT_NOTES.md`.
