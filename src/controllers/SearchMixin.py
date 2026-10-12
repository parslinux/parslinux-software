import gettext
import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango

_ = gettext.gettext


class SearchMixin:
    """Kategori listeleme, üst arama çubuğu ve depo araması kontrolcü mixin'i."""

    def set_categories(self):
        GLib.idle_add(lambda: (self.ui_leftcats_listbox and self.ui_leftcats_listbox.foreach(
            lambda child: self.ui_leftcats_listbox.remove(child)), False))

        GLib.idle_add(lambda: (self.ui_leftinstalled_listbox and self.ui_leftinstalled_listbox.foreach(
            lambda child: self.ui_leftinstalled_listbox.remove(child)), False))

        if getattr(self, "Server", None) and getattr(self.Server, "connection", False):
            self.categories = []
            for cat in self.cats:
                self.categories.append({
                    "id": cat.get("id") or cat.get("en", "").lower(),
                    "name": cat[self.user_locale],
                    "icon": cat.get("icon") or cat["en"],
                    "number": cat.get("number")
                })

            self.categories = sorted(
                self.categories,
                key=lambda x: (
                    0 if x.get("number") is not None else 1,
                    x.get("number", float('inf')),
                    x["name"].lower()
                )
            )

            if self.server_cat_all:
                name_from_server = self.server_cat_all.get(self.user_locale)
                self.cat_all["name"] = name_from_server if name_from_server else self.cat_all["name"]

            self.categories.insert(0, self.cat_all)

            # discover
            icon = Gtk.Image.new_from_icon_name("ps-cat-discover-symbolic", Gtk.IconSize.BUTTON)
            label = Gtk.Label.new()
            label.set_markup("<b>{}</b>".format(_("Discover")))
            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box.pack_start(icon, False, True, 0)
            box.pack_start(label, False, True, 0)
            box.set_margin_start(8)
            box.set_margin_end(30)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            row = Gtk.ListBoxRow()
            row.add(box)
            row.name = "discover"
            GLib.idle_add(self.ui_leftcats_listbox.add, row)

            # categories
            for cat in self.categories:
                cat_icon = Gtk.Image.new_from_icon_name("ps-cat-{}-symbolic".format(cat["icon"]), Gtk.IconSize.BUTTON)

                label = Gtk.Label.new()
                label.set_markup("<b>{}</b>".format(cat["name"].title()))
                label.set_ellipsize(Pango.EllipsizeMode.END)

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
                box.pack_start(cat_icon, False, True, 0)
                box.pack_start(label, False, True, 0)
                box.set_margin_start(8)
                box.set_margin_end(8)
                box.set_margin_top(8)
                box.set_margin_bottom(8)

                row = Gtk.ListBoxRow()
                row.add(box)
                row.name = cat["name"]

                GLib.idle_add(self.ui_leftcats_listbox.add, row)

            # installed
            installed_icon = Gtk.Image.new_from_icon_name("ps-cat-installed-symbolic", Gtk.IconSize.BUTTON)

            label = Gtk.Label.new()
            label.set_markup("<b>{}</b>".format(_("Installed Apps")))
            label.set_ellipsize(Pango.EllipsizeMode.END)

            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box.pack_start(installed_icon, False, True, 0)
            box.pack_start(label, False, True, 0)
            box.set_margin_start(8)
            box.set_margin_end(8)
            box.set_margin_top(8)
            box.set_margin_bottom(8)

            row = Gtk.ListBoxRow()
            row.add(box)
            row.name = "installed"
            GLib.idle_add(self.ui_leftinstalled_listbox.add, row)

            # settings
            settings_icon = Gtk.Image.new_from_icon_name("preferences-other-symbolic", Gtk.IconSize.BUTTON)

            settings_label = Gtk.Label.new()
            settings_label.set_markup("<b>{}</b>".format(_("Settings")))
            settings_label.set_ellipsize(Pango.EllipsizeMode.END)

            settings_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            settings_box.pack_start(settings_icon, False, True, 0)
            settings_box.pack_start(settings_label, False, True, 0)
            settings_box.set_margin_start(8)
            settings_box.set_margin_end(8)
            settings_box.set_margin_top(8)
            settings_box.set_margin_bottom(8)

            settings_row = Gtk.ListBoxRow()
            settings_row.add(settings_box)
            settings_row.name = "settings"
            GLib.idle_add(self.ui_leftinstalled_listbox.add, settings_row)

            # show widgets
            GLib.idle_add(self.ui_leftcats_listbox.show_all)
            GLib.idle_add(self.ui_leftinstalled_listbox.show_all)

            # default select discover
            GLib.idle_add(lambda: self.ui_leftcats_listbox.select_row(self.ui_leftcats_listbox.get_row_at_index(0)))

    def _load_flathub_category(self, cat_name):
        cat_id = None
        for cat in self.categories:
            if cat.get("name") == cat_name:
                cat_id = cat.get("id") or cat.get("icon") or cat.get("en", "").lower()
                break
        if not cat_id:
            cat_id = cat_name.lower()
        if cat_id in ("all", "tümü", "discover"):
            return

        def _fetch():
            apps = self.Server.flathub.get_category_apps(cat_id, limit=60)
            if apps:
                new_apps = []
                for a in apps:
                    self.apps[a["name"]] = a
                    self.apps_full[a["name"]] = a
                    if not hasattr(self, "_flowbox_app_ids") or a["name"] not in self._flowbox_app_ids:
                        new_apps.append(a)
                if new_apps:
                    GLib.idle_add(self._append_apps_to_flowbox, new_apps)
                else:
                    GLib.idle_add(self.ui_parslinuxapps_flowbox.invalidate_filter)

        threading.Thread(target=_fetch, daemon=True).start()

    def on_ui_leftcats_listbox_row_activated(self, listbox, row):
        self.searching = False
        self.ui_leftupdates_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        self.current_category = row.name
        if self.current_category == "discover":
            self.ui_right_stack_navigate_to("discover")
            self.ui_discover_scrolledwindow.set_vadjustment(Gtk.Adjustment())
        else:
            if getattr(self.Server, "is_flathub", False):
                self._load_flathub_category(self.current_category)
            self.ui_parslinuxapps_flowbox.invalidate_filter()
            self.ui_right_stack_navigate_to("apps")
            self.ui_parslinuxapps_title_stack.set_visible_child_name("apps")
            self.ui_repotitle_box.set_visible(False)
            self.ui_repoapps_flowbox.set_visible(False)

            self.ui_parslinuxapps_scrolledwindow.set_vadjustment(Gtk.Adjustment())

            self.ui_currentcat_label.set_markup("<span size='x-large'><b>{}</b></span>".format(self.current_category.title()))
            self.ui_currentcat_image.set_from_icon_name(
                next(("ps-cat-{}-symbolic".format(cat["icon"]) for cat in self.categories if cat["name"] == self.current_category),
                     "image-missing-symbolic"), Gtk.IconSize.DIALOG)
            self.ui_currentcat_image.set_pixel_size(55)

    def on_ui_leftupdates_listbox_row_activated(self, listbox, row):
        self.searching = False
        self.ui_leftcats_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        self.ui_right_stack_navigate_to("installed")
        self.ui_installedapps_scrolledwindow.set_vadjustment(Gtk.Adjustment())
        self.ui_installedapps_flowbox.invalidate_filter()

    def on_ui_leftinstalled_listbox_row_activated(self, listbox, row):
        if getattr(row, "name", None) == "settings":
            self.on_menu_settings_clicked(None)
            return
        self.searching = False
        self.ui_leftcats_listbox.unselect_all()
        self.ui_leftupdates_listbox.unselect_all()
        self.ui_right_stack_navigate_to("installed")
        self.ui_installedapps_scrolledwindow.set_vadjustment(Gtk.Adjustment())
        self.ui_installedapps_flowbox.invalidate_filter()

    def on_ui_top_searchentry_focus_in_event(self, widget, event):
        self.searching = True

        if self.ui_right_stack.get_visible_child_name() == "installed":
            self.ui_installedapps_flowbox.invalidate_filter()
        else:
            self.ui_right_stack_navigate_to("apps")
            self.ui_parslinuxapps_title_stack.set_visible_child_name("search")
            self.ui_repotitle_box.set_visible(self.repo_final_list)
            self.ui_repoapps_flowbox.set_visible(True)

            self.ui_leftcats_listbox.unselect_all()
            self.ui_leftinstalled_listbox.unselect_all()
            self.ui_leftupdates_listbox.unselect_all()

            self.ui_parslinuxapps_flowbox.invalidate_filter()

    def on_ui_top_searchentry_search_changed(self, entry_search):
        self.searching = True

        if getattr(self, "_search_debounce_id", None):
            GLib.source_remove(self._search_debounce_id)
            self._search_debounce_id = None

        text = entry_search.get_text().strip().lower()

        if self.ui_right_stack.get_visible_child_name() == "installed":
            self.Logger.info(f"installed_apps searching for: {text}")
            self.ui_installedapps_flowbox.invalidate_filter()
            return

        self.ui_right_stack_navigate_to("apps")
        self.ui_parslinuxapps_title_stack.set_visible_child_name("search")
        self.ui_searchterm_label.set_text(_("Results for {}").format(text) if text else _("Results"))

        # Debounce the heavy network search and repo scanning by 250ms
        self._search_debounce_id = GLib.timeout_add(250, self._perform_debounced_search, text)

    def _perform_debounced_search(self, text):
        self._search_debounce_id = None
        self.ui_parslinuxapps_flowbox.invalidate_filter()

        self._current_search_token = getattr(self, "_current_search_token", 0) + 1
        current_token = self._current_search_token

        self.Logger.info(f"store_apps debounced searching for: {text} (token: {current_token})")

        if getattr(self.Server, "is_flathub", False) and len(text) >= 2:
            def _flathub_search_worker(query, token):
                results = self.Server.flathub.search(query, limit=40)
                if token != getattr(self, "_current_search_token", None):
                    return
                if results:
                    new_apps = []
                    for a in results:
                        self.apps[a["name"]] = a
                        self.apps_full[a["name"]] = a
                        if not hasattr(self, "_flowbox_app_ids") or a["name"] not in self._flowbox_app_ids:
                            new_apps.append(a)
                    GLib.idle_add(self._apply_search_results, token, new_apps)

            threading.Thread(target=_flathub_search_worker, args=(text, current_token), daemon=True).start()

        self._repo_search_cancel_flag = True

        if getattr(self, "_search_start_id", None):
            GLib.source_remove(self._search_start_id)
            self._search_start_id = None

        if getattr(self, "_search_step_id", None):
            GLib.source_remove(self._search_step_id)
            self._search_step_id = None

        GLib.idle_add(self._clear_repo_results)

        if len(text) < 3:
            return False

        self._repo_search_cancel_flag = False
        self._search_start_id = GLib.idle_add(self._start_repo_search, text)
        self.Logger.info(f"repo_apps searching for: {text}")
        return False

    def _apply_search_results(self, token, new_apps=None):
        if token != getattr(self, "_current_search_token", None):
            return False
        if new_apps:
            self._append_apps_to_flowbox(new_apps)
        else:
            self.ui_parslinuxapps_flowbox.invalidate_filter()
        return False

    def _clear_repo_results(self):
        if self.ui_repoapps_flowbox:
            for row in list(self.ui_repoapps_flowbox.get_children()):
                self.ui_repoapps_flowbox.remove(row)
        self.repo_final_list = []

    def _start_repo_search(self, text):
        self._search_start_id = None

        if self._repo_search_cancel_flag or len(text) < 3:
            return False

        repo_list = self.Package.load_repo_packages()

        GLib.idle_add(self._clear_repo_results)

        self._repo_search_text = text
        self._repo_startswith = []
        self._repo_contains = []
        self._repo_results = []
        self._repo_matched_set = set()
        self._repo_phase = "startswith"

        self._repo_iter = iter(repo_list)

        self._search_step_id = GLib.idle_add(self._repo_search_step)
        return False

    def _repo_search_step(self):
        if self._repo_search_cancel_flag:
            self._search_step_id = None
            return False

        if self._repo_phase not in ("startswith", "contains"):
            self._search_step_id = None
            return False

        text = self._repo_search_text
        CHUNK = 400

        try:
            if self._repo_phase == "startswith":
                for _ in range(CHUNK):
                    pkg = next(self._repo_iter)
                    name = pkg.lower()
                    if name.startswith(text):
                        if pkg not in self._repo_matched_set:
                            self._repo_startswith.append(pkg)
                            self._repo_matched_set.add(pkg)

                            if len(self._repo_startswith) >= 6:
                                return self._repo_search_finish()
                return True

            elif self._repo_phase == "contains":
                for _ in range(CHUNK):
                    pkg = next(self._repo_iter)
                    name = pkg.lower()
                    if pkg in self._repo_matched_set:
                        continue
                    if text in name:
                        self._repo_contains.append(pkg)
                        self._repo_matched_set.add(pkg)

                        if len(self._repo_startswith) + len(self._repo_contains) >= 6:
                            return self._repo_search_finish()
                return True

        except StopIteration:
            if self._repo_phase == "startswith":
                repo_list = self.Package.load_repo_packages()
                self._repo_iter = iter(repo_list)
                self._repo_phase = "contains"
                return True
            else:
                return self._repo_search_finish()

        return True

    def _repo_search_finish(self):
        self._search_step_id = None

        if self._repo_search_cancel_flag:
            return False

        self.repo_final_list = list(self._repo_startswith)

        if len(self.repo_final_list) < 6:
            need = 6 - len(self.repo_final_list)
            self.repo_final_list += self._repo_contains[:need]

        for pkg in self.repo_final_list:
            widget = self.create_app_widget(pkg, repo_app=True)
            GLib.idle_add(self.ui_repoapps_flowbox.add, widget)

        GLib.idle_add(self.ui_repoapps_flowbox.show_all)
        GLib.idle_add(self.ui_repotitle_box.set_visible, bool(self.repo_final_list))

        self.Logger.info(f"repo_apps search startswith list: {self._repo_startswith}")
        self.Logger.info(f"repo_apps search contains list: {self._repo_contains}")
        self.Logger.info(f"repo_apps search final list: {self.repo_final_list}")

        self._repo_startswith = []
        self._repo_contains = []
        self._repo_matched_set = set()
        self._repo_phase = None
        return False

    def on_ui_top_searchentry_activate(self, entry):
        pass

    def on_ui_top_searchentry_icon_press(self, entry, icon_pos, event):
        pass
