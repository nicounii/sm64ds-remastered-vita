# sm64ds-remastered
Fork of [AloXado320/sm64ex-alo](https://github.com/AloUltraExt/sm64ex-alo)
 
## Backends included
 * Same ones as in [sm64ex](https://github.com/sm64pc/sm64ex/tree/nightly) (macOS - Raspberry Pi Series - Windows - Linux), etc.
 * [Nintendo 64](https://github.com/n64decomp/sm64) along with some slight [HackerSM64](https://github.com/HackerN64/HackerSM64) changes.
 * [Nintendo Wii U](https://github.com/aboood40091/sm64ex/tree/nightly) (by AboodXD)
 * [Nintendo 3DS](https://github.com/mkst/sm64-port) (by Fnouwt, mkst)
 * [Nintendo Switch](https://github.com/fgsfdsfgs/sm64ex/tree/switch) (by Vatuu, fgsfdsfgs, KiritoDev)
 * [Android](https://github.com/VDavid003/sm64-port-android/tree/ex/nightly) (by VDavid003)

## Building
 ### Clone the repository:

 ```sh
 git clone https://github.com/ExcellentGamer/sm64ds-remastered
 cd sm64ds-remastered
 ```
 
 **Note:** On Unix systems you may need to do this before doing any changes:
 
 ```sh
 git config core.fileMode false
 chmod -R 777 .
 ```
 
 ### Copy baserom(s) for asset extraction:
 
 For each version (jp/us/eu/sh) for which you want to build an executable, put an existing ROM at `./baserom.<VERSION>.z64` for asset extraction.
 
 By default it builds the US version.

<details>
  <summary>To build for N64, click here.</summary>
 
  **Note:** Only tested in WSL, works on (Debian / Ubuntu) as well, other distros untested.

  #### Install build dependencies:
  ```sh
  sudo apt install -y binutils-mips-linux-gnu build-essential git pkgconf python3 gcc-mips-linux-gnu
  ```

  #### Build:
  ```sh
  # if you have more cores available, you can increase the -j parameter
  make -j4 =1 
  ```
 
  #### ROM location:
  ```sh
  build/us/sm64dsr.us.(currentver).z64
  ```

</details>

<details>
  <summary>To build for Android, click here.</summary>
 
  **Note:** Only Termux build is supported.
 
  #### Install Termux
 
  Install the app from F-Droid [here](https://f-droid.org/en/packages/com.termux/)
 
  Make sure you use this version, as the Google Play version is outdated.

  #### Install build dependencies
  ```sh
  pkg install git wget make python getconf zip apksigner clang binutils
  ```

  #### Copy in your baserom:

  Do this using your default file manager (on AOSP, you can slide on the left and there will be a "Termux" option there), or using Termux.
  ```sh
  termux-setup-storage
  cp /sdcard/path/to/your/baserom.z64 ./baserom.us.z64
  ```

  #### Install external dependencies
  ```sh
  cd platform/android/ && ./getkhrplatform.sh && ./getSDL.sh && cd ../..
  ```
 
  #### Build
  ```sh
  # if you have more cores available, you can increase the -j parameter
  # On Termux, TARGET_ANDROID=1 is defined automatically in Makefile
  make -j4
  ```

 #### Install apk:
  ```sh
  xdg-open build/us_android/sm64dsr.us.(currentver).apk
  ```
 
</details>

<details>
  <summary>To build for PS Vita, click here.</summary>

  Requires FW 3.60+ (HENkaku/enso recommended).

  #### Install VitaSDK:

  ```sh
  # Install vitasdk (Linux)
  export VITASDK=/usr/local/vitasdk
  curl -sL https://github.com/vitasdk/vdpm/raw/master/last_built_toolchain.py | python3 - master linux | tar xj -C $VITASDK --strip-components=1
  # Install common libs
  git clone https://github.com/vitasdk/vdpm.git
  for pkg in zlib freetype bzip2 libpng sdl2 sdl2_mixer vitaGL; do
    ./vdpm/vdpm -f $pkg
  done
  ```

  #### Build VPK:
  ```sh
  make TARGET_VITA=1 -j$(nproc) vpk
  ```

  #### Output:
  ```sh
  build/us_vita/sm64dsr.us.vpk
  ```

  #### Install on Vita:
  1. Transfer the VPK to your Vita via **FTP** (USB in VitaShell 1.95 is buggy).
  2. Install with VitaShell (hold L on launch if USB errors occur).
  3. If installation fails:
     - Delete `ux0:/patch/SM64DSR01/` if it exists from a prior install
     - Ensure PNG assets are <420KB with indexed palette (already optimized)
     - Ensure VPK contains no `sce_sys/package/` files (checked in CI)

  #### CI (GitHub Actions):
  The repo includes `.github/workflows/vita.yml` which builds and validates
  every push/PR:
  - ✅ Cross-compiles in `vitasdk/vitasdk:latest` Docker container
  - ✅ Validates VPK structure (SCE magic, required files, PNG size limits)
  - ✅ Detects forbidden `sce_sys/package/` files (causes 0x80870005)
  - 🧪 Experimental headless Vita3K runtime test

</details>

 * To build for sm64ex platforms, [click here](https://github.com/sm64pc/sm64ex/blob/nightly/README.md).
 * To build for Wii U, [click here](https://github.com/aboood40091/sm64-port/blob/master/README.md). (TARGET_WII_U=1)
 * To build for 3DS, [click here](https://github.com/sm64-port/sm64_3ds/blob/master/README.md). (TARGET_N3DS=1)
 * To build for Switch, [click here](https://github.com/fgsfdsfgs/sm64ex/blob/switch/README.md). (TARGET_SWITCH=1)
