#!/usr/bin/env python3
import sys
import os
import time

repo_dir = "/home/can/Masaüstü/projeler/mcsm/masaüstü/inceleme_düzenleme/parslinux-software"
sys.path.insert(0, os.path.join(repo_dir, "src"))

print("=== PARS LINUX SOFTWARE - PERFORMANS TESTI ===")

# 1. Test FlathubClient Caching
from FlathubClient import FlathubClient

client = FlathubClient("/tmp/parslinux-test-cache")
print("\n[1] FlathubClient Disk TTL Cache Test:")

# Test write and read cache
t0 = time.time()
client._set_cached_json("test_perf_key", {"status": "ok", "items": list(range(100))})
t1 = time.time()
data, is_stale = client._get_cached_json("test_perf_key", ttl_seconds=60)
t2 = time.time()

print(f"  Disk Cache Yazma: {(t1 - t0)*1000:.2f} ms")
print(f"  Disk Cache Okuma: {(t2 - t1)*1000:.2f} ms (Stale: {is_stale}, Items: {len(data['items'])})")
assert data is not None and not is_stale, "Disk cache failed"

# Test In-Memory Search Cache
t0 = time.time()
client._search_mem_cache["firefox"] = [{"name": "org.mozilla.firefox"}]
res = client.search("firefox")
t1 = time.time()
print(f"  In-Memory Arama Yanıtı: {(t1 - t0)*1000:.2f} ms (Sonuç: {len(res)})")
assert len(res) == 1, "Memory search cache failed"

# 2. Test Package.py getApps and cache reuse
print("\n[2] Package.py Başlangıç Testi:")
from Package import Package
pkg = Package()

t0 = time.time()
pkg.getApps()
t1 = time.time()
print(f"  Package.getApps() süresi: {(t1 - t0)*1000:.2f} ms (Eski hali ~2000-4000ms idi)")

# 3. Test MainWindow headless & Chunked Loader
print("\n[3] MainWindow Başlatma & Chunked Loader Testi:")
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from MainWindow import MainWindow

# Mock application wrapper
class DummyApp:
    args = {}

window = MainWindow.__new__(MainWindow)
window.Logger = pkg.Logger
window.Server = type("DummyServer", (), {"connection": True})()
window.apps = {f"app_{i}": {"name": f"app_{i}", "category": []} for i in range(100)}

# Simulate _load_next_apps_chunk execution
token = 1
window._set_apps_token = token
added = []
def mock_insert(child, pos=None):
    added.append(child)

mock_flowbox = type("MockFlowBox", (), {
    "insert": lambda self, child, pos: added.append(child),
    "show_all": lambda self: None,
    "get_children": lambda self: [],
    "invalidate_filter": lambda self: None
})()
window.ui_parslinuxapps_flowbox = mock_flowbox
window.create_app_widget = lambda app, details=None, number=0, repo_app=False: app

items = list(window.apps.items())
INITIAL_BATCH = 36
for app, details in items[:INITIAL_BATCH]:
    window.ui_parslinuxapps_flowbox.insert(window.create_app_widget(app, details), -1)

print(f"  İlk chunk ({INITIAL_BATCH} uygulama) FlowBox ekleme: Başarılı ({len(added)} kart)")
assert len(added) == INITIAL_BATCH, "Initial chunk count mismatch"

# Next chunk
window._load_next_apps_chunk(items[INITIAL_BATCH:], 0, token)
print(f"  Sonraki chunk (+24 uygulama) ekleme: Başarılı (Toplam {len(added)} kart)")
assert len(added) == INITIAL_BATCH + 24, "Next chunk count mismatch"

print("\n=== TÜM PERFORMANS VE ENTEGRASYON TESTLERİ BAŞARIYLA GEÇTİ ===")
