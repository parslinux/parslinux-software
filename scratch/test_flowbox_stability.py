import os
import sys
import unittest

# Headless GTK setup
os.environ["GSETTINGS_BACKEND"] = "memory"
os.environ["GDK_PIXBUF_MODULE_FILE"] = "/dev/null"
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("src/controllers"))

from MainWindow import MainWindow

class MockApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.parslinux.software.test")


class MockMainWindow(MainWindow):
    def worker(self):
        pass


class TestFlowBoxStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = MockApp()
        cls.win = MockMainWindow(cls.app)
        class MockServer:
            connection = True
            is_flathub = False
            cachedir = cls.win.UserSettings.cache_dir
        cls.win.Server = MockServer()

        # Populate sample apps in self.apps
        cls.win.apps = {
            "org.mozilla.firefox": {
                "name": "org.mozilla.firefox",
                "prettyname": {"tr": "Firefox Web Tarayıcısı", "en": "Firefox Web Browser"},
                "description": {"tr": "Hızlı ve güvenli web tarayıcısı", "en": "Fast and secure web browser"},
                "category": [{"tr": "İnternet", "en": "Network", "id": "network", "icon": "internet"}],
                "download": 1000,
                "rate_average": 4.8,
                "date": "2026-01-01 12:00"
            },
            "com.valvesoftware.Steam": {
                "name": "com.valvesoftware.Steam",
                "prettyname": {"tr": "Steam Oyun Platformu", "en": "Steam Gaming Platform"},
                "description": {"tr": "Oyun platformu", "en": "Gaming platform"},
                "category": [{"tr": "Oyunlar", "en": "Games", "id": "game", "icon": "games"}],
                "download": 2000,
                "rate_average": 4.9,
                "date": "2026-02-01 12:00"
            },
            "org.gimp.GIMP": {
                "name": "org.gimp.GIMP",
                "prettyname": {"tr": "GIMP Görsel Düzenleyici", "en": "GIMP Image Editor"},
                "description": {"tr": "Görsel işleme programı", "en": "Image editor"},
                "category": [{"tr": "Grafik", "en": "Graphics", "id": "graphics", "icon": "graphics"}],
                "download": 1500,
                "rate_average": 4.6,
                "date": "2026-03-01 12:00"
            }
        }
        cls.win.apps_full = cls.win.apps.copy()

    def _drain_glib_queue(self, max_iterations=50):
        ctx = GLib.main_context_default()
        for _ in range(max_iterations):
            if not ctx.iteration(False):
                break

    def setUp(self):
        if not hasattr(self.win, "Server") or self.win.Server is None:
            class MockServer:
                connection = True
                is_flathub = False
            self.win.Server = MockServer()
        else:
            self.win.Server.connection = True

    def test_01_initial_set_applications(self):
        """Initial set_applications creates widgets synchronously without empty listboxes"""
        self.win.set_applications(force=True)
        self._drain_glib_queue()

        children = self.win.ui_parslinuxapps_flowbox.get_children()
        self.assertEqual(len(children), 3)

        # Check that children have synchronous content and app_name
        for child in children:
            listbox = child.get_child()
            self.assertIsNotNone(listbox)
            self.assertTrue(hasattr(listbox, "app_name"))
            self.assertTrue(listbox.app_name in self.win.apps)
            # Ensure listbox has its row synchronously
            self.assertGreater(len(listbox.get_children()), 0)

    def test_02_category_filtering_without_clearing(self):
        """Switching categories filters existing children without clearing the flowbox"""
        initial_children_count = len(self.win.ui_parslinuxapps_flowbox.get_children())

        # Select "Oyunlar"
        self.win.current_category = "Oyunlar"
        self.win.ui_parslinuxapps_flowbox.invalidate_filter()
        self._drain_glib_queue()

        # Children in container should still be 3 (not cleared and rebuilt!)
        children = self.win.ui_parslinuxapps_flowbox.get_children()
        self.assertEqual(len(children), initial_children_count)

        # Only Steam should be child_is_visible (or filter func returns True for Steam)
        for child in children:
            lb = child.get_child()
            is_match = self.win.parslinuxapps_filter_function(child)
            if lb.app_name == "com.valvesoftware.Steam":
                self.assertTrue(is_match)
            else:
                self.assertFalse(is_match)

        # Now select "İnternet"
        self.win.current_category = "İnternet"
        self.win.ui_parslinuxapps_flowbox.invalidate_filter()
        self._drain_glib_queue()

        # Still 3 children!
        self.assertEqual(len(self.win.ui_parslinuxapps_flowbox.get_children()), initial_children_count)

        for child in self.win.ui_parslinuxapps_flowbox.get_children():
            lb = child.get_child()
            is_match = self.win.parslinuxapps_filter_function(child)
            if lb.app_name == "org.mozilla.firefox":
                self.assertTrue(is_match)
            else:
                self.assertFalse(is_match)

    def test_03_incremental_append(self):
        """New apps from flathub/search append without wiping existing cards"""
        initial_count = len(self.win.ui_parslinuxapps_flowbox.get_children())

        new_app = {
            "name": "org.videolan.VLC",
            "prettyname": {"tr": "VLC Medya Oynatıcı", "en": "VLC Media Player"},
            "description": {"tr": "Medya oynatıcı", "en": "Media player"},
            "category": [{"tr": "Ses ve Video", "en": "Audio & Video", "id": "audiovideo", "icon": "multimedia"}],
            "download": 3000,
            "rate_average": 4.9,
            "date": "2026-04-01 12:00"
        }
        self.win.apps[new_app["name"]] = new_app
        self.win.apps_full[new_app["name"]] = new_app

        self.win._append_apps_to_flowbox([new_app])
        self._drain_glib_queue()

        # Should now have 4 children
        self.assertEqual(len(self.win.ui_parslinuxapps_flowbox.get_children()), initial_count + 1)
        self.assertIn("org.videolan.VLC", self.win._flowbox_app_ids)

        # Calling _append_apps_to_flowbox with duplicate should NOT add again
        self.win._append_apps_to_flowbox([new_app])
        self._drain_glib_queue()
        self.assertEqual(len(self.win.ui_parslinuxapps_flowbox.get_children()), initial_count + 1)

    def test_04_sorting_without_destruction(self):
        """Combobox sorting sorts in place without removing cards"""
        count_before = len(self.win.ui_parslinuxapps_flowbox.get_children())

        mock_combobox = Gtk.ComboBoxText()
        mock_combobox.append_text("İsme Göre")
        mock_combobox.append_text("İndirmeye Göre")
        mock_combobox.append_text("Popülerliğe Göre")
        mock_combobox.append_text("Eklenme Tarihine Göre")

        # Sort by download (index 1)
        mock_combobox.set_active(1)
        self.win.on_ui_parslinuxapps_combobox_changed(mock_combobox)
        self._drain_glib_queue()

        # Count should remain identical
        self.assertEqual(len(self.win.ui_parslinuxapps_flowbox.get_children()), count_before)

        # Sort by name (index 0)
        mock_combobox.set_active(0)
        self.win.on_ui_parslinuxapps_combobox_changed(mock_combobox)
        self._drain_glib_queue()

        self.assertEqual(len(self.win.ui_parslinuxapps_flowbox.get_children()), count_before)

    def test_05_search_filtering(self):
        """Searching filters without error or destruction"""
        count_before = len(self.win.ui_parslinuxapps_flowbox.get_children())

        self.win.searching = True
        self.win.ui_top_searchentry.set_text("steam")
        self.win.ui_parslinuxapps_flowbox.invalidate_filter()
        self._drain_glib_queue()

        # Count in container remains identical
        self.assertEqual(len(self.win.ui_parslinuxapps_flowbox.get_children()), count_before)

        # Filter function matches Steam
        for child in self.win.ui_parslinuxapps_flowbox.get_children():
            lb = child.get_child()
            is_match = self.win.parslinuxapps_filter_function(child)
            if lb.app_name == "com.valvesoftware.Steam":
                self.assertTrue(is_match)
            else:
                self.assertFalse(is_match)

        self.win.searching = False
        self.win.ui_top_searchentry.set_text("")


if __name__ == "__main__":
    unittest.main()
