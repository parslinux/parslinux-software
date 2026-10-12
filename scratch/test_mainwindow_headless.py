#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, "src")

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

print("Importing MainWindow...")
from MainWindow import MainWindow

print("Checking class inheritance...")
parents = [cls.__name__ for cls in MainWindow.__mro__]
print("MRO:", parents)

required_mixins = [
    "SliderMixin",
    "ImageGalleryMixin",
    "SearchMixin",
    "DetailMixin",
    "QueueMixin",
    "InstalledMixin"
]

for mixin in required_mixins:
    assert mixin in parents, f"{mixin} is not in MainWindow MRO!"
print("All mixins correctly present in MRO.")

# Verify key methods exist and are callable
key_methods = [
    # Slider
    "set_slider", "on_slider_app_activated", "on_ui_slider_right_button_clicked",
    # ImageGallery
    "add_to_image_popover", "round_corners", "app_image_from_server",
    # Search
    "set_categories", "on_ui_top_searchentry_search_changed", "_start_repo_search",
    # Detail
    "set_rating_stars", "set_app_details_page", "display_app_sandbox_permissions", "create_comment_widget",
    # Queue
    "action_package", "_action_flatpak_package", "create_queue_widget", "update_queue_progress",
    # Installed
    "set_myapps", "create_myapp_widget", "set_upgradables", "installedapps_filter_function",
    # Core
    "create_app_widget", "ui_right_stack_navigate_to"
]

for km in key_methods:
    assert hasattr(MainWindow, km), f"MainWindow is missing method {km}!"
    assert callable(getattr(MainWindow, km)), f"{km} is not callable!"

print(f"Verified {len(key_methods)} critical methods are present and callable.")
print("All tests passed successfully!")
