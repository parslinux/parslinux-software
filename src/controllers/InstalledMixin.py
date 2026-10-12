import os
import threading
import locale
import gettext
from datetime import datetime

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango, GdkPixbuf

_ = gettext.gettext


class InstalledMixin:
    """Kurulu uygulamalar (MyApps), güncellemeler ve disk kullanımı hesaplama mixin'i."""

    def get_upgradables(self):
        if not self.Server.connection:
            return
        self.upgradables = {}
        for app, details in self.apps.items():
            is_installed = self.Package.isinstalled(app)
            is_upgradable = self.Package.is_upgradable(app)

            if is_installed and is_upgradable:
                self.upgradables[app] = details

        # Flatpak güncellemelerini de ekle
        try:
            if hasattr(self.Package, "get_upgradable_apps"):
                flatpak_upgradables = self.Package.get_upgradable_apps()
                for fp_id, fp_info in flatpak_upgradables.items():
                    if fp_id not in self.upgradables:
                        details = self.apps.get(fp_id)
                        if not details:
                            details = {
                                "name": fp_id,
                                "description": _("Flatpak update available"),
                                "icon_name": fp_id,
                                "category": "Updates",
                                "package_names": [fp_id],
                                "flatpak": True,
                            }
                        self.upgradables[fp_id] = details
        except Exception as e:
            self.Logger.warning(f"Error fetching Flatpak upgradables: {e}")

        self.Logger.info(f"Upgradable apps: {', '.join(self.upgradables.keys())}")

    def on_update_all_clicked(self, button):
        if not self.upgradables:
            return

        button.set_sensitive(False)
        self.Logger.info(f"Updating all apps: {list(self.upgradables.keys())}")

        for app_name, details in list(self.upgradables.items()):
            if any(item.get("name") == app_name for item in self.queue) or getattr(self, "inprogress_app_name", "") == app_name:
                continue

            command = self.get_action_command(app_name, details)
            desktop_id = details.get("desktop", "")

            self.queue.append({"name": app_name, "command": command, "desktop_id": desktop_id, "upgrade": True})
            self.add_to_queue_ui(app_name, True, details.get("icon_name"))
            self.update_app_widget_label(app_name)

        if not getattr(self, "inprogress", False) and len(self.queue) > 0:
            first = self.queue[0]
            self.ui_header_queue_button.set_visible(True)
            self.ui_queue_stack.set_visible_child_name("inprogress")
            self.action_package(first["name"], first["command"], first["desktop_id"], first["upgrade"])

    def set_upgradables(self):
        if not self.Server.connection:
            return
        self.Logger.info("in set_upgradables")

        GLib.idle_add(lambda: (self.ui_upgradableapps_flowbox and self.ui_upgradableapps_flowbox.foreach(
            lambda row: self.ui_upgradableapps_flowbox.remove(row)), False))

        GLib.idle_add(lambda: (self.ui_leftupdates_listbox and self.ui_leftupdates_listbox.foreach(
            lambda child: self.ui_leftupdates_listbox.remove(child)), False))

        GLib.idle_add(self.ui_leftupdates_separator.set_visible, bool(self.upgradables))
        GLib.idle_add(self.ui_upgradableapps_box.set_visible, bool(self.upgradables))

        # 'Tümünü Güncelle' butonunu ekle/güncelle
        if not hasattr(self, "ui_update_all_button") or self.ui_update_all_button is None:
            self.ui_update_all_button = Gtk.Button.new_with_label(_("Update All"))
            self.ui_update_all_button.get_style_context().add_class("suggested-action")
            self.ui_update_all_button.set_tooltip_text(_("Update all pending applications"))
            self.ui_update_all_button.connect("clicked", self.on_update_all_clicked)
            if hasattr(self, "ui_upgradableapps_box") and self.ui_upgradableapps_box:
                self.ui_upgradableapps_box.pack_end(self.ui_update_all_button, False, False, 6)

        if hasattr(self, "ui_update_all_button") and self.ui_update_all_button:
            has_updates = bool(self.upgradables)
            is_in_progress = getattr(self, "inprogress", False)
            GLib.idle_add(self.ui_update_all_button.set_visible, has_updates)
            GLib.idle_add(self.ui_update_all_button.set_sensitive, has_updates and not is_in_progress)

        if self.Server.connection and self.upgradables:
            updates_icon = Gtk.Image.new_from_icon_name("ps-cat-updates-symbolic", Gtk.IconSize.BUTTON)
            updates_icon.props.halign = Gtk.Align.START

            label = Gtk.Label.new()
            label.set_markup("<b>{}</b>".format(_("Updates")))
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(15)

            box_updates_count = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            label_updates_count = Gtk.Label.new()
            label_updates_count.set_markup("{}".format(len(self.upgradables)))
            label_updates_count.set_margin_start(5)
            label_updates_count.set_margin_end(5)
            label_updates_count.set_margin_top(3)
            label_updates_count.set_margin_bottom(3)
            box_updates_count.pack_start(label_updates_count, False, True, 0)
            box_updates_count.props.halign = Gtk.Align.END
            box_updates_count.get_style_context().add_class("parslinux-software-left-updates-count-box")

            label_updates = Gtk.Label.new()
            label_updates.set_markup("<small>{}</small>".format(_("Some applications are outdated.")))
            label_updates.set_max_width_chars(23)
            label_updates.set_ellipsize(Pango.EllipsizeMode.END)
            label_updates.props.halign = Gtk.Align.START
            label_updates.set_margin_start(3)
            label_updates.set_opacity(0.7)

            box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box_h.pack_start(updates_icon, False, True, 0)
            box_h.pack_start(label, False, True, 0)
            box_h.pack_end(box_updates_count, True, True, 0)

            box_v = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
            box_v.pack_start(box_h, False, True, 0)
            box_v.pack_start(label_updates, False, True, 0)
            box_v.set_margin_start(8)
            box_v.set_margin_end(12)
            box_v.set_margin_top(5)
            box_v.set_margin_bottom(5)
            box_v.set_spacing(8)

            row = Gtk.ListBoxRow()
            row.add(box_v)
            row.name = "updates"
            row.props.valign = Gtk.Align.END
            row.set_vexpand(True)

            GLib.idle_add(self.ui_leftupdates_listbox.add, row)

            for app, details in self.upgradables.items():
                listbox = self.create_upgradable_myapp_widget(app, details)
                GLib.idle_add(self.ui_upgradableapps_flowbox.insert, listbox, -1)

            self.ui_upgradableapps_count_label.set_markup("<span size='large'><b>({})</b></span>".format(len(self.upgradables)))

            GLib.idle_add(self.ui_upgradableapps_flowbox.show_all)
            GLib.idle_add(self.ui_leftupdates_listbox.show_all)

        self.Logger.info("set_upgradables done")

    def create_myapp_widget(self, app, du=False):
        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(GLib.markup_escape_text(app["name"], -1)))
        app_name.props.halign = Gtk.Align.START
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)

        try:
            if os.path.isfile(app["icon_name"]):
                px = GdkPixbuf.Pixbuf.new_from_file_at_size(app["icon_name"], 32, 32)
                app_icon = Gtk.Image.new()
                app_icon.set_from_pixbuf(px)
            else:
                app_icon = Gtk.Image.new_from_icon_name(app["icon_name"], Gtk.IconSize.DND)
        except Exception as e:
            app_icon = Gtk.Image.new_from_icon_name("image-missing-symbolic", Gtk.IconSize.DND)
            self.Logger.exception("Exception on create_myapp_widget: {}, app: {}".format(e, app))
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("parslinux-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        action_button = Gtk.Button.new()
        action_button.connect("clicked", self.open_from_myapps)
        action_button.props.valign = Gtk.Align.CENTER
        action_button.set_size_request(77, -1)
        action_button_label = Gtk.Label.new()
        action_button_label.set_line_wrap(False)
        action_button_label.set_justify(Gtk.Justification.LEFT)
        action_button_label.set_max_width_chars(6)
        action_button_label.set_ellipsize(Pango.EllipsizeMode.END)
        action_button.add(action_button_label)
        self.set_button_class(action_button, 4)
        action_button_label.set_markup("<small>{}</small>".format(_("Open")))
        action_button.name = app["id"]

        uninstallbutton = Gtk.Button.new()
        uninstallbutton.name = app
        uninstallbutton.props.valign = Gtk.Align.CENTER
        uninstallbutton.props.always_show_image = True
        uninstallbutton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        uninstallbutton.set_label("")
        uninstallbutton.set_tooltip_text(_("Uninstall"))
        uninstallbutton.set_relief(Gtk.ReliefStyle.NONE)
        uninstallbutton.connect("clicked", self.remove_from_myapps_popup)

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(
            GLib.markup_escape_text(app["description"], -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(33)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)

        du_static = Gtk.Label.new()
        du_static.set_line_wrap(False)

        du_size = Gtk.Label.new()
        du_size.set_line_wrap(False)

        box_du = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_du.props.halign = Gtk.Align.START
        box_du.pack_start(du_static, False, True, 0)
        box_du.pack_start(du_size, False, True, 0)
        box_du.set_size_request(77, -1)

        if du:
            du_static.set_markup("<b>{}</b>".format(_("Disk Usage")))
            du_size.set_markup("<span weight='light' size='small'>{}</span>".format(self.Package.beauty_size(app["disk_usage"])))
        else:
            du_static.set_markup("")
            du_size.set_markup("")

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_end(uninstallbutton, False, True, 0)
        box_h.pack_end(action_button, False, True, 0)
        box_h.pack_end(box_du, False, True, 40 if self.display_width >= 1920 else 20)

        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        bottom_separator.get_style_context().add_class("parslinux-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect("row-activated", self.on_myapp_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        listbox_row.add(box)
        listbox_row.name = app
        listbox.add(listbox_row)

        listbox.get_style_context().add_class("parslinux-software-listbox-mostdown")
        return listbox

    def create_upgradable_myapp_widget(self, app, details=None):
        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(GLib.markup_escape_text("{}".format(self.get_pretty_name_from_app_name(app)), -1)))
        app_name.props.halign = Gtk.Align.START
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)

        app_icon = Gtk.Image.new_from_icon_name(app, Gtk.IconSize.DND)
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("parslinux-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        action_button = Gtk.Button.new()
        action_button.connect("clicked", self.app_widget_action_clicked)
        action_button.props.valign = Gtk.Align.CENTER
        action_button.set_size_request(77, -1)
        if hasattr(self, "app_action_buttons"):
            self.app_action_buttons.setdefault(app, []).append(action_button)

        action_button_label = Gtk.Label.new()
        action_button_label.set_line_wrap(False)
        action_button_label.set_justify(Gtk.Justification.LEFT)
        action_button_label.set_max_width_chars(6)
        action_button_label.set_ellipsize(Pango.EllipsizeMode.END)

        is_installed = self.Package.isinstalled(app)
        is_upgradable = self.Package.is_upgradable(app)
        is_openable = self.get_desktop_filename_from_app_name(app) != ""
        is_in_queue = any(item.get("name") == app for item in self.queue)
        if is_installed is not None:
            if is_in_queue:
                self.set_button_class(action_button, 2)
                spinner = Gtk.Spinner()
                action_button.add(spinner)
                spinner.start()
                spinner.show_all()
            else:
                action_button.add(action_button_label)
                if is_installed:
                    if is_upgradable:
                        self.set_button_class(action_button, 3)
                        action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                        action_button.name = 2
                    else:
                        if is_openable:
                            self.set_button_class(action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            action_button.name = 3
                        else:
                            self.set_button_class(action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            action_button.name = 9
                else:
                    self.set_button_class(action_button, 0)
                    action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                    action_button.name = 1
        else:
            self.set_button_class(action_button, 2)
            not_found_image = Gtk.Image.new_from_icon_name("action-unavailable-symbolic", Gtk.IconSize.BUTTON)
            action_button.add(not_found_image)

        uninstallbutton = Gtk.Button.new()
        uninstallbutton.name = 0
        uninstallbutton.props.valign = Gtk.Align.CENTER
        uninstallbutton.props.always_show_image = True
        uninstallbutton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        uninstallbutton.set_label("")
        uninstallbutton.set_tooltip_text(_("Uninstall"))
        uninstallbutton.set_relief(Gtk.ReliefStyle.NONE)
        uninstallbutton.connect("clicked", self.app_widget_action_clicked)
        uninstallbutton.set_sensitive(not is_in_queue)

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(GLib.markup_escape_text(
            self.get_sub_category_name_from_app_name(app), -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(33)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)

        du_static = Gtk.Label.new()
        du_static.set_line_wrap(False)
        du_static.set_markup("")

        du_size = Gtk.Label.new()
        du_size.set_line_wrap(False)
        du_size.set_markup("")

        box_du = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_du.props.halign = Gtk.Align.CENTER
        box_du.pack_start(du_static, False, True, 0)
        box_du.pack_start(du_size, False, True, 0)
        box_du.set_size_request(177, -1)

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_end(uninstallbutton, False, True, 0)
        box_h.pack_end(action_button, False, True, 0)
        box_h.pack_end(box_du, False, True, 40 if self.display_width >= 1920 else 20)

        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        bottom_separator.get_style_context().add_class("parslinux-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect("row-activated", self.on_app_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        listbox_row.add(box)
        listbox_row.name = {app: details} if details else app
        listbox.add(listbox_row)

        listbox.get_style_context().add_class("parslinux-software-listbox-mostdown")
        return listbox

    def set_myapps(self, du=False):
        def clear_flowbox():
            if self.ui_installedapps_flowbox:
                self.ui_installedapps_flowbox.foreach(
                    lambda row: self.ui_installedapps_flowbox.remove(row)
                )
            return False

        GLib.idle_add(self.ui_myapps_combobox.set_sensitive, False)
        GLib.idle_add(clear_flowbox)

        if du:
            GLib.idle_add(self.ui_myapps_du_progress_box.set_visible, True)
            GLib.idle_add(self.ui_myapps_du_spinner.start)
            self.myapps_du_cancel_event = threading.Event()

        def run_worker():
            processed = {"count": 0}
            total = {"count": 0}

            def total_callback(count):
                total["count"] = count
                GLib.idle_add(
                    self.ui_myapps_du_progress_label.set_text,
                    f"0 / {count}",
                )

            def progress_callback():
                processed["count"] += 1
                if total["count"]:
                    GLib.idle_add(
                        self.ui_myapps_du_progress_label.set_text,
                        f"{processed['count']} / {total['count']}",
                    )

            if du:
                myapps = self.myapps_worker(
                    du=True,
                    cancel_event=self.myapps_du_cancel_event,
                    progress_callback=progress_callback,
                    total_callback=total_callback,
                )
            else:
                myapps = self.myapps_worker(
                    du=False,
                    cancel_event=self.myapps_du_cancel_event,
                )

            if myapps is not None:
                GLib.idle_add(self.on_myapps_worker_done, myapps, du)
            else:
                GLib.idle_add(self.on_myapps_worker_cancelled)

        threading.Thread(target=run_worker, daemon=True).start()

    def myapps_worker(self, du=False, cancel_event=None, progress_callback=None, total_callback=None):
        return self.Package.get_installed_apps(
            du=du,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            total_callback=total_callback,
        )

    def on_myapps_worker_done(self, myapps, du=False):
        for pkg in myapps:
            self.add_to_myapps_ui(pkg, du=du)
        GLib.idle_add(self.ui_myapps_du_progress_box.set_visible, False)
        GLib.idle_add(self.ui_myapps_du_spinner.stop)
        GLib.idle_add(self.ui_myapps_combobox.set_sensitive, True)
        GLib.idle_add(self.ui_installedapps_flowbox.show_all)
        GLib.idle_add(self.control_args)
        if du:
            self.ui_installedapps_flowbox.set_sort_func(None)
        self.Logger.info("on_myapps_worker_done")

    def on_myapps_worker_cancelled(self):
        GLib.idle_add(self.ui_myapps_du_spinner.stop)
        GLib.idle_add(self.ui_myapps_du_progress_box.set_visible, False)
        GLib.idle_add(self.ui_myapps_combobox.set_sensitive, True)
        self.Logger.info("on_myapps_worker_cancelled")
        self.myapps_du_cancel_event = None
        self.Logger.info("on_myapps_worker_cancelled: setting apps as default")
        GLib.idle_add(self.ui_myapps_combobox.set_active, 0)

    def on_myapps_du_cancel_button_clicked(self, button):
        if self.myapps_du_cancel_event:
            self.myapps_du_cancel_event.set()

    def myappsdetail_popup_worker_thread(self, app, popup=False):
        myappdetails = self.myappsdetail_popup_worker(app)
        GLib.idle_add(self.on_myappsdetail_popup_worker_done, myappdetails, popup)

    def myappsdetail_popup_worker(self, app):
        valid, myapp_details, myapp_package = self.Package.myapps_remove_details(app["filename"])
        self.Logger.info("{}".format(myapp_details))
        return valid, myapp_details, myapp_package, app["name"], app["icon_name"], app["filename"], app["description"]

    def on_myappsdetail_popup_worker_done(self, myapp, popup=False):
        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""
        self.myapp_toremove_icon = ""

        valid, details, package, name, icon, desktop, description = myapp
        if valid and details is not None:
            self.ui_myapp_pop_app.set_markup(
                "<span size='large'><b>{}</b></span>".format(GLib.markup_escape_text(name, -1)))
            self.ui_myapp_pop_package.set_markup("<i>{}</i>".format(package))
            self.myapp_toremove_icon = icon
            self.ui_myapp_pop_uninstall_button.set_sensitive(True)

            if details["to_delete"] and details["to_delete"] is not None:
                self.ui_myapp_pop_toremove_label.set_markup(
                    "{}".format(", ".join(details["to_delete"])))
                self.ui_myapp_pop_toremove_box.set_visible(True)
                self.myapp_toremove_list = details["to_delete"]
                self.myapp_toremove = package
                self.myapp_toremove_desktop = desktop

            if details["to_install"] and details["to_install"] is not None:
                self.ui_myapp_pop_toinstall_label.set_markup(
                    "{}".format(", ".join(details["to_install"])))
                self.ui_myapp_pop_toinstall_box.set_visible(True)

            if details["broken"] and details["broken"] is not None:
                self.ui_myapp_pop_broken_label.set_markup(
                    "{}".format(", ".join(details["broken"])))
                self.ui_myapp_pop_broken_box.set_visible(True)

            if details["freed_size"] and details["freed_size"] is not None and details["freed_size"] > 0:
                self.ui_myapp_pop_fsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["freed_size"])))
                self.ui_myapp_pop_fsize_box.set_visible(True)

            if details["download_size"] and details["download_size"] is not None and details["download_size"] > 0:
                self.ui_myapp_pop_dsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["download_size"])))
                self.ui_myapp_pop_dsize_box.set_visible(True)

            if details["install_size"] and details["install_size"] is not None and details["install_size"] > 0:
                self.ui_myapp_pop_isize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["install_size"])))
                self.ui_myapp_pop_isize_box.set_visible(True)

            self.ui_myapp_pop_stack.set_visible_child_name("details")
            self.ui_myapp_pop_uninstall_button.grab_focus()

        else:
            self.Logger.info("package not found: {}".format(myapp))
            self.ui_myapp_pop_stack.set_visible_child_name("notfound")

            try:
                if os.path.isfile(icon):
                    px = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, 64, 64)
                    self.ui_myapp_pop_notfound_image.set_from_pixbuf(px)
                else:
                    self.ui_myapp_pop_notfound_image.set_from_icon_name(icon, Gtk.IconSize.DIALOG)
            except Exception as e:
                self.ui_myapp_pop_notfound_image.set_from_icon_name("image-missing-symbolic", Gtk.IconSize.DIALOG)
            self.ui_myapp_pop_notfound_image.set_pixel_size(64)
            self.ui_myapp_pop_notfound_name.set_markup("<span size='large'><b>{}</b></span>".format(name))

    def on_ui_myapp_details_popover_closed(self, popover):
        self.ui_myapp_pop_spinner.stop()
        self.ui_myapp_pop_stack.set_visible_child_name("spinner")
        self.ui_myapp_pop_app.set_can_focus(False)
        self.ui_myapp_pop_package.set_can_focus(False)
        self.ui_myapp_pop_toremove_label.set_can_focus(False)
        self.ui_myapp_pop_toinstall_label.set_can_focus(False)
        self.ui_myapp_pop_broken_label.set_can_focus(False)
        self.ui_myapp_pop_fsize_label.set_can_focus(False)
        self.ui_myapp_pop_dsize_label.set_can_focus(False)
        self.ui_myapp_pop_isize_label.set_can_focus(False)

    def on_ui_myapp_pop_close_clicked(self, button):
        self.ui_myapp_details_popover.popdown()

    def on_myapp_listbox_row_activated(self, listbox, row):
        self.Logger.info(f"on_myapp_listbox_row_activated: {row.name}")
        GLib.idle_add(listbox.get_parent().get_parent().unselect_all)
        threading.Thread(target=self.myappsdetail_page_worker_thread,
                         args=(row.name["filename"], row.name,), daemon=True).start()

    def myappsdetail_page_worker_thread(self, filename, details):
        package = self.myappsdetail_page_worker(filename)
        GLib.idle_add(self.on_myappsdetail_page_worker_done, package, details)

    def myappsdetail_page_worker(self, filename):
        return self.Package.get_appname_from_desktopfile(filename)

    def on_myappsdetail_page_worker_done(self, package, details):
        found, package_name = package
        if found:
            if package_name in self.apps_full.keys():
                self.set_app_details_page(app=package_name, source=1)
            else:
                self.set_app_details_page(app={package_name: details}, source=2)
        else:
            self.set_app_details_page(app={package_name: details}, source=0)

    def installedapps_filter_function(self, row):
        search_entry_text = self.ui_top_searchentry.get_text().lower()
        app = row.get_children()[0].get_children()[0].name

        name = app.get("name", "")
        description = app.get("description", "")
        keywords = app.get("keywords", "")
        executable = app.get("executable", "")

        if self.searching:
            if any(search_entry_text in field.lower() for field in [name, description, keywords, executable]):
                return True
        else:
            return True

        return False

    def parslinuxapps_filter_function(self, row):
        try:
            listbox = row.get_child() or (row.get_children()[0] if row.get_children() else None)
            if not listbox:
                return True

            appname = getattr(listbox, "app_name", None)
            details = getattr(listbox, "app_details", None)

            if not appname:
                listbox_children = listbox.get_children()
                if not listbox_children:
                    return True
                name_obj = getattr(listbox_children[0], "name", None)
                if isinstance(name_obj, dict):
                    appname, details = next(iter(name_obj.items()))
                elif isinstance(name_obj, str):
                    appname = name_obj
                    details = self.apps_full.get(appname, {}) if hasattr(self, "apps_full") else {}
                else:
                    return True

            if not details:
                details = self.apps_full.get(appname, {}) if hasattr(self, "apps_full") else {}

            search_entry_text = self.ui_top_searchentry.get_text().strip().lower()

            if self.searching and search_entry_text:
                pretty = details.get("prettyname", {}) if isinstance(details, dict) else {}
                if isinstance(pretty, dict):
                    pn_en = pretty.get("en", "")
                    pn_tr = pretty.get("tr", "")
                else:
                    pn_en = pn_tr = str(pretty or "")

                desc = details.get("description", {}) if isinstance(details, dict) else {}
                if isinstance(desc, dict):
                    desc_en = desc.get("en", "")
                    desc_tr = desc.get("tr", "")
                else:
                    desc_en = desc_tr = str(desc or "")

                display_name = details.get("display_name", "") if isinstance(details, dict) else ""
                search_fields = [appname, pn_en, pn_tr, desc_en, desc_tr, display_name]
                return any(search_entry_text in field.lower() for field in search_fields if field)

            current_cat = getattr(self, "current_category", "").lower()
            all_cat_name = (self.cat_all.get("name", "") if isinstance(self.cat_all, dict) else "").lower()

            if not current_cat or current_cat in ("all", "tümü", "discover", all_cat_name):
                return True

            categories = details.get("category", []) if isinstance(details, dict) else []
            for cat in categories:
                if isinstance(cat, dict):
                    cat_vals = [
                        cat.get(self.user_locale, "").lower(),
                        cat.get("en", "").lower(),
                        cat.get("id", "").lower(),
                        cat.get("icon", "").lower()
                    ]
                    if current_cat in cat_vals:
                        return True
                elif isinstance(cat, str) and current_cat == cat.lower():
                    return True

            return False
        except Exception:
            return True

    def on_ui_parslinuxapps_combobox_changed(self, combo_box):
        active_idx = combo_box.get_active()
        self._current_sort_mode = active_idx
        try:
            if active_idx == 0:  # sort by name
                self.apps = dict(sorted(self.apps.items(),
                                        key=lambda item: locale.strxfrm(str(item[1].get("prettyname", {}).get(self.user_locale, item[0])))))
            elif active_idx == 1:  # sort by download
                self.apps = dict(sorted(
                    self.apps.items(),
                    key=lambda item: (item[1].get("download", 0), item[1].get("rate_average", 0)),
                    reverse=True
                ))
            elif active_idx == 2:  # sort by popularity
                self.apps = dict(sorted(
                    self.apps.items(),
                    key=lambda item: (item[1].get("popularity", item[1].get("rate_average", 0)), item[1].get("download", 0)),
                    reverse=True
                ))
            elif active_idx == 3:  # sort by last added
                self.apps = dict(sorted(
                    self.apps.items(),
                    key=lambda item: str(item[1].get("date", "")),
                    reverse=True
                ))
        except Exception:
            pass
        GLib.idle_add(self.ui_parslinuxapps_flowbox.invalidate_sort)

    def on_ui_upgradables_combobox_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            self.upgradables = dict(sorted(self.upgradables.items(),
                                           key=lambda item: locale.strxfrm(item[1]["prettyname"][self.user_locale])))
            GLib.idle_add(self.set_upgradables)
        elif combo_box.get_active() == 1:  # sort by download
            self.upgradables = dict(sorted(
                self.upgradables.items(),
                key=lambda item: (item[1]["download"], item[1]["rate_average"]),
                reverse=True
            ))
            GLib.idle_add(self.set_upgradables)
        elif combo_box.get_active() == 2:  # sort by popularity
            self.upgradables = dict(sorted(
                self.upgradables.items(),
                key=lambda item: (item[1].get("popularity", item[1]["rate_average"]), item[1]["download"]),
                reverse=True
            ))
            GLib.idle_add(self.set_upgradables)
        elif combo_box.get_active() == 3:  # sort by last added
            self.upgradables = dict(sorted(
                self.upgradables.items(),
                key=lambda item: datetime.strptime(item[1]["date"], "%d-%m-%Y %H:%M"),
                reverse=True
            ))
            GLib.idle_add(self.set_upgradables)

    def on_ui_myapps_combobox_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            GLib.idle_add(self.set_myapps)
        elif combo_box.get_active() == 1:  # sort by disk usage
            GLib.idle_add(self.set_myapps, True)

    def add_to_myapps_ui(self, app, du=False):
        listbox = self.create_myapp_widget(app, du=du)
        GLib.idle_add(self.ui_installedapps_flowbox.insert, listbox, -1)

    def remove_from_myapps_popup(self, button):
        self.Logger.info("remove_from_myapps_popup {}".format(button.name))

        self.ui_myapp_pop_toremove_box.set_visible(False)
        self.ui_myapp_pop_toinstall_box.set_visible(False)
        self.ui_myapp_pop_broken_box.set_visible(False)
        self.ui_myapp_pop_fsize_box.set_visible(False)
        self.ui_myapp_pop_dsize_box.set_visible(False)
        self.ui_myapp_pop_isize_box.set_visible(False)

        self.ui_myapp_pop_spinner.start()
        self.ui_myapp_pop_stack.set_visible_child_name("spinner")

        self.ui_myapp_details_popover.set_relative_to(button)
        self.ui_myapp_details_popover.popup()

        threading.Thread(target=self.myappsdetail_popup_worker_thread, args=(button.name, True,), daemon=True).start()

    def open_from_myapps(self, button):
        self.Logger.info("Opening {}".format(button.name))
        self.launch_desktop_file(button.name)

    def on_ui_myapp_pop_uninstall_button_clicked(self, button):
        importants = [i for i in self.important_packages if i in self.myapp_toremove_list]
        if importants:
            self.ui_myapp_pop_stack.set_visible_child_name("disclaimer")
            self.ui_myapp_pop_disclaimer_remove_label.set_markup("{}".format(", ".join(importants)))
        else:
            self.Logger.info("not important package")
            self.ui_myapps_uninstall()

    def on_ui_myapp_pop_accept_disclaimer_clicked(self, button):
        self.ui_myapp_pop_stack.set_visible_child_name("details")
        self.ui_myapps_uninstall()

    def on_ui_myapp_pop_cancel_disclaimer_clicked(self, button):
        self.ui_myapp_pop_stack.set_visible_child_name("details")

    def ui_myapps_uninstall(self):
        self.ui_header_queue_button.set_visible(True)
        self.ui_queue_stack.set_visible_child_name("inprogress")

        self.ui_myapp_pop_uninstall_button.set_sensitive(False)

        self.queue.append({"name": self.myapp_toremove, "command": self.myapp_toremove,
                           "desktop_id": self.myapp_toremove_desktop, "upgrade": False})
        self.add_to_queue_ui(self.myapp_toremove, icon_name=self.myapp_toremove_icon)
        if not self.inprogress:
            self.action_package(self.myapp_toremove, self.myapp_toremove, self.myapp_toremove_desktop)
            self.inprogress = True
            self.Logger.info("action_package app: {}, command: {}, desktop_id: {}, upgrade: {}".format(
                self.myapp_toremove, self.myapp_toremove, self.myapp_toremove_desktop, False))

    def myapps_filter_func(self, row):
        myapp_name = row.get_children()[0].get_children()[3].name
        search = self.myapps_searchentry.get_text().lower()
        if search in myapp_name["name"].lower() or search in myapp_name["description"].lower() or \
                search in myapp_name["keywords"].lower() or search in myapp_name["executable"].lower():
            return True

    def installedapps_sort_func(self, row1, row2):
        return locale.strxfrm(row1.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].name["name"]) > locale.strxfrm(
            row2.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].name["name"])
