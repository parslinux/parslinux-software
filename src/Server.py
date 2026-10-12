#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server and backend synchronization manager for Pars Linux Software Center
Supports Flathub v2 REST API backend as primary source
"""

import json
import os.path
import tarfile
import threading
from hashlib import md5
from pathlib import Path
from shutil import rmtree

try:
    from tarfile import OutsideDestinationError
except ImportError:
    OutsideDestinationError = None

import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib, Gio
from Logger import Logger
from FlathubClient import FlathubClient


class Server(object):
    def __init__(self):
        self.Logger = Logger(__name__)
        self.serverurl = "https://flathub.org/api/v2"
        self.serverhash = "/api/v3/hash"
        self.serverapps = "/api/v3/apps/"
        self.serverhomepage = "/api/v3/homepage"
        self.serverdetails = "/api/v3/details"
        self.servercomments = "/api/v3/comments"
        self.serversendrate = "/api/v3/rate"
        self.serversenddownload = "/api/v3/download"
        self.serversendsuggest = "/api/v3/suggest"
        self.serverfiles = "/files/"
        self.server_apps_archive = "apps.tar.gz"
        self.server_icons_archive = "icons.tar.gz"
        self.server_images_archive = "images.tar.gz"
        self.server_cats_archive = "cats.tar.gz"
        self.server_home_archive = "home.tar.gz"

        self.cachedir = "{}/parslinux/parslinux-software/".format(GLib.get_user_cache_dir())
        self.configdir = "{}/parslinux/parslinux-software/".format(GLib.get_user_config_dir())

        self.icons_dir = self.cachedir + "icons/"
        self.app_icons_dir = self.icons_dir + "app-icons"
        self.cat_icons_dir = self.icons_dir + "cat-icons"

        self.error_message = ""
        self.connection = False
        self.editor_app_list = []
        self.slider_app_list = []
        self.most_down_app_list = []
        self.trend_app_list = []
        self.recent_app_list = []
        self.appversion_parslinux = ""
        self.blocked_gnome_reviews = []
        self.apt_uptime = 86400

        self.gnomeratingserver = "https://odrs.gnome.org/1.0/reviews/api/ratings"
        self.gnomecommentserver = "https://odrs.gnome.org/1.0/reviews/api/fetch"

        self.flathub = FlathubClient(self.cachedir)
        self.is_flathub = True
        self._cached_startup_apps = None

    def get_hashes(self, url):
        """Asynchronously check Flathub connection and trigger ServerHashesCB"""
        if self.is_flathub or "flathub.org" in self.serverurl:
            def _flathub_hashes():
                ok = self.flathub.check_connection()
                self.connection = ok
                if ok:
                    dummy_md5 = {
                        "md5": {
                            "apps": "flathub_apps",
                            "cats": "flathub_cats",
                            "icons": "flathub_icons",
                            "images": "flathub_images",
                            "home": "flathub_home",
                        }
                    }
                    GLib.idle_add(self.ServerHashesCB, True, dummy_md5)
                else:
                    self.error_message = "Flathub sunucusuna ulaşılamadı."
                    GLib.idle_add(self.ServerHashesCB, False)

            threading.Thread(target=_flathub_hashes, daemon=True).start()
            return

        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_hashes_stream)

    def _open_hashes_stream(self, file, result):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.error_message = error
            self.Logger.warning("_open_hashes_stream Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerHashesCB(False)
            return False

        if success:
            self.ServerHashesCB(True, json.loads(data))
        else:
            self.Logger.warning("_open_hashes_stream is not success")
            self.ServerHashesCB(False)

    def get_file(self, url, download_location, server_md5="", type="", save_file=True):
        if self.is_flathub or "flathub.org" in self.serverurl:
            def _flathub_get_file():
                try:
                    if type == "apps":
                        if self._cached_startup_apps is None:
                            self._cached_startup_apps = self.flathub.get_popular(limit=100)
                        apps = self._cached_startup_apps
                        apps_dict = {a["name"]: a for a in apps}
                        GLib.idle_add(self.ServerFilesCB, True, "apps", apps_dict)
                    elif type == "cats":
                        cats = self.flathub.get_categories()
                        Path(os.path.dirname(download_location)).mkdir(parents=True, exist_ok=True)
                        cats_json_path = os.path.join(os.path.dirname(download_location), "cats.json")
                        with open(cats_json_path, "w", encoding="utf-8") as f:
                            json.dump({"categories": cats}, f, ensure_ascii=False)
                        with open(download_location, "w", encoding="utf-8") as f:
                            json.dump({"categories": cats}, f, ensure_ascii=False)
                        GLib.idle_add(self.ServerFilesCB, True, "cats")
                    elif type in ("icons", "images"):
                        GLib.idle_add(self.ServerFilesCB, True, type)
                    elif type == "home":
                        if self._cached_startup_apps is None:
                            self._cached_startup_apps = self.flathub.get_popular(limit=100)
                        pops = self._cached_startup_apps[:25]
                        trends = self.flathub.get_trending(limit=20)

                        slider_apps = []
                        for a in pops[:5]:
                            slider_apps.append({
                                "name": a["name"],
                                "prettyname": a["prettyname"],
                                "slogan": a["shortdesc"],
                                "category": a["category"][0] if a["category"] else {},
                            })

                        editor_apps = pops[5:15]
                        most_down_apps = pops[:10]
                        trend_apps = trends[:10]
                        recent_apps = pops[15:25]

                        home_data = {
                            "editor_apps": editor_apps,
                            "slider_apps": slider_apps,
                            "most_down_apps": most_down_apps,
                            "trend_apps": trend_apps,
                            "recent_apps": recent_apps,
                            "version_parslinux": None,
                            "apt_uptime": 86400,
                        }
                        GLib.idle_add(self.ServerFilesCB, True, "home", home_data)
                    else:
                        GLib.idle_add(self.ServerFilesCB, True, type)
                except Exception as e:
                    self.Logger.exception(f"Flathub get_file error for {type}: {e}")
                    GLib.idle_add(self.ServerFilesCB, False, type)

            threading.Thread(target=_flathub_get_file, daemon=True).start()
            return

        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_file_stream, download_location, server_md5, type, save_file)

    def _open_file_stream(self, file, result, download_location, server_md5, type, save_file=True):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.error_message = "{} : {}".format(error, type)
            self.Logger.warning("{} _open_file_stream Error: {}, {}".format(type, error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerFilesCB(False)
            return False

        if save_file:
            try:
                Path(os.path.dirname(download_location)).mkdir(parents=True, exist_ok=True)
                with open(download_location, "wb") as f:
                    f.write(data)
            except Exception as e:
                self.error_message = "{}".format(e)
                self.Logger.warning("_open_file_stream Error: {}".format(e))
                self.Logger.exception("{}".format(e))
                self.ServerFilesCB(False)
                return False

            if md5(open(download_location, "rb").read()).hexdigest() == server_md5:
                if self.extract_archive(download_location):
                    self.ServerFilesCB(True, type=type)
                else:
                    self.error_message = "{} extract error".format(type)
                    self.Logger.warning("{} extract error".format(type))
                    self.ServerFilesCB(False)
            else:
                self.error_message = "{} file downloaded but md5 is different!".format(download_location)
                self.Logger.warning("{} file downloaded but md5 is different!".format(download_location))
                self.ServerFilesCB(False)
        else:
            self.ServerFilesCB(True, type=type, response=json.loads(data))

    def extract_archive(self, archive):
        dest_path = os.path.dirname(archive)

        def remove_subdirectories_and_files(directory, excepted_file):
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path != excepted_file:
                        os.remove(file_path)
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    rmtree(dir_path, ignore_errors=True)

        def is_within_directory(directory, target):
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
            return os.path.commonpath([abs_directory, abs_target]) == abs_directory

        try:
            remove_subdirectories_and_files(dest_path, excepted_file=archive)
            with tarfile.open(archive) as tar:
                allowed_extensions = (".svg", ".png", ".json")
                extractables = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(allowed_extensions)]
                try:
                    tar.extractall(members=extractables, path=dest_path, filter="data")
                except TypeError:
                    self.Logger.info("filter='data' not supported, using secure fallback method")
                    safe_extractables = []
                    for member in extractables:
                        target_path = os.path.abspath(os.path.join(dest_path, member.name))
                        if is_within_directory(dest_path, target_path):
                            safe_extractables.append(member)
                        else:
                            self.Logger.warning(f"Skipped unsafe path: {member.name}")
                    if safe_extractables:
                        tar.extractall(members=safe_extractables, path=dest_path)
                    else:
                        return False
        except Exception as e:
            if OutsideDestinationError and isinstance(e, OutsideDestinationError):
                self.Logger.exception(f"Extraction blocked: attempted path traversal detected: {e}")
                return False
            self.Logger.exception(f"Unexpected error while processing tar archive: {e}")
            return False
        return True

    def delete_cache(self):
        try:
            rmtree(self.cachedir)
            Path(self.cachedir).mkdir(parents=True, exist_ok=True)
            self.Logger.info("{} removed".format(self.cachedir))
            return True, ""
        except Exception as e:
            self.Logger.exception("{}".format(e))
            return False, str(e)
