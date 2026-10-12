#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import subprocess

from setuptools import setup, find_packages


def create_mo_files():
    podir = "po"
    mo = []
    if os.path.exists(podir):
        for po in os.listdir(podir):
            if po.endswith(".po"):
                lang = po[:-3]
                local_dir = os.path.join(podir, lang, "LC_MESSAGES")
                os.makedirs(local_dir, exist_ok=True)
                mo_file = os.path.join(local_dir, "parslinux-software.mo")
                subprocess.call(["msgfmt", os.path.join(podir, po), "-o", mo_file])
                mo.append((f"/usr/share/locale/{lang}/LC_MESSAGES", [mo_file]))
    return mo


changelog = "debian/changelog"
version = "2.0.0"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except Exception:
        print("debian/changelog format is wrong for get version")

os.makedirs("src", exist_ok=True)
with open("src/__version__", "w") as f:
    f.write(version)


def pythonic_version(version):
    return (
        version.replace("~alpha", "a")
        .replace("~beta", "b")
        .replace("~rc", "rc")
        .replace("~dev", ".dev")
    )


data_files = [
    ("/usr/bin", ["parslinux-software"]),
    (
        "/usr/share/applications",
        [
            "org.parslinux.software.desktop",
            "org.parslinux.software-open.desktop",
        ],
    ),
    (
        "/usr/share/polkit-1/actions",
        ["org.parslinux.pkexec.parslinux-software.policy"],
    ),
    (
        "/usr/share/parslinux/parslinux-software/css",
        ["css/adwaita.css", "css/base.css"],
    ),
    (
        "/usr/share/parslinux/parslinux-software/ui",
        ["ui/MainWindow.glade"],
    ),
    (
        "/usr/share/parslinux/parslinux-software/src",
        [
            "src/Actions.py",
            "src/AppDetail.py",
            "src/AppImage.py",
            "src/AppRequest.py",
            "src/AutoAptUpdate.py",
            "src/FlathubClient.py",
            "src/FlatpakManager.py",
            "src/GnomeComment.py",
            "src/GnomeRatingServer.py",
            "src/Group.py",
            "src/Logger.py",
            "src/Main.py",
            "src/MainWindow.py",
            "src/Package.py",
            "src/Server.py",
            "src/SysActions.py",
            "src/UserSettings.py",
            "src/Utils.py",
            "src/__version__",
        ],
    ),
    (
        "/usr/share/parslinux/parslinux-software/src/controllers",
        [
            "src/controllers/__init__.py",
            "src/controllers/SliderMixin.py",
            "src/controllers/ImageGalleryMixin.py",
            "src/controllers/SearchMixin.py",
            "src/controllers/DetailMixin.py",
            "src/controllers/QueueMixin.py",
            "src/controllers/InstalledMixin.py",
        ],
    ),
    (
        "/usr/share/icons/hicolor/scalable/apps",
        ["images/parslinux-software.svg"],
    ),
    (
        "/usr/share/icons/hicolor/scalable/categories",
        sorted(glob.glob("icons/*.svg")),
    ),
    (
        "/usr/share/parslinux/parslinux-software/icons",
        sorted(glob.glob("icons/*.svg")),
    ),
    (
        "/usr/share/parslinux/parslinux-software/icons/hicolor",
        ["icons/hicolor/index.theme"],
    ),
    (
        "/usr/share/parslinux/parslinux-software/icons/hicolor/scalable/apps",
        ["icons/hicolor/scalable/apps/parslinux-software.svg"],
    ),
    (
        "/usr/share/parslinux/parslinux-software/icons/hicolor/scalable/categories",
        sorted(glob.glob("icons/hicolor/scalable/categories/*.svg")),
    ),
    ("/usr/share/mime/packages/", ["parslinux-software.xml"]),
    (
        "/usr/share/polkit-1/rules.d/",
        ["parslinux-software-group.rules"],
    ),
    ("/etc/parslinux/", ["parslinux-software.conf"]),
] + create_mo_files()

setup(
    name="Pars Linux Software",
    version=pythonic_version(version),
    packages=find_packages(),
    scripts=["parslinux-software"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Pars Linux Developers",
    author_email="dev@parslinux.org",
    description="Pars Linux Software Center",
    license="GPLv3",
    keywords="software center",
    url="https://parslinux.org",
)
