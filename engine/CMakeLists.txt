cmake_minimum_required(VERSION 3.20)

# ============================================================================
# Need for Speed: Underground 2 (Xbox, NTSC-U) - Static Recompilation
#
# Hosts: Windows (MSVC, D3D11), Linux (GCC, SDL2 + OpenGL) and Nintendo
# Switch homebrew (devkitA64 + libnx, built with switch/build.sh).
# ============================================================================

project(nfsu2_recomp C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_compile_definitions(
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

set(XBOXRECOMP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/xboxrecomp" CACHE PATH
    "Path to the xboxrecomp toolkit root directory")

# The lifted code is ~100 MB of C generated from the retail XBE. It is never
# committed; point this at wherever tools.recomp --gen-dir wrote it.
set(NFSU2_GEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/recomp/gen" CACHE PATH
    "Directory holding the tools.recomp output (recomp_*.c, recomp_funcs.h)")

if(NOT EXISTS "${NFSU2_GEN_DIR}/recomp_funcs.h")
    message(FATAL_ERROR "No generated code in ${NFSU2_GEN_DIR}. Run tools.recomp "
                        "with --gen-dir, or pass -DNFSU2_GEN_DIR=<dir>.")
endif()

# The Vulkan renderer (xboxrecomp nv2a_vk) instead of OpenGL. On the Switch it
# links mesa-switch's static NVK (NVK_SDK) and builds nfsu1x-vulkan.nro.
option(NFSU2_VULKAN "Render with Vulkan instead of OpenGL" OFF)
set(XBOXRECOMP_VULKAN ${NFSU2_VULKAN} CACHE BOOL "" FORCE)
# Apple: the native Metal renderer (nv2a_metal, from nfsu2-ios), the default at
# run time; with NFSU2_VULKAN too, NFSU2_RENDERER=vulkan picks MoltenVK.
if(APPLE)
    option(NFSU2_METAL "Build the Metal renderer" ON)
else()
    set(NFSU2_METAL OFF)
endif()
set(XBOXRECOMP_METAL ${NFSU2_METAL} CACHE BOOL "" FORCE)

add_subdirectory(${XBOXRECOMP_DIR} ${CMAKE_BINARY_DIR}/xboxrecomp)

file(GLOB RECOMP_GEN_SOURCES CONFIGURE_DEPENDS "${NFSU2_GEN_DIR}/*.c")

set(GAME_SOURCES
    src/main.c
    src/nfsu1_extras.c
    src/recomp_manual.c
    src/switch_nx.c
    src/switch_saltynx.c
)

if(WIN32)
    add_executable(${PROJECT_NAME} WIN32 ${GAME_SOURCES} ${RECOMP_GEN_SOURCES})
else()
    add_executable(${PROJECT_NAME} ${GAME_SOURCES} ${RECOMP_GEN_SOURCES})
endif()

target_link_libraries(${PROJECT_NAME} PRIVATE xboxrecomp)

# AppKit owns the main thread: window and events there, the title on its own
# thread (src/apple/apple_main.c).
if(APPLE)
    enable_language(OBJC)
    enable_language(CXX)
    enable_language(OBJCXX)
    target_sources(${PROJECT_NAME} PRIVATE src/apple/apple_main.c src/apple/apple_game_state.c src/apple/apple_perf.m
                                           src/apple/apple_keyboard.c src/apple/apple_window.m
                                           src/apple/apple_menu.m src/apple/apple_player.c)
    set_source_files_properties(src/apple/apple_window.m src/apple/apple_menu.m
                                PROPERTIES COMPILE_OPTIONS "-fobjc-arc")
    set_source_files_properties(src/apple/apple_perf.m PROPERTIES COMPILE_OPTIONS "-fobjc-arc"
                                INCLUDE_DIRECTORIES "${XBOXRECOMP_DIR}/src/apu")
    target_link_libraries(${PROJECT_NAME} PRIVATE "-framework Foundation" "-framework CoreGraphics"
                          "-framework CoreText" "-framework AppKit")

    # The overlay menu (src/overlay, from the NFS Underground 2 port): Dear ImGui 1.92.9 (third_party/imgui,
    # MIT) on Metal, the Roboto Medium font (third_party/fonts, Apache-2.0) compiled in, this port's version
    # on its Advanced page.
    set(IMGUI_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/imgui)
    add_library(imgui STATIC ${IMGUI_DIR}/imgui.cpp ${IMGUI_DIR}/imgui_draw.cpp ${IMGUI_DIR}/imgui_tables.cpp
                ${IMGUI_DIR}/imgui_widgets.cpp ${IMGUI_DIR}/backends/imgui_impl_metal.mm)
    target_include_directories(imgui PUBLIC ${IMGUI_DIR} ${IMGUI_DIR}/backends)
    set_source_files_properties(${IMGUI_DIR}/backends/imgui_impl_metal.mm PROPERTIES COMPILE_OPTIONS "-fobjc-arc")
    file(READ ${CMAKE_CURRENT_SOURCE_DIR}/third_party/fonts/Roboto-Medium.ttf OVERLAY_FONT_HEX HEX)
    string(REGEX REPLACE "([0-9a-f][0-9a-f])" "0x\\1," OVERLAY_FONT_BYTES "${OVERLAY_FONT_HEX}")
    file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/generated/overlay_font.inc "${OVERLAY_FONT_BYTES}\n")
    set(PORT_VERSION "dev")
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/../VERSION)
        file(STRINGS ${CMAKE_CURRENT_SOURCE_DIR}/../VERSION PORT_VERSION LIMIT_COUNT 1)
    endif()
    execute_process(COMMAND git -C ${CMAKE_CURRENT_SOURCE_DIR} rev-parse --short HEAD
                    OUTPUT_VARIABLE PORT_COMMIT OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
    if(NOT PORT_COMMIT)
        set(PORT_COMMIT "local")
    endif()
    target_sources(${PROJECT_NAME} PRIVATE src/overlay/overlay.mm src/overlay/nfsu1_options.c)
    set_source_files_properties(src/overlay/overlay.mm PROPERTIES COMPILE_OPTIONS "-fobjc-arc"
                                INCLUDE_DIRECTORIES ${CMAKE_CURRENT_BINARY_DIR}/generated)
    set_source_files_properties(src/overlay/nfsu1_options.c PROPERTIES COMPILE_DEFINITIONS
                                "NFSU2_PORT_VERSION=\"${PORT_VERSION}\";NFSU2_PORT_COMMIT=\"${PORT_COMMIT}\"")
    target_link_libraries(${PROJECT_NAME} PRIVATE imgui "-framework Metal" "-framework QuartzCore")
    target_link_libraries(imgui PUBLIC "-framework Metal" "-framework QuartzCore" "-framework Foundation")
endif()

# Movies: VP6 decoded by FFmpeg instead of the lifted On2 decoder
# (src/movie_vp6.c). NFSU2_FFMPEG_DIR is an install of the minimal LGPL
# build from tools/build_ffmpeg_vp6.sh (libavcodec with only the vp6
# decoder); without it the lifted decoder plays the movies.
set(NFSU2_FFMPEG_DIR "" CACHE PATH "FFmpeg (vp6 decoder) install prefix")
if(NFSU2_FFMPEG_DIR)
    if(NOT EXISTS "${NFSU2_FFMPEG_DIR}/lib/libavcodec.a")
        message(FATAL_ERROR "no libavcodec.a in ${NFSU2_FFMPEG_DIR}/lib (tools/build_ffmpeg_vp6.sh)")
    endif()
    target_sources(${PROJECT_NAME} PRIVATE src/movie_vp6.c)
    target_compile_definitions(${PROJECT_NAME} PRIVATE NFSU2_NATIVE_VP6=1)
    # BEFORE: the Switch portlibs include dir has devkitPro's (GPL) FFmpeg headers.
    target_include_directories(${PROJECT_NAME} BEFORE PRIVATE "${NFSU2_FFMPEG_DIR}/include")
    target_link_libraries(${PROJECT_NAME} PRIVATE
        "${NFSU2_FFMPEG_DIR}/lib/libavcodec.a" "${NFSU2_FFMPEG_DIR}/lib/libavutil.a")
endif()

if(NFSU2_VULKAN)
    target_compile_definitions(${PROJECT_NAME} PRIVATE NFSU2_VULKAN=1)
endif()
if(NFSU2_METAL)
    target_compile_definitions(${PROJECT_NAME} PRIVATE NFSU2_METAL=1)
endif()

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${NFSU2_GEN_DIR}
    ${XBOXRECOMP_DIR}/include
)

