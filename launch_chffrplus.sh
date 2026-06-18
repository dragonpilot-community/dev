#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

source "$DIR/launch_env.sh"

# dp - feature launch hooks.
#
# A feature ships ONE file, dragonpilot/launch/NN_<name>.sh, containing its
# function(s) and appending the entry point to DP_LAUNCH_HOOKS:
#
#     set_lite_hw() { ... }
#     DP_LAUNCH_HOOKS="$DP_LAUNCH_HOOKS set_lite_hw"
#
# The NN prefix sets run order, which matters: set_tici_hw exports TICI_DOS/TICI_TRES
# that later hooks depend on. Order used to be implicit in merge order - the same
# class of bug the DPFlags bit numbering had. Reserve 00-49 for hardware detection,
# 50-99 for anything that depends on it.
#
# Features never edit this file, so they cannot collide here. Previously each one
# appended a function body AND a call at two shared anchors, and a bad resolution
# could leave a function unterminated - swallowing the next definition with no
# syntax error.
DP_LAUNCH_HOOKS=""
for _dp_hook in "$DIR"/dragonpilot/launch/*.sh; do
  [ -f "$_dp_hook" ] && source "$_dp_hook"
done
unset _dp_hook

function dp_run_launch_hooks {
  local _fn
  for _fn in $DP_LAUNCH_HOOKS; do
    if command -v "$_fn" >/dev/null 2>&1; then
      "$_fn"
    else
      echo "dp: launch hook '$_fn' declared but not defined; skipping"
    fi
  done
}

function agnos_init {
  # TODO: move this to agnos
  sudo rm -f /data/etc/NetworkManager/system-connections/*.nmmeta
  rm -f /data/scons_cache/config.lock

  # set success flag for current boot slot
  sudo abctl --set_success

  # TODO: do this without udev in AGNOS
  # udev does this, but sometimes we startup faster
  sudo chgrp gpu /dev/adsprpc-smd /dev/ion /dev/kgsl-3d0
  sudo chmod 660 /dev/adsprpc-smd /dev/ion /dev/kgsl-3d0

  # Check if AGNOS update is required
  if [ $(< /VERSION) != "$AGNOS_VERSION" ]; then
    AGNOS_PY="$DIR/system/hardware/tici/agnos.py"
    MANIFEST="$DIR/system/hardware/tici/agnos.json"
    if $AGNOS_PY --verify $MANIFEST; then
      sudo reboot
    fi
    $DIR/system/hardware/tici/updater $AGNOS_PY $MANIFEST
  fi
}

# Determine the panda MCU type (F4=DOS, H7=TRES) and set the TICI_* env vars.
# The MCU type is a permanent hardware fact, so it is detected once and cached in
# /persist (survives fork switch / reset / reflash); every later boot reads the
# cache and skips the panda query entirely.
set_tici_hw() {
  grep -q "tici" /sys/firmware/devicetree/base/model 2>/dev/null || return 0
  export TICI_HW=1

  local cache="/persist/dp_dev_panda_mcu_type"
  local attempts=15 confirm=3         # give up after N reads; trust after M in a row
  local mcu="" count=0 last="" cur cached

  # --- fast path: trust a valid (F4/H7) cached value, no panda query or sleep ---
  cached=$(cat "$cache" 2>/dev/null)
  case "$cached" in
    F4|H7) mcu="$cached"; echo "panda MCU $mcu [cached]" ;;
  esac

  # --- slow path: detect, requiring M consecutive identical reads to reject a
  #     transient misread while the panda enumerates, then persist for next boot ---
  if [ -z "$mcu" ]; then
    echo "Querying panda MCU type..."
    for attempt in $(seq 1 "$attempts"); do
      # wait long while the panda is still coming up, short between confirmations
      if [ -n "$last" ]; then sleep 1; else sleep 3; fi

      # Transport is the DOS/TRES discriminator: TRES=SPI (H7), DOS=USB (F4). With
      # more than one panda attached, prefer the internal SPI panda (so an external
      # USB panda can't win on a C3/C3X), falling back to the first USB panda for
      # USB-only hardware (DOS/lite). Panda.list() is unordered (it set()s), so the
      # preference order is built explicitly.
      case "$(python -c "from panda_tici import Panda; s = Panda.spi_list() or sorted(Panda.usb_list()); p = Panda(serial=(s[0] if s else None), cli=False); print(p.get_mcu_type()); p.close()" 2>/dev/null)" in
        *McuType.F4*) cur="F4" ;;
        *McuType.H7*) cur="H7" ;;
        *)            cur="" ;;
      esac

      if [ -n "$cur" ] && [ "$cur" = "$last" ]; then
        count=$((count + 1))
      else
        count=1
        last="$cur"
      fi

      if [ -n "$cur" ] && [ "$count" -ge "$confirm" ]; then
        mcu="$cur"
        break
      fi
      echo "panda MCU read='${cur:-UNKNOWN}' (confirmed $count/$confirm, attempt $attempt/$attempts)"
    done

    if [ -z "$mcu" ]; then
      echo "TICI (UNKNOWN) detected after $attempts attempts, stop processing."
      exit 1
    fi

    # Persist it so future boots skip detection. /persist is comma's protected,
    # read-only partition, so flip it rw just for this one write (happens once per
    # device) and back to ro. The fast-path cat above reads fine on a ro mount, so
    # only the write needs this. Any failure here is non-fatal: re-detect next boot.
    if sudo mount -o remount,rw /persist 2>/dev/null; then
      echo "$mcu" | sudo tee "$cache" >/dev/null 2>&1
      sudo mount -o remount,ro /persist 2>/dev/null
    fi
  fi

  # --- apply: DOS (F4) also mounts the NVMe; TRES (H7) does not ---
  if [ "$mcu" = "F4" ]; then
    echo "TICI (DOS) detected"
    mount_nvme
    export TICI_DOS=1
  else
    echo "TICI (TRES) detected"
    export TICI_TRES=1
  fi
}

mount_nvme() {
  for i in $(seq 1 10); do
    [ -b /dev/nvme0n1p1 ] && break
    sleep 1
  done

  # Returns 0 (success) so the boot process continues without errors
  if [ ! -b /dev/nvme0n1p1 ]; then
    return 0
  fi

  # We assume /data/media/0/realdata exists per defaults
  if ! mountpoint -q /data/media/0/realdata; then
    mount /dev/nvme0n1p1 /data/media/0/realdata
  fi

  if mountpoint -q /data/media/0/realdata; then
    OWNER="$(stat -c '%U' /data/media/0/realdata)"
    GROUP="$(stat -c '%G' /data/media/0/realdata)"
    PERM="$(stat -c '%a' /data/media/0/realdata)"

    if [ "$OWNER" != "comma" ] || [ "$GROUP" != "comma" ]; then
      chown comma:comma /data/media/0/realdata
    fi

    if [ "$PERM" != "755" ]; then
      chmod 755 /data/media/0/realdata
    fi
  fi
}

function launch {
  # Remove orphaned git lock if it exists on boot
  [ -f "$DIR/.git/index.lock" ] && rm -f $DIR/.git/index.lock

  # Check to see if there's a valid overlay-based update available. Conditions
  # are as follows:
  #
  # 1. The DIR init file has to exist, with a newer modtime than anything in
  #    the DIR Git repo. This checks for local development work or the user
  #    switching branches/forks, which should not be overwritten.
  # 2. The FINALIZED consistent file has to exist, indicating there's an update
  #    that completed successfully and synced to disk.

  if [ -f "${DIR}/.overlay_init" ]; then
    find ${DIR}/.git -newer ${DIR}/.overlay_init | grep -q '.' 2> /dev/null
    if [ $? -eq 0 ]; then
      echo "${DIR} has been modified, skipping overlay update installation"
    else
      if [ -f "${STAGING_ROOT}/finalized/.overlay_consistent" ]; then
        if [ ! -d /data/safe_staging/old_openpilot ]; then
          echo "Valid overlay update found, installing"
          LAUNCHER_LOCATION="${BASH_SOURCE[0]}"

          mv $DIR /data/safe_staging/old_openpilot
          mv "${STAGING_ROOT}/finalized" $DIR
          cd $DIR

          echo "Restarting launch script ${LAUNCHER_LOCATION}"
          unset AGNOS_VERSION
          exec "${LAUNCHER_LOCATION}"
        else
          echo "openpilot backup found, not updating"
          # TODO: restore backup? This means the updater didn't start after swapping
        fi
      fi
    fi
  fi

  # handle pythonpath
  ln -sfn $(pwd) /data/pythonpath
  export PYTHONPATH="$PWD"

  # hardware specific init
  if [ -f /AGNOS ]; then
    # dp - feature hooks run before agnos_init so hardware detection (TICI_DOS/
    # TICI_TRES) is available to everything after it. Relative order among hooks
    # comes from the NN_ filename prefix in dragonpilot/launch/.
    dp_run_launch_hooks
    agnos_init
  fi

  # write tmux scrollback to a file
  tmux capture-pane -pq -S-1000 > /tmp/launch_log

  # start manager
  cd system/manager
  if [ ! -f $DIR/prebuilt ]; then
    ./build.py
  fi
  ./manager.py

  # if broken, keep on screen error
  while true; do sleep 1; done
}

launch
