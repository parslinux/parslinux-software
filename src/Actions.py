#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import subprocess
import sys
import pwd
import signal
try:
    import psutil
except ImportError:
    psutil = None
try:
    import apt
    import apt_pkg
    HAS_APT = True
except ImportError:
    apt = None
    apt_pkg = None
    HAS_APT = False
import re


def is_flatpak_package(packages):
    parts = packages.split()
    for p in parts:
        if "." in p and not p.endswith(".deb") and not p.startswith("-"):
            return True
    return False


def main():
    def control_lock():
        if not HAS_APT or not apt_pkg:
            return True
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError as e:
            print(e, file=sys.stderr)
            return False
        apt_pkg.pkgsystem_unlock()
        return True

    def parse_packages(packages):
        packagelist = packages.split()

        valid_packages = []
        apt_options = []

        package_re = re.compile(r'^[a-z0-9][a-z0-9+.-]*(?::[a-z0-9]+)?$')

        for item in packagelist:
            if item == "--no-install-recommends":
                apt_options.append(item)
            elif package_re.fullmatch(item):
                valid_packages.append(item)
            else:
                raise ValueError(f"Invalid package name: {item}")

        return apt_options, valid_packages

    def install(packages):
        if is_flatpak_package(packages):
            cmd = ["flatpak", "install", "-y", "--noninteractive", "flathub"] + packages.split()
            subprocess.call(cmd)
            return

        apt_options, valid_packages = parse_packages(packages)

        if not valid_packages:
            print("No valid package was found to install.")
            return

        cmd = ["apt", "install", "-yq", "-o", "APT::Status-Fd=2"] + apt_options + ["--"] + valid_packages
        subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def remove(packages):
        if is_flatpak_package(packages):
            cmd = ["flatpak", "uninstall", "-y", "--noninteractive"] + packages.split()
            subprocess.call(cmd)
            return

        apt_options, valid_packages = parse_packages(packages)

        if not valid_packages:
            print("No valid package was found to remove.")
            return

        cmd = ["apt", "remove", "--purge", "-yq", "-o", "APT::Status-Fd=2"] + apt_options + ["--"] + valid_packages
        subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def upgrade(packages):
        if is_flatpak_package(packages):
            cmd = ["flatpak", "update", "-y", "--noninteractive"] + packages.split()
            subprocess.call(cmd)
            return

        apt_options, valid_packages = parse_packages(packages)

        if not valid_packages:
            print("No valid package was found to upgrade.")
            return

        cmd = ["apt", "install", "--upgrade", "-yq", "-o", "APT::Status-Fd=2"] + apt_options + ["--"] + valid_packages
        subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def update():
        subprocess.call(["apt", "update", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def enable_i386_install(packages):
        print("parslinux-software-i386-start", file=sys.stderr)
        subprocess.call(["dpkg", "--add-architecture", "i386"])
        try:
            cache = apt.Cache()
            cache.update()
            cache.open()
        except Exception as e:
            print(str(e))
            print("{}".format(e), file=sys.stderr)
            update()
        install(packages)

    def kill(pid):
        print("kill function working for: {} pid".format(pid))

        if int(pid) < 100:
            print(f"kill func: cannot kill, pid: {pid}")
            return

        if not psutil:
            try:
                os.kill(int(pid), signal.SIGTERM)
                print(f"kill func: killed process {pid}")
            except Exception as e:
                print(f"kill func error: {e}")
            return

        parent = psutil.Process(int(pid))

        parent_cmdline = "".join(parent.cmdline())
        if "Actions.py" not in parent_cmdline:
            print("kill func: not software process")
            return

        install_phase = any("dpkg" in child.exe() for child in parent.children(recursive=True))
        print(f"Install phase: {install_phase}")

        if install_phase:
            print("You can't cancel the operation because download completed and install in progress.")
            return

        kill_dic = {}
        for child in parent.children(recursive=True):
            try:
                child_name = child.name()
                child_pid = child.pid
                child_exe = child.exe()
                child_uid = child.uids().real
                child_user = pwd.getpwuid(child_uid).pw_name
                child_cmdline = " ".join(child.cmdline())
                print(f"Checking child: {child_name} PID={child_pid} exe={child_exe} user={child_user} cmdline={child_cmdline}")

                if child_name in ("apt", "flatpak") and ("apt" in child_cmdline or "flatpak" in child_cmdline):
                    print(f"Adding child to kill list: {child_name} PID={child_pid}")
                    kill_dic[child_pid] = child_name

                elif child_user == "_apt" and \
                     (child_exe.startswith("/usr/lib/apt/methods")) and \
                     (child_cmdline.startswith("/usr/lib/apt/methods")):
                    print(f"Adding apt download child to kill list: {child_name} PID={child_pid}")
                    kill_dic[child_pid] = child_name

            except Exception as e:
                print(f"Error reading child PID={child.pid}: {e}")
                continue

        if kill_dic:
            print("Download operation is cancelling")
            for child_pid, child_name in kill_dic.items():
                print(f"child killing: name: {child_name} - pid: {child_pid}")
                psutil.Process(child_pid).kill()
            print(f"parent killing name: {parent.name()} - pid: {parent.pid}")
            parent.kill()
        else:
            print("No apt/flatpak download child found. Nothing to kill.")

    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "kill":
            kill(sys.argv[2])
            return

        packages_arg = sys.argv[2] if len(sys.argv) > 2 else ""

        # Flatpak packages do not need APT system lock
        if is_flatpak_package(packages_arg):
            if action == "install":
                install(packages_arg)
            elif action == "remove":
                remove(packages_arg)
            elif action == "upgrade":
                upgrade(packages_arg)
            return

        if control_lock():
            if action == "install":
                install(packages_arg)
            elif action == "remove":
                remove(packages_arg)
            elif action == "upgrade":
                upgrade(packages_arg)
            elif action == "update":
                update()
            elif action == "enablei386andinstall":
                enable_i386_install(packages_arg)
        else:
            print("lock error")
            sys.exit(1)
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