if(WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE
        d3d11 dxgi dxguid xinput winmm dbghelp)
    if(MSVC)
        target_link_options(${PROJECT_NAME} PRIVATE /LARGEADDRESSAWARE)
        target_compile_options(${PROJECT_NAME} PRIVATE /bigobj)
    endif()
else()
    # The generated chunks are huge straight-line functions; -O1 keeps GCC's
    # memory and time per chunk sane while still allocating registers. The
    # Switch's CPU is the bottleneck there, so it gets -O2; so does Apple arm64.
    if(NINTENDO_SWITCH OR APPLE)
        set(NFSU2_GEN_OPT "-O2" CACHE STRING "Optimisation for the lifted code")
    else()
        set(NFSU2_GEN_OPT "-O1" CACHE STRING "Optimisation for the lifted code")
    endif()
    # NFSU2_LTO: link-time optimisation of the lifted code and its manual
    # overrides, so lifted callers inline each other and the native leaves
    # (_ftol2, ...). The runtime and renderers are compiled as usual.
    # NFSU2_LTO_JOBS parallel LTRANS jobs (memory: ~1-2 GB each).
    option(NFSU2_LTO "Link-time optimisation of the lifted code" OFF)
    set(NFSU2_LTO_JOBS "4" CACHE STRING "Parallel LTO link jobs")
    # -ffp-contract=off: x86 rounds every SSE mul and add; GCC on AArch64
    # fuses a*b+c into fmadd by default, so the Switch computed different
    # floats from the same guest code.
    set(NFSU2_GEN_FLAGS "${NFSU2_GEN_OPT};-w;-fno-strict-aliasing;-fwrapv;-ffp-contract=off")
    if(NFSU2_LTO)
        list(APPEND NFSU2_GEN_FLAGS "-flto=auto")
        set_property(SOURCE src/recomp_manual.c APPEND PROPERTY
            COMPILE_OPTIONS "-flto=auto;-fno-strict-aliasing;-fwrapv;-ffp-contract=off")
        target_link_options(${PROJECT_NAME} PRIVATE
            "-flto=${NFSU2_LTO_JOBS}" "-flto-partition=balanced" ${NFSU2_GEN_OPT})
    endif()
    set_source_files_properties(${RECOMP_GEN_SOURCES} PROPERTIES
        COMPILE_OPTIONS "${NFSU2_GEN_FLAGS}")
    target_link_libraries(${PROJECT_NAME} PRIVATE m)
