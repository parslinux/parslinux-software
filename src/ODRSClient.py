#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ODRS Client for Pars Linux Software Center
Fetches ratings and user reviews from the Open Desktop Rating Service (odrs.gnome.org).
Used by GNOME Software, KDE Discover, and Pars Linux Software Center.
"""

import os
import time
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import hashlib
import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib

from Logger import Logger

ODRS_BASE_URL = "https://odrs.gnome.org/1.0/reviews/api"
USER_AGENT = "ParsLinuxSoftware/2.0 (Linux; x86_64) ODRSClient/1.0"


class ODRSClient:
    def __init__(self, cache_dir=None):
        self.Logger = Logger(__name__)
        if not cache_dir:
            cache_dir = os.path.expanduser("~/.cache/parslinux/parslinux-software/odrs_cache")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="odrs_worker")

    def _get_cached_json(self, key, ttl_seconds=3600):
        path = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(path):
            return None, True
        try:
            mtime = os.path.getmtime(path)
            is_stale = (time.time() - mtime) > ttl_seconds
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data, is_stale
        except Exception as e:
            self.Logger.warning(f"Error reading ODRS cache {key}: {e}")
            return None, True

    def _set_cached_json(self, key, data):
        path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            self.Logger.warning(f"Error saving ODRS cache {key}: {e}")

    def _fetch_url(self, url, timeout=6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw = resp.read().decode("utf-8", errors="replace")
                    return json.loads(raw)
        except Exception as e:
            self.Logger.warning(f"ODRS fetch failed for {url}: {e}")
        return None

    def get_ratings(self, app_id):
        """
        Fetches rating distribution for app_id.
        Returns dict with:
          'status': bool
          'average': float (1.0 to 5.0)
          'count': int
          'star1': int, 'star2': int, 'star3': int, 'star4': int, 'star5': int
        """
        if not app_id:
            return {"status": False, "average": 0.0, "count": 0}

        cache_key = f"ratings_{app_id.lower()}"
        cached, is_stale = self._get_cached_json(cache_key, ttl_seconds=7200)
        if cached is not None and not is_stale:
            return cached

        url = f"{ODRS_BASE_URL}/ratings/{app_id}"
        data = self._fetch_url(url)

        res = {
            "status": False,
            "average": 0.0,
            "count": 0,
            "star1": 0,
            "star2": 0,
            "star3": 0,
            "star4": 0,
            "star5": 0,
        }

        if data and isinstance(data, dict):
            s1 = data.get("star1", 0)
            s2 = data.get("star2", 0)
            s3 = data.get("star3", 0)
            s4 = data.get("star4", 0)
            s5 = data.get("star5", 0)
            total = data.get("total", (s1 + s2 + s3 + s4 + s5))

            if total > 0:
                weighted = (1 * s1) + (2 * s2) + (3 * s3) + (4 * s4) + (5 * s5)
                avg = round(weighted / total, 1)
                res = {
                    "status": True,
                    "average": avg,
                    "count": total,
                    "star1": s1,
                    "star2": s2,
                    "star3": s3,
                    "star4": s4,
                    "star5": s5,
                }
                self._set_cached_json(cache_key, res)
                return res

        if cached is not None:
            return cached
        return res

    def get_reviews(self, app_id, user_locale="tr"):
        """
        Fetches user reviews for app_id.
        Returns list of review dicts:
          'user': str
          'rating': int (1 to 5)
          'summary': str
          'description': str
          'date': str
          'distro': str
          'locale': str
        """
        if not app_id:
            return []

        cache_key = f"reviews_{app_id.lower()}"
        cached, is_stale = self._get_cached_json(cache_key, ttl_seconds=3600)
        if cached is not None and not is_stale:
            return cached

        url = f"{ODRS_BASE_URL}/app/{app_id}"
        data = self._fetch_url(url)

        parsed_reviews = []
        if data and isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                score = item.get("rating", 0)
                stars = max(1, min(5, round(score / 20.0))) if score > 0 else 3

                date_ts = item.get("date_created", 0)
                date_str = ""
                if date_ts:
                    try:
                        date_str = datetime.fromtimestamp(date_ts).strftime("%d.%m.%Y")
                    except Exception:
                        date_str = ""

                parsed_reviews.append({
                    "user": item.get("user_display") or "Anonim",
                    "rating": stars,
                    "summary": item.get("summary") or "",
                    "description": item.get("description") or "",
                    "date": date_str,
                    "distro": item.get("distro") or "",
                    "locale": item.get("locale") or "",
                    "version": item.get("version") or "",
                })

            def _sort_key(r):
                loc = r.get("locale", "").lower()
                is_user_loc = 2 if loc.startswith(user_locale.lower()) else (1 if loc.startswith("en") else 0)
                return is_user_loc

            parsed_reviews.sort(key=_sort_key, reverse=True)
            self._set_cached_json(cache_key, parsed_reviews)
            return parsed_reviews

        if cached is not None:
            return cached
        return []

    def _get_user_hash(self):
        """Generate anonymous machine/user SHA1 hash for ODRS vote deduplication"""
        seed = ""
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        seed = f.read().strip()
                        if seed:
                            break
                except Exception:
                    pass
        if not seed:
            seed = os.environ.get("USER", "parslinux-user")
        return hashlib.sha1(f"parslinux_{seed}".encode("utf-8")).hexdigest()

    def submit_review(self, app_id, rating_stars, summary, description, user_display=None):
        """
        Submit a new review to ODRS.
        rating_stars: int 1-5
        Returns (success: bool, message: str)
        """
        if not app_id:
            return False, "Uygulama kimliği eksik."

        score = max(1, min(5, int(rating_stars))) * 20
        user_hash = self._get_user_hash()
        display_name = (user_display or "").strip() or "Pars Linux Kullanıcısı"

        payload = {
            "user_hash": user_hash,
            "user_display": display_name,
            "summary": (summary or "").strip(),
            "description": (description or "").strip(),
            "rating": score,
            "version": "1.0",
            "distro": "Pars Linux",
        }

        url = f"{ODRS_BASE_URL}/app/{app_id}"
        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    # Invalidate local review cache for app_id
                    cache_key = f"reviews_{app_id.lower()}"
                    path = os.path.join(self.cache_dir, f"{cache_key}.json")
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception:
                            pass
                    self.Logger.info(f"ODRS review submitted successfully for {app_id}")
                    return True, "Yorumunuz başarıyla gönderildi."
                else:
                    return False, f"Sunucu yanıtı: {resp.status}"
        except urllib.error.HTTPError as e:
            msg = f"HTTP {e.code}: {e.reason}"
            self.Logger.warning(f"ODRS submit failed: {msg}")
            return False, msg
        except Exception as e:
            self.Logger.exception(f"ODRS submit exception: {e}")
            return False, str(e)

    def submit_review_async(self, app_id, rating_stars, summary, description, user_display=None, callback=None):
        """
        Asynchronously submits review to ODRS and calls callback(success: bool, message: str) on GLib main thread.
        """
        def _worker():
            success, msg = self.submit_review(app_id, rating_stars, summary, description, user_display)
            if callback:
                GLib.idle_add(callback, success, msg)

        self.executor.submit(_worker)
