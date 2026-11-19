# Third-party notices

NFS Underground for Mac (GPL-3.0-or-later, `LICENSE`) is built on the work below. The installer ships each one's license text in
`Contents/Resources/kit/licenses/`.

| Project | What it gives | Where | License |
|---|---|---|---|
| [nfsu1-sw](https://github.com/antoxa2584x/nfsu1-sw) by antoxa2584x | the game's recompilation: seeds, hand-written overrides (`recomp_manual.c`), lifter fixes, Hor+ widescreen, Options rows, 60 fps | `engine/` (at `d597e08f`), the kit | no license file upstream; used here under this project's GPL-3.0-or-later, with credit (see `NOTICE`) |
| [nfsu2-ios](https://github.com/myUdav4iik/nfsu2-ios) by myUdav4iik | the Apple host and the Metal renderer (`nv2a_metal`) | `engine/` (from `85d2cbf`), the kit's objects | no license file upstream; as above |
| [xboxrecomp](https://github.com/sp00nznet/xboxrecomp) by sp00nz | the Xbox lifter (Python) and runtime: kernel, D3D8, NV2A, audio, input | the kit's `lift/` and libraries | MIT |
| [xemu](https://github.com/xemu-project/xemu) | the APU (MCPX audio) and NV2A parts inside xboxrecomp | the kit's libraries (relinked on the player's Mac) | LGPL-2.1-or-later |
| [NFSU2Deadware](https://github.com/LeoDeadware/NFSU2Deadware) by LeoDeadware | the Mac engine patches (render scale, Metal effects, mip chains, pacing), the kit builder, disc import, icon | `engine/` (via the NFS Underground 2 port, `docs/upstream-patches/0007`), `tools/kit.py`, `mac/` | MIT |
| [reUndr-ps5](https://github.com/bystritskiy/reUndr-ps5) by bystritskiy | the disc check by section digests (the reference values) | `mac/xbe_check.py` (written for this port) | MIT |
| [Dear ImGui](https://github.com/ocornut/imgui) 1.92.9 by Omar Cornut | the settings menu's drawing, Metal backend | `engine/third_party/imgui`, the kit's `libimgui.a` | MIT |
| [Roboto](https://fonts.google.com/specimen/Roboto) Medium | the settings menu's font, compiled in | `engine/third_party/fonts` | Apache-2.0 |
| [SpeedBreaker](https://github.com/SpeedBreakerProject) by project(u) | the settings menu's design (pages, rows, controller first, Quit Game) | `engine/src/overlay` (written for the NFS Underground 2 port) | GPL-3.0-or-later |
| [Capstone](https://github.com/capstone-engine/capstone) | the x86 disassembler the lifter uses | the kit's `py/capstone` | BSD-3-Clause |
| [SDL3](https://github.com/libsdl-org/SDL) 3.4.16 | window, input, gamepads, sound | `libSDL3.dylib` | Zlib |
| [sdl2-compat](https://github.com/libsdl-org/sdl2-compat) 2.32.74 | SDL2's API on SDL3 (the runtime is written against SDL2) | `libSDL2-2.0.0.dylib` | Zlib |