endif()

# ── Nintendo Switch homebrew (devkitA64 + libnx) ────────────────
#
# Build with switch/build.sh. The NRO reads the extracted disc from
# sdmc:/switch/nfsu1x/game/ (never an ISO); logs and nfsu1x_env.txt live in
# sdmc:/switch/nfsu1x/.
if(NINTENDO_SWITCH)
    set(NFSU2_SWITCH_APP_NAME "NFS Underground (Xbox recomp)" CACHE STRING
        "Title shown in the homebrew menu")
    set(NFSU2_SWITCH_AUTHOR "nfsu2-xbox" CACHE STRING "Author shown in the homebrew menu")
    # The release lives here, not in the cache: a cached default stays at
    # whatever the build directory was first configured with.
    # -DNFSU2_SWITCH_VERSION_OVERRIDE=x sets another one.
    set(NFSU2_SWITCH_VERSION "0.4.0")
    if(NFSU2_SWITCH_VERSION_OVERRIDE)
        set(NFSU2_SWITCH_VERSION "${NFSU2_SWITCH_VERSION_OVERRIDE}")
    endif()
    set(NFSU2_SWITCH_ICON "${CMAKE_CURRENT_SOURCE_DIR}/assets/icon.jpg" CACHE FILEPATH
        "256x256 JPEG icon (libnx default when empty)")

    if(NFSU2_VULKAN)
        # No GL: SDL is only the audio output; NVK comes with nv2a_vk.
        target_link_libraries(${PROJECT_NAME} PRIVATE nx m)
    else()
        # switch-sdl2's GL path is EGL on switch-mesa.
        target_link_libraries(${PROJECT_NAME} PRIVATE EGL glapi drm_nouveau nx m)
    endif()
    # SDL's audio thread gets a real-time priority and audren gaps are
    # counted (switch_nx.c, "SDL's audio thread").
    target_link_options(${PROJECT_NAME} PRIVATE
        "LINKER:--wrap=SDL_SYS_SetThreadPriority"
        "LINKER:--wrap=audrvVoiceAddWaveBuf")
    set_property(SOURCE src/switch_nx.c APPEND PROPERTY
        INCLUDE_DIRECTORIES "${XBOXRECOMP_DIR}/src/apu")
    # switch_nx.c's loading screen asks EGL for the on-screen size.
    target_include_directories(${PROJECT_NAME} PRIVATE "$ENV{DEVKITPRO}/portlibs/switch/include")

    set(NFSU2_NACP "${CMAKE_CURRENT_BINARY_DIR}/nfsu1x.nacp")
    nx_generate_nacp(OUTPUT "${NFSU2_NACP}"
        NAME "${NFSU2_SWITCH_APP_NAME}"
        AUTHOR "${NFSU2_SWITCH_AUTHOR}"
        VERSION "${NFSU2_SWITCH_VERSION}")
    if(NFSU2_SWITCH_ICON)
        nx_create_nro(${PROJECT_NAME} NACP "${NFSU2_NACP}" ICON "${NFSU2_SWITCH_ICON}")
    else()
        nx_create_nro(${PROJECT_NAME} NACP "${NFSU2_NACP}")
    endif()
endif()
