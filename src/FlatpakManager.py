#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flatpak Manager for Pars Linux Software Center
Handles flatpak query, install, uninstall, update, launch, progress parsing, and sandbox permissions.
"""

import os
import re
import shutil
import subprocess
import threading
from Logger import Logger


class FlatpakManager:
    def __init__(self):
        self.Logger = Logger(__name__)
        self.flatpak_bin = shutil.which("flatpak") or "/usr/bin/flatpak"
        self._installed_cache = {}
        self._permissions_cache = {}
        self._lock = threading.Lock()
        self.refresh_installed()

    def is_available(self):
        return os.path.exists(self.flatpak_bin) and os.access(self.flatpak_bin, os.X_OK)

    def refresh_installed(self):
        """Refresh local cache of installed Flatpak apps"""
        if not self.is_available():
            return {}

        cmd = [
            self.flatpak_bin,
            "list",
            "--app",
            "--noninteractive",
            "--columns=application,name,version,branch,arch,origin",
        ]
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            installed = {}
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()
                for line in lines:
                    parts = [p.strip() for p in line.split("\t") if p.strip()]
                    if not parts:
                        continue
                    app_id = parts[0]
                    if app_id in ("Uygulama Kimliği", "Application ID", "Application"):
                        continue
                    name = parts[1] if len(parts) > 1 else app_id
                    version = parts[2] if len(parts) > 2 else ""
                    installed[app_id] = {
                        "app_id": app_id,
                        "name": name,
                        "version": version,
                    }
            with self._lock:
                self._installed_cache = installed
            self.Logger.info(f"Loaded {len(self._installed_cache)} installed Flatpak applications.")
            return self._installed_cache
        except Exception as e:
            self.Logger.exception(f"Error checking installed Flatpaks: {e}")
            return {}

    def is_installed(self, app_id):
        with self._lock:
            return app_id in self._installed_cache

    def get_installed_version(self, app_id):
        with self._lock:
            info = self._installed_cache.get(app_id)
            return info.get("version", "") if info else None

    def get_installed_apps(self):
        with self._lock:
            return list(self._installed_cache.values())

    @staticmethod
    def parse_progress(line):
        """
        Parses Flatpak CLI output line for percentage and status text.
        Returns (percent_int, status_text) or (None, line)
        """
        if not line:
            return None, ""

        clean = line.strip()
        match = re.search(r"(\d{1,3})\s*%", clean)
        percent = int(match.group(1)) if match else None

        if percent is not None and percent > 100:
            percent = 100

        # Determine phase
        lower = clean.lower()
        if "download" in lower or "indir" in lower:
            status = "İndiriliyor"
        elif "install" in lower or "kurul" in lower or "yükle" in lower:
            status = "Yükleniyor"
        elif "update" in lower or "güncell" in lower:
            status = "Güncelleniyor"
        elif "uninstall" in lower or "kaldır" in lower:
            status = "Kaldırılıyor"
        else:
            status = "İşleniyor"

        return percent, f"{status} ({percent}%)" if percent is not None else clean

    def install(self, app_id, remote="flathub", user_mode=True, on_progress=None, on_finish=None):
        """Asynchronously install a flatpak package with progress streaming"""
        cmd = [self.flatpak_bin, "install", "-y", "--noninteractive"]
        if user_mode:
            cmd.append("--user")
        cmd.extend([remote, app_id])

        def _worker():
            self.Logger.info(f"Starting installation: {' '.join(cmd)}")
            success = False
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                for line in iter(proc.stdout.readline, ""):
                    if on_progress:
                        percent, status = self.parse_progress(line)
                        on_progress(percent, status, line)
                proc.stdout.close()
                proc.wait()
                success = proc.returncode == 0
            except Exception as e:
                self.Logger.exception(f"Flatpak install error: {e}")
                if on_progress:
                    on_progress(None, f"Hata: {e}", f"Hata: {e}\n")

            self.refresh_installed()
            if on_finish:
                on_finish(success)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def uninstall(self, app_id, on_progress=None, on_finish=None):
        """Asynchronously uninstall a flatpak package"""
        cmd = [self.flatpak_bin, "uninstall", "-y", "--noninteractive", app_id]

        def _worker():
            self.Logger.info(f"Starting uninstall: {' '.join(cmd)}")
            success = False
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                for line in iter(proc.stdout.readline, ""):
                    if on_progress:
                        percent, status = self.parse_progress(line)
                        on_progress(percent, status, line)
                proc.stdout.close()
                proc.wait()
                success = proc.returncode == 0
            except Exception as e:
                self.Logger.exception(f"Flatpak uninstall error: {e}")
                if on_progress:
                    on_progress(None, f"Hata: {e}", f"Hata: {e}\n")

            self.refresh_installed()
            if on_finish:
                on_finish(success)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def update(self, app_id, on_progress=None, on_finish=None):
        """Asynchronously update a flatpak package"""
        cmd = [self.flatpak_bin, "update", "-y", "--noninteractive", app_id]

        def _worker():
            self.Logger.info(f"Starting update: {' '.join(cmd)}")
            success = False
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                for line in iter(proc.stdout.readline, ""):
                    if on_progress:
                        percent, status = self.parse_progress(line)
                        on_progress(percent, status, line)
                proc.stdout.close()
                proc.wait()
                success = proc.returncode == 0
            except Exception as e:
                self.Logger.exception(f"Flatpak update error: {e}")
                if on_progress:
                    on_progress(None, f"Hata: {e}", f"Hata: {e}\n")

            self.refresh_installed()
            if on_finish:
                on_finish(success)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def get_permissions(self, app_id):
        """
        Inspects application sandbox permissions (network, filesystem, audio, display, devices).
        Returns a dict of permissions and visual badges.
        """
        with self._lock:
            if app_id in self._permissions_cache:
                return self._permissions_cache[app_id]

        metadata_text = ""
        try:
            if self.is_installed(app_id):
                res = subprocess.run(
                    [self.flatpak_bin, "info", "-m", app_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0:
                    metadata_text = res.stdout
            else:
                res = subprocess.run(
                    [self.flatpak_bin, "remote-info", "-m", "--noninteractive", "flathub", app_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=4,
                )
                if res.returncode == 0:
                    metadata_text = res.stdout
        except Exception as e:
            self.Logger.debug(f"Permissions lookup exception for {app_id}: {e}")

        perms = {
            "network": False,
            "filesystem": "Isolated",
            "audio": False,
            "display": "None",
            "devices": False,
            "items": [],
        }

        if metadata_text:
            for line in metadata_text.splitlines():
                line = line.strip()
                if line.startswith("shared="):
                    if "network" in line:
                        perms["network"] = True
                        perms["items"].append(
                            ("network-transmit-receive-symbolic", "İnternet Erişimi")
                        )
                elif line.startswith("sockets="):
                    if "pulseaudio" in line:
                        perms["audio"] = True
                        perms["items"].append(
                            ("audio-volume-high-symbolic", "Ses Çıkışı ve Girişi")
                        )
                    has_wayland = "wayland" in line
                    has_x11 = "x11" in line
                    if has_wayland and has_x11:
                        perms["display"] = "Wayland & X11"
                        perms["items"].append(
                            ("video-display-symbolic", "Pencere Yöneticisi (Wayland / X11)")
                        )
                    elif has_wayland:
                        perms["display"] = "Wayland"
                        perms["items"].append(
                            ("video-display-symbolic", "Pencere Yöneticisi (Wayland)")
                        )
                    elif has_x11:
                        perms["display"] = "X11"
                        perms["items"].append(
                            ("video-display-symbolic", "Pencere Yöneticisi (X11)")
                        )
                elif line.startswith("devices="):
                    if "all" in line or "video" in line:
                        perms["devices"] = True
                        perms["items"].append(
                            ("camera-web-symbolic", "Kamera ve Donanım Aygıtları")
                        )
                elif line.startswith("filesystems="):
                    if "host" in line:
                        perms["filesystem"] = "Tam Sistem Erişimi"
                        perms["items"].append(
                            ("drive-harddisk-symbolic", "Tüm Dosya Sistemine Erişim")
                        )
                    elif "home" in line:
                        perms["filesystem"] = "Kullanıcı Ev Dizini"
                        perms["items"].append(
                            ("user-home-symbolic", "Kullanıcı Ev Dizinine Erişim")
                        )
                    elif "xdg-download" in line:
                        perms["filesystem"] = "İndirilenler Klasörü"
                        perms["items"].append(
                            ("folder-download-symbolic", "İndirilenler Klasörüne Erişim")
                        )

        if not perms["items"]:
            perms["items"].append(
                ("security-high-symbolic", "Güvenli Sandbox (İzole Edilmiş)")
            )

        with self._lock:
            self._permissions_cache[app_id] = perms

        return perms

    def get_permission_overrides(self, app_id):
        """
        Returns active overrides and effective states for common sandbox permissions.
        Key permissions: network, filesystem_home, filesystem_host, socket_x11, socket_wayland, socket_pulseaudio, device_all
        """
        if not self.is_available() or not app_id:
            return {}

        base_perms = self.get_permissions(app_id)
        overrides_path = os.path.expanduser(f"~/.local/share/flatpak/overrides/{app_id}")
        raw_overrides = ""
        if os.path.exists(overrides_path):
            try:
                with open(overrides_path, "r", encoding="utf-8") as f:
                    raw_overrides = f.read()
            except Exception as e:
                self.Logger.warning(f"Could not read overrides for {app_id}: {e}")

        states = {
            "network": {
                "label": "İnternet Erişimi",
                "icon": "network-transmit-receive-symbolic",
                "default": bool(base_perms.get("network")),
                "effective": bool(base_perms.get("network")),
                "overridden": False,
            },
            "filesystem_home": {
                "label": "Kullanıcı Ev Dizini (~/)",
                "icon": "user-home-symbolic",
                "default": "Kullanıcı Ev Dizini" in str(base_perms.get("filesystem", "")) or "Tam Sistem Erişimi" in str(base_perms.get("filesystem", "")),
                "effective": "Kullanıcı Ev Dizini" in str(base_perms.get("filesystem", "")) or "Tam Sistem Erişimi" in str(base_perms.get("filesystem", "")),
                "overridden": False,
            },
            "filesystem_host": {
                "label": "Tüm Dosya Sistemi (/)",
                "icon": "drive-harddisk-symbolic",
                "default": "Tam Sistem Erişimi" in str(base_perms.get("filesystem", "")),
                "effective": "Tam Sistem Erişimi" in str(base_perms.get("filesystem", "")),
                "overridden": False,
            },
            "socket_wayland": {
                "label": "Wayland Ekran Sunucusu",
                "icon": "video-display-symbolic",
                "default": "Wayland" in str(base_perms.get("display", "")),
                "effective": "Wayland" in str(base_perms.get("display", "")),
                "overridden": False,
            },
            "socket_x11": {
                "label": "X11 Ekran Sunucusu",
                "icon": "video-display-symbolic",
                "default": "X11" in str(base_perms.get("display", "")),
                "effective": "X11" in str(base_perms.get("display", "")),
                "overridden": False,
            },
            "socket_pulseaudio": {
                "label": "Ses Çıkışı ve Girişi",
                "icon": "audio-volume-high-symbolic",
                "default": bool(base_perms.get("audio")),
                "effective": bool(base_perms.get("audio")),
                "overridden": False,
            },
            "device_all": {
                "label": "Kamera ve Donanım Aygıtları",
                "icon": "camera-web-symbolic",
                "default": bool(base_perms.get("devices")),
                "effective": bool(base_perms.get("devices")),
                "overridden": False,
            },
        }

        if raw_overrides:
            for line in raw_overrides.splitlines():
                line = line.strip()
                if line.startswith("shared="):
                    if "!network" in line:
                        states["network"]["effective"] = False
                        states["network"]["overridden"] = True
                    elif "network" in line:
                        states["network"]["effective"] = True
                        states["network"]["overridden"] = True
                elif line.startswith("sockets="):
                    if "!pulseaudio" in line:
                        states["socket_pulseaudio"]["effective"] = False
                        states["socket_pulseaudio"]["overridden"] = True
                    elif "pulseaudio" in line:
                        states["socket_pulseaudio"]["effective"] = True
                        states["socket_pulseaudio"]["overridden"] = True
                    if "!wayland" in line:
                        states["socket_wayland"]["effective"] = False
                        states["socket_wayland"]["overridden"] = True
                    elif "wayland" in line:
                        states["socket_wayland"]["effective"] = True
                        states["socket_wayland"]["overridden"] = True
                    if "!x11" in line:
                        states["socket_x11"]["effective"] = False
                        states["socket_x11"]["overridden"] = True
                    elif "x11" in line:
                        states["socket_x11"]["effective"] = True
                        states["socket_x11"]["overridden"] = True
                elif line.startswith("filesystems="):
                    if "!home" in line:
                        states["filesystem_home"]["effective"] = False
                        states["filesystem_home"]["overridden"] = True
                    elif "home" in line:
                        states["filesystem_home"]["effective"] = True
                        states["filesystem_home"]["overridden"] = True
                    if "!host" in line:
                        states["filesystem_host"]["effective"] = False
                        states["filesystem_host"]["overridden"] = True
                    elif "host" in line:
                        states["filesystem_host"]["effective"] = True
                        states["filesystem_host"]["overridden"] = True
                elif line.startswith("devices="):
                    if "!all" in line:
                        states["device_all"]["effective"] = False
                        states["device_all"]["overridden"] = True
                    elif "all" in line:
                        states["device_all"]["effective"] = True
                        states["device_all"]["overridden"] = True

        return states

    def set_permission_override(self, app_id, permission_key, enable):
        """
        Configures user permission override using 'flatpak override --user'
        """
        if not self.is_available() or not app_id:
            return False

        flag_map = {
            "network": "--share=network" if enable else "--unshare=network",
            "filesystem_home": "--filesystem=home" if enable else "--nofilesystem=home",
            "filesystem_host": "--filesystem=host" if enable else "--nofilesystem=host",
            "socket_wayland": "--socket=wayland" if enable else "--nosocket=wayland",
            "socket_x11": "--socket=x11" if enable else "--nosocket=x11",
            "socket_pulseaudio": "--socket=pulseaudio" if enable else "--nosocket=pulseaudio",
            "device_all": "--device=all" if enable else "--nodevice=all",
        }

        flag = flag_map.get(permission_key)
        if not flag:
            self.Logger.error(f"Unknown permission key: {permission_key}")
            return False

        cmd = [self.flatpak_bin, "override", "--user", flag, app_id]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode == 0:
                with self._lock:
                    self._permissions_cache.pop(app_id, None)
                self.Logger.info(f"Set permission {permission_key}={enable} for {app_id}")
                return True
            else:
                self.Logger.error(f"Failed to set permission for {app_id}: {res.stderr}")
                return False
        except Exception as e:
            self.Logger.exception(f"Error overriding permission: {e}")
            return False

    def reset_permissions(self, app_id):
        """Resets all user permission overrides for the application"""
        if not self.is_available() or not app_id:
            return False

        cmd = [self.flatpak_bin, "override", "--user", "--reset", app_id]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            with self._lock:
                self._permissions_cache.pop(app_id, None)
            self.Logger.info(f"Reset permissions for {app_id}")
            return res.returncode == 0
        except Exception as e:
            self.Logger.exception(f"Error resetting permissions for {app_id}: {e}")
            return False

    def get_upgradable_apps(self, force_refresh=False):
        """
        Scans remote repositories for pending Flatpak updates.
        Returns dict: {app_id: {'candidate_version': ..., 'branch': ..., 'arch': ...}}
        """
        if not self.is_available():
            return {}

        if not force_refresh and hasattr(self, "_upgradable_cache") and self._upgradable_cache is not None:
            return self._upgradable_cache

        cmd = [
            self.flatpak_bin,
            "remote-ls",
            "--updates",
            "--app",
            "--columns=application,version,branch,arch",
        ]
        env = dict(os.environ, LC_ALL="C")
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, env=env)
            upgradables = {}
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()
                for line in lines:
                    parts = [p.strip() for p in line.split("\t") if p.strip()]
                    if not parts or len(parts) < 1:
                        # Fallback split by whitespace if tab not used
                        parts = line.split()
                    if not parts:
                        continue
                    app_id = parts[0]
                    if app_id in ("Application", "Application ID", "Uygulama Kimliği"):
                        continue
                    version = parts[1] if len(parts) > 1 else ""
                    branch = parts[2] if len(parts) > 2 else "stable"
                    arch = parts[3] if len(parts) > 3 else "x86_64"
                    upgradables[app_id] = {
                        "name": app_id,
                        "candidate_version": version,
                        "branch": branch,
                        "arch": arch,
                    }

            with self._lock:
                self._upgradable_cache = upgradables
            self.Logger.info(f"Found {len(upgradables)} upgradable Flatpak apps: {list(upgradables.keys())}")
            return upgradables
        except Exception as e:
            self.Logger.warning(f"Error checking Flatpak updates: {e}")
            return {}

    def is_upgradable(self, app_id):
        """Returns True if the specified flatpak has a pending update"""
        upgradables = self.get_upgradable_apps()
        return app_id in upgradables

    def update_all(self, progress_callback=None):
        """
        Updates all flatpak applications non-interactively.
        """
        if not self.is_available():
            return False

        cmd = [self.flatpak_bin, "update", "-y", "--noninteractive"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                if progress_callback:
                    pct, msg = self.parse_progress(line)
                    progress_callback(pct, msg)
            proc.wait()
            with self._lock:
                self._upgradable_cache = None
            self.refresh_installed()
            return proc.returncode == 0
        except Exception as e:
            self.Logger.exception(f"Error updating flatpaks: {e}")
            return False

    def launch(self, app_id):
        """Launch a flatpak application in the background"""
        cmd = [self.flatpak_bin, "run", app_id]
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.Logger.info(f"Launched {app_id}")
            return True
        except Exception as e:
            self.Logger.exception(f"Failed to launch {app_id}: {e}")
            return False

