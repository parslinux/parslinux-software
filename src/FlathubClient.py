#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flathub API Client for Pars Linux Software Center
Interacts with Flathub v2 REST API (https://flathub.org/api/v2)
"""

import os
import json
import time
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from Logger import Logger

FLATHUB_API_BASE = "https://flathub.org/api/v2"
USER_AGENT = "ParsLinuxSoftwareCenter/1.0 (X11; Linux; +https://github.com/parslinux/parslinux-software)"

CATEGORY_METADATA = {
    "audiovideo": {"tr": "Ses ve Video", "en": "Audio & Video", "icon": "multimedia"},
    "development": {"tr": "Geliştirme", "en": "Development", "icon": "development"},
    "education": {"tr": "Eğitim", "en": "Education", "icon": "education"},
    "game": {"tr": "Oyunlar", "en": "Games", "icon": "games"},
    "graphics": {"tr": "Grafik", "en": "Graphics", "icon": "graphics"},
    "network": {"tr": "İnternet", "en": "Network", "icon": "internet"},
    "office": {"tr": "Ofis", "en": "Office", "icon": "office"},
    "science": {"tr": "Bilim", "en": "Science", "icon": "science"},
    "system": {"tr": "Sistem", "en": "System", "icon": "system"},
    "utility": {"tr": "Araçlar", "en": "Utilities", "icon": "utilities"},
    "healthfitness": {"tr": "Sağlık", "en": "Health & Fitness", "icon": "health"},
}


class FlathubClient:
    def __init__(self, cache_dir=None):
        self.Logger = Logger(__name__)
        self.base_url = FLATHUB_API_BASE
        if not cache_dir:
            from gi.repository import GLib
            cache_dir = os.path.join(GLib.get_user_cache_dir(), "parslinux-software")
        self.cache_dir = cache_dir
        self.icons_dir = os.path.join(self.cache_dir, "icons", "app-icons")
        self.api_cache_dir = os.path.join(self.cache_dir, "api_cache")
        Path(self.icons_dir).mkdir(parents=True, exist_ok=True)
        Path(self.api_cache_dir).mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=8)
        self._search_mem_cache = {}
        self._mem_lock = threading.Lock()

    def _get_cached_json(self, key, ttl_seconds):
        cache_file = os.path.join(self.api_cache_dir, f"{key}.json")
        if not os.path.exists(cache_file):
            return None, True
        try:
            mtime = os.path.getmtime(cache_file)
            age = time.time() - mtime
            is_stale = (age > ttl_seconds)
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data, is_stale
        except Exception as e:
            self.Logger.warning(f"Error reading cache {key}: {e}")
            return None, True

    def _set_cached_json(self, key, data):
        if not data:
            return
        cache_file = os.path.join(self.api_cache_dir, f"{key}.json")
        try:
            temp_file = f"{cache_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(temp_file, cache_file)
        except Exception as e:
            self.Logger.warning(f"Error saving cache {key}: {e}")

    def _request(self, endpoint, data=None, method="GET", timeout=10):
        url = f"{self.base_url}{endpoint}"
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        req_data = None
        if data is not None:
            req_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw)
        except urllib.error.HTTPError as e:
            self.Logger.warning(f"Flathub HTTP Error {e.code} for {url}: {e.reason}")
        except urllib.error.URLError as e:
            self.Logger.warning(f"Flathub URL Error for {url}: {e.reason}")
        except Exception as e:
            self.Logger.exception(f"Flathub Request Error for {url}: {e}")
        return None

    def check_connection(self):
        """Check if Flathub API is reachable"""
        res = self._request("/collection/popular", timeout=5)
        return res is not None and "hits" in res

    def get_popular(self, limit=50):
        """Fetch popular apps list with 4-hour disk TTL cache"""
        cache_key = f"popular_{limit}"
        cached_data, is_stale = self._get_cached_json(cache_key, ttl_seconds=14400)
        if cached_data and not is_stale:
            apps = [self.adapt_app_hit(h) for h in cached_data.get("hits", [])]
            self._prefetch_icons(apps)
            return apps

        res = self._request("/collection/popular")
        if res and "hits" in res:
            self._set_cached_json(cache_key, res)
            hits = res["hits"][:limit] if limit else res["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps

        # Offline fallback
        if cached_data and "hits" in cached_data:
            hits = cached_data["hits"][:limit] if limit else cached_data["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps
        return []

    def get_trending(self, limit=30):
        """Fetch trending apps list with 4-hour disk TTL cache"""
        cache_key = f"trending_{limit}"
        cached_data, is_stale = self._get_cached_json(cache_key, ttl_seconds=14400)
        if cached_data and not is_stale:
            apps = [self.adapt_app_hit(h) for h in cached_data.get("hits", [])]
            self._prefetch_icons(apps)
            return apps

        res = self._request("/collection/trending")
        if res and "hits" in res:
            self._set_cached_json(cache_key, res)
            hits = res["hits"][:limit] if limit else res["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps

        # Offline fallback
        if cached_data and "hits" in cached_data:
            hits = cached_data["hits"][:limit] if limit else cached_data["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps
        return []

    def get_recently_updated(self, limit=30):
        """Fetch recently updated apps list with 4-hour disk TTL cache"""
        cache_key = f"recent_{limit}"
        cached_data, is_stale = self._get_cached_json(cache_key, ttl_seconds=14400)
        if cached_data and not is_stale:
            apps = [self.adapt_app_hit(h) for h in cached_data.get("hits", [])]
            self._prefetch_icons(apps)
            return apps

        res = self._request("/collection/recently-updated")
        if res and "hits" in res:
            self._set_cached_json(cache_key, res)
            hits = res["hits"][:limit] if limit else res["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps

        # Offline fallback
        if cached_data and "hits" in cached_data:
            hits = cached_data["hits"][:limit] if limit else cached_data["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps
        return []

    def get_categories(self):
        """Return list of categories with localized names and icons"""
        cache_key = "categories_list"
        cached_data, is_stale = self._get_cached_json(cache_key, ttl_seconds=86400)
        if cached_data and not is_stale and isinstance(cached_data, list):
            cats = cached_data
        else:
            res = self._request("/collection/category")
            if res and isinstance(res, list):
                self._set_cached_json(cache_key, res)
                cats = res
            elif cached_data and isinstance(cached_data, list):
                cats = cached_data
            else:
                cats = list(CATEGORY_METADATA.keys())

        result = []
        for c in cats:
            c_low = c.lower()
            meta = CATEGORY_METADATA.get(c_low, {"tr": c.title(), "en": c.title(), "icon": "utilities"})
            result.append({
                "id": c_low,
                "en": meta["en"],
                "tr": meta["tr"],
                "icon": meta["icon"],
            })
        return result

    def get_category_apps(self, category, limit=60):
        """Fetch apps belonging to a category with 4-hour disk TTL cache"""
        cat_key = category.lower()
        if cat_key == "games":
            cat_key = "game"
        cache_key = f"cat_{cat_key}_{limit}"
        cached_data, is_stale = self._get_cached_json(cache_key, ttl_seconds=14400)
        if cached_data and not is_stale:
            apps = [self.adapt_app_hit(h) for h in cached_data.get("hits", [])]
            self._prefetch_icons(apps)
            return apps

        res = self._request(f"/collection/category/{cat_key}")
        if res and "hits" in res:
            self._set_cached_json(cache_key, res)
            hits = res["hits"][:limit] if limit else res["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps

        # Offline fallback
        if cached_data and "hits" in cached_data:
            hits = cached_data["hits"][:limit] if limit else cached_data["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            return apps
        return []

    def search(self, query, limit=40):
        """Search apps on Flathub with in-memory session cache"""
        if not query or not query.strip():
            return []
        q_norm = query.strip().lower()

        with self._mem_lock:
            if q_norm in self._search_mem_cache:
                return self._search_mem_cache[q_norm]

        res = self._request("/search", data={"query": q_norm}, method="POST")
        if res and "hits" in res:
            hits = res["hits"][:limit] if limit else res["hits"]
            apps = [self.adapt_app_hit(h) for h in hits]
            self._prefetch_icons(apps)
            with self._mem_lock:
                self._search_mem_cache[q_norm] = apps
            return apps
        return []

    def get_appstream(self, app_id):
        """Fetch detailed appstream metadata with 24-hour disk TTL cache"""
        cache_key = f"appstream_{app_id}"
        cached_data, is_stale = self._get_cached_json(cache_key, ttl_seconds=86400)
        if cached_data and not is_stale:
            return cached_data

        data = self._request(f"/appstream/{app_id}")
        if data:
            self._set_cached_json(cache_key, data)
            return data

        # Fallback to stale if network error
        return cached_data

    def adapt_app_hit(self, hit):
        """Convert Flathub API hit into normalized dictionary"""
        app_id = hit.get("app_id") or hit.get("id") or ""
        name = hit.get("name") or app_id
        summary = hit.get("summary") or ""
        description = hit.get("description") or summary
        icon_url = hit.get("icon") or ""
        main_cat = (hit.get("main_categories") or "utility").lower()
        meta = CATEGORY_METADATA.get(main_cat, {"tr": main_cat.title(), "en": main_cat.title(), "icon": "utilities"})

        local_icon = self.get_icon_local_path(app_id, icon_url)

        return {
            "name": app_id,
            "app_id": app_id,
            "display_name": name,
            "prettyname": {"tr": name, "en": name},
            "summary": {"tr": summary, "en": summary},
            "shortdesc": {"tr": summary, "en": summary},
            "description": {"tr": description, "en": description},
            "icon_url": icon_url,
            "icon": local_icon,
            "category": [{
                "en": main_cat,
                "tr": meta["tr"],
                "icon": meta["icon"],
                "external": False,
                "subcats": False,
            }],
            "license": hit.get("project_license") or "",
            "developer": hit.get("developer_name") or "",
            "installs": hit.get("installs_last_month") or 0,
            "verified": hit.get("verification_verified", False),
            "flatpak": True,
        }

    def get_icon_local_path(self, app_id, icon_url=""):
        ext = ".png" if ".png" in icon_url else ".svg" if ".svg" in icon_url else ".png"
        path = os.path.join(self.icons_dir, f"{app_id}{ext}")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        return path

    def _prefetch_icons(self, apps):
        """Asynchronously download icons in background threads"""
        def _download(app_id, icon_url):
            if not icon_url:
                return
            ext = ".png" if ".png" in icon_url else ".svg" if ".svg" in icon_url else ".png"
            dest = os.path.join(self.icons_dir, f"{app_id}{ext}")
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                return
            try:
                req = urllib.request.Request(icon_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        with open(dest, "wb") as f:
                            f.write(resp.read())
            except Exception:
                pass

        for app in apps:
            app_id = app.get("app_id")
            icon_url = app.get("icon_url")
            if app_id and icon_url:
                self.executor.submit(_download, app_id, icon_url)
