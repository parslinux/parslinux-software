import os
import re
import subprocess
import gettext
from datetime import datetime

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf, Vte

from Package import Package

_ = gettext.gettext


class QueueMixin:
    """Kuyruk yönetimi, paket kurulum/kaldırma eylemleri, Flatpak asenkron çalıştırma ve alt süreçler mixin'i."""

    def on_queue_cancel_button_clicked(self, button):
        for fbc in self.ui_queue_flowbox.get_children():
            lb = fbc.get_child()
            if lb.get_children():
                lbr = lb.get_children()[0]
                if lbr.name == button.name:
                    children = self.ui_queue_flowbox.get_children()
                    index = children.index(fbc)
                    if index != 0:
                        self.ui_queue_flowbox.remove(fbc)
                        q_index = next((i for i, app in enumerate(self.queue)
                                        if app["name"] == button.name), None)
                        if q_index is not None:
                            self.queue.pop(q_index)
                            self.Logger.info(f"{button.name} removed from queue, updating widget actions")
                            self.update_app_widget_label(app_name=button.name, from_queue_cancelled=True)
                    else:
                        self.Logger.info("Cancelling {} {}".format(self.inprogress_app_name, self.pid))
                        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/../Actions.py",
                                   "kill", "{}".format(self.pid)]
                        self.start_kill_process(command)
                    break

    def app_widget_action_clicked(self, button):
        app = button.get_parent().get_parent().get_parent().name

        self.Logger.info(f"app_widget_action_clicked: {app}")

        if isinstance(app, dict):
            app_name, details = next(iter(app.items()))
        elif isinstance(app, str):
            app_name = app
            details = self.apps_full.get(app_name, {})
        else:
            self.Logger.warning("{} {}".format("app_widget_action_clicked func ERROR for: ", app))
            return

        if not details:
            self.Logger.warning("{} details not found on app_widget_action_clicked.".format(app_name))
            return

        if button.name == 3:
            self.Logger.info("{} opening".format(app_name))
            if hasattr(self, "FlatpakManager") and self.FlatpakManager.is_installed(app_name):
                if self.FlatpakManager.launch(app_name):
                    return
            desktop = details.get("desktop")
            desk_id = details.get("id")
            extras = details.get("desktopextras", "")
            if desktop:
                if self.launch_desktop_file(desktop):
                    return
            if extras:
                for extra in extras.split(","):
                    if self.launch_desktop_file(extra):
                        break
            if desk_id:
                if self.launch_desktop_file(desk_id):
                    return
            return

        if button.name == 9:
            self.Logger.info("{} opening details page".format(app_name))
            repo_app = details.get("repo_app", "")
            self.set_app_details_page(app, source=1 if not repo_app else 2)
            return

        self.Logger.info("app_name: {}".format(app_name))
        self.Logger.info("details: {}".format(details))

        self.update_app_widget_label(app_name)

        command = self.get_action_command(app_name, details)
        desktop_id = details.get("desktop", "")

        self.ui_header_queue_button.set_visible(True)
        self.ui_queue_stack.set_visible_child_name("inprogress")

        self.queue.append({"name": app_name, "command": command, "desktop_id": desktop_id, "upgrade": button.name == 2})
        self.add_to_queue_ui(app_name, button.name == 2, details.get("icon_name"))
        self.Logger.info(f"queue_add: app: {app_name}")
        self.Logger.info(f"queue: {self.queue}")
        if not self.inprogress:
            self.action_package(app_name, command, desktop_id, button.name == 2)
            self.Logger.info("action_package app: {}, command: {}, desktop_id: {}, upgrade: {}".format(
                app_name, command, desktop_id, button.name == 2))

    def get_action_command(self, app_name, details):
        self.Logger.info(f"build_install_command: app_name={app_name}")

        install_recommends = details.get("install_recommends", True)
        self.Logger.info(f"install_recommends={install_recommends}")

        cmd = details.get("command") or {}
        self.Logger.info(f"raw command data: {cmd}")

        command = app_name

        if isinstance(cmd, dict):
            raw_cmd = (cmd.get(self.user_locale) or "").strip()
            self.Logger.info(f"localized raw_cmd='{raw_cmd}'")

            if raw_cmd:
                packages = [
                    p for p in raw_cmd.split()
                    if self.Package.control_package_cache(p)
                ]
                self.Logger.info(f"valid packages: {packages}")

                if packages:
                    if not install_recommends:
                        packages.append("--no-install-recommends")
                        self.Logger.info("added '--no-install-recommends'")

                    command = " ".join(packages)
                    self.Logger.info(f"final command built: {command}")
                else:
                    self.Logger.info("no valid packages found, using fallback app_name")
            else:
                self.Logger.info("raw_cmd empty, using fallback app_name")
        else:
            self.Logger.info("cmd is not a dict, using fallback app_name")

        if command == app_name and not install_recommends:
            command = f"{app_name} --no-install-recommends"
            self.Logger.info("added '--no-install-recommends' to fallback command")

        return command

    def on_ui_ad_action_button_clicked(self, button):
        if self.ui_app_name in self.apps_full.keys():
            name = self.ui_app_name
        else:
            name = self.ui_myapp_name_dic
        button.get_parent().get_parent().get_parent().name = name
        self.app_widget_action_clicked(button)

    def on_ui_ad_remove_button_clicked(self, button):
        if self.ui_app_name in self.apps_full.keys():
            name = self.ui_app_name
        else:
            name = self.ui_myapp_name_dic
        button.get_parent().get_parent().get_parent().name = name
        self.app_widget_action_clicked(button)

    def on_ui_ad_disclaimer_button_clicked(self, button):
        self.ui_disclaimer_popover.popup()

    def launch_desktop_file(self, desktop):
        try:
            subprocess.check_call(["gtk-launch", desktop])
            return True
        except subprocess.CalledProcessError as e:
            self.Logger.warning("error opening {}".format(desktop))
            self.Logger.exception("{}".format(e))
            return False

    def add_to_queue_ui(self, app_name, upgrade=False, icon_name=None):
        listbox = self.create_queue_widget(app_name, upgrade, icon_name)
        GLib.idle_add(self.ui_queue_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_queue_flowbox.show_all)

    def start_highlight_queue(self):
        if self.UserSettings.config_animations:
            self.ui_header_queue_button.get_style_context().add_class("queue-highlight")
            GLib.timeout_add_seconds(4, self.remove_highlight_queue)

    def remove_highlight_queue(self):
        if self.UserSettings.config_animations:
            self.ui_header_queue_button.get_style_context().remove_class("queue-highlight")
        return False

    def action_package(self, app_name, command, desktop_id="", upgrade=False):
        self.inprogress = True

        self.inprogress_app_name = app_name
        self.inprogress_command = command
        self.inprogress_desktop = desktop_id

        self.isinstalled = self.Package.isinstalled(app_name)
        self.isupgrade = self.Package.is_upgradable(app_name) and upgrade

        # FLATPAK ROUTING: Run without pkexec / root password
        is_flatpak = (
            getattr(self.Server, "is_flathub", False)
            or ("." in app_name and not app_name.endswith(".deb"))
            or (hasattr(self, "FlatpakManager") and self.FlatpakManager.is_installed(app_name))
        )
        if is_flatpak and hasattr(self, "FlatpakManager") and self.FlatpakManager.is_available():
            self._action_flatpak_package(app_name, upgrade=upgrade)
            return

        actions_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Actions.py")
        if self.isinstalled is True:
            if self.isupgrade:
                command = ["/usr/bin/pkexec", actions_script, "upgrade", self.inprogress_command]
            else:
                command = ["/usr/bin/pkexec", actions_script, "remove", self.inprogress_command]
        elif self.isinstalled is False:
            command = ["/usr/bin/pkexec", actions_script, "install", self.inprogress_command]
            packagelist = self.inprogress_command.split(" ")
            if [i for i in self.i386_packages if i in packagelist]:
                command = ["/usr/bin/pkexec", actions_script, "enablei386andinstall", self.inprogress_command]
        else:
            self.Logger.info("actionPackage func error")

        self.pid = self.action_process(command)
        self.Logger.info(f"started pid : {self.pid} with command: {command}")

    def _action_flatpak_package(self, app_name, upgrade=False):
        self.Logger.info(f"_action_flatpak_package: app={app_name}, upgrade={upgrade}")
        if not hasattr(self, "_queue_animation_started"):
            self._queue_animation_started = True
            self.start_highlight_queue()

        def on_progress(percent, status, raw_line):
            GLib.idle_add(self._update_queue_flatpak_progress, app_name, percent, status)

        def on_finish(success):
            GLib.idle_add(self._on_flatpak_action_finish, app_name, success)

        if self.isinstalled and not self.isupgrade:
            self.Logger.info(f"Flatpak uninstalling: {app_name}")
            self.FlatpakManager.uninstall(app_name, on_progress=on_progress, on_finish=on_finish)
        elif self.isupgrade:
            self.Logger.info(f"Flatpak updating: {app_name}")
            self.FlatpakManager.update(app_name, on_progress=on_progress, on_finish=on_finish)
        else:
            self.Logger.info(f"Flatpak installing: {app_name}")
            self.FlatpakManager.install(app_name, remote="flathub", user_mode=True, on_progress=on_progress, on_finish=on_finish)

    def _update_queue_flatpak_progress(self, app_name, percent, status):
        fraction = (percent / 100.0) if percent is not None else None
        text = status if status else (_("Installing") if not self.isinstalled else _("Removing"))
        self.update_queue_progress(app_name, fraction, text, cancel_sensitive=(percent is None or percent < 90))

    def _on_flatpak_action_finish(self, app_name, success):
        self.Logger.info(f"Flatpak action finished for {app_name}, success: {success}")
        status = 0 if success else 1
        self.error = not success
        self.on_action_process_exit(0, status)

    def update_queue_progress(self, app_name, fraction, text, cancel_sensitive=None):
        qw = getattr(self, "queue_widgets", {}).get(app_name)
        if qw:
            pb = qw.get("progress_bar")
            if pb:
                if fraction is not None:
                    pb.set_fraction(fraction)
                if text:
                    pb.set_text(text)
            if cancel_sensitive is not None:
                cb = qw.get("cancel_button")
                if cb:
                    cb.set_sensitive(cancel_sensitive)
            return

        try:
            children = self.ui_queue_flowbox.get_children()
            if children:
                row = children[0]
                if hasattr(row, "_progress_bar"):
                    if fraction is not None:
                        row._progress_bar.set_fraction(fraction)
                    if text:
                        row._progress_bar.set_text(text)
                else:
                    pb = row.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3]
                    if fraction is not None:
                        pb.set_fraction(fraction)
                    if text:
                        pb.set_text(text)
        except Exception as e:
            self.Logger.debug(f"update_queue_progress error: {e}")

    def update_app_widget_label(self, app_name, from_queue_cancelled=False):
        self.Logger.info("inprogress_app_name: {}, app_name: {}".format(self.inprogress_app_name, app_name))
        def to_spinner(action_button):
            action_button.remove(action_button.get_children()[0])
            action_button.set_sensitive(False)
            spinner = Gtk.Spinner()
            action_button.add(spinner)
            spinner.start()
            spinner.show_all()

        def to_normal(action_button):
            action_button.remove(action_button.get_children()[0])
            action_button_label = Gtk.Label.new()
            action_button_label.set_line_wrap(False)
            action_button_label.set_justify(Gtk.Justification.LEFT)
            action_button_label.set_max_width_chars(6)
            action_button_label.set_ellipsize(Pango.EllipsizeMode.END)
            is_installed = self.Package.isinstalled(app_name)
            is_upgradable = self.Package.is_upgradable(app_name)
            is_openable = self.get_desktop_filename_from_app_name(app_name) != ""
            if is_installed is not None:
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
            action_button.show_all()

        registered_buttons = getattr(self, "app_action_buttons", {}).get(app_name, [])
        for action_button in list(registered_buttons):
            try:
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)
            except Exception as e:
                self.Logger.debug(f"Action button update exception: {e}")

        if self.ui_right_stack.get_visible_child_name() == "appdetails":
            if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                to_spinner(self.ui_ad_action_button)
                self.ui_ad_remove_button.set_sensitive(False)
            else:
                to_normal(self.ui_ad_action_button)
                self.ui_ad_remove_button.set_sensitive(True)
                self.ui_ad_remove_button.set_visible(self.Package.isinstalled(app_name))

    def create_queue_widget(self, app, upgrade=False, icon_name=None):
        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(GLib.markup_escape_text(self.get_pretty_name_from_app_name(app), -1)))
        app_name.props.halign = Gtk.Align.START
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23 if self.display_width >= 1920 else 21)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)

        try:
            if os.path.isfile(icon_name if icon_name else app):
                px = GdkPixbuf.Pixbuf.new_from_file_at_size(app, 32, 32)
                app_icon = Gtk.Image.new()
                app_icon.set_from_pixbuf(px)
            else:
                app_icon = Gtk.Image.new_from_icon_name(icon_name if icon_name else app, Gtk.IconSize.DND)
        except Exception as e:
            app_icon = Gtk.Image.new_from_icon_name("image-missing-symbolic", Gtk.IconSize.DND)
            self.Logger.exception("Exception on create_queue_widget: {}, app: {}".format(e, app))
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("parslinux-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        cancel_button = Gtk.Button.new()
        cancel_button.connect("clicked", self.on_queue_cancel_button_clicked)
        cancel_button.props.valign = Gtk.Align.CENTER
        cancel_button.set_size_request(77, -1)
        cancel_button_label = Gtk.Label.new()
        cancel_button_label.set_line_wrap(False)
        cancel_button_label.set_justify(Gtk.Justification.LEFT)
        cancel_button_label.set_max_width_chars(6)
        cancel_button_label.set_ellipsize(Pango.EllipsizeMode.END)
        cancel_button.add(cancel_button_label)
        cancel_button_label.set_markup("<small>{}</small>".format(_("Cancel")))
        cancel_button.name = app

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(GLib.markup_escape_text(
            self.get_sub_category_name_from_app_name(app), -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(23 if self.display_width >= 1920 else 21)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)

        version_title = Gtk.Label.new()
        version_title.set_line_wrap(False)
        version_title.set_markup("<b>{}</b>".format(_("Version")))

        version_label = Gtk.Label.new()
        version_label.set_line_wrap(False)
        version_label.set_max_width_chars(21 if self.display_width >= 1920 else 13)
        version_label.set_ellipsize(Pango.EllipsizeMode.END)
        version_label.set_markup("<span weight='light' size='small'>{}</span>".format(self.Package.candidate_version(app)))

        box_version = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_version.props.halign = Gtk.Align.END
        box_version.props.valign = Gtk.Align.CENTER
        box_version.pack_start(version_title, False, True, 0)
        box_version.pack_start(version_label, False, True, 0)
        box_version.set_size_request(120, -1)

        progress_bar = Gtk.ProgressBar.new()
        progress_bar.set_show_text(True)
        progress_bar.set_ellipsize(Pango.EllipsizeMode.END)
        progress_bar.props.valign = Gtk.Align.CENTER
        if self.Package.isinstalled(app):
            if self.Package.is_upgradable(app) and upgrade:
                progress_bar.set_text("{}".format(_("Will be upgraded")))
            else:
                progress_bar.set_text("{}".format(_("Will be removed")))
        else:
            progress_bar.set_text("{}".format(_("Will be installed")))

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_end(cancel_button, False, True, 0)
        box_h.pack_end(progress_bar, False, True, 20 if self.display_width >= 1920 else 6)
        box_h.pack_end(box_version, False, True, 20 if self.display_width >= 1920 else 6)

        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        GLib.idle_add(bottom_separator.get_style_context().add_class, "parslinux-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox_row = Gtk.ListBoxRow()
        GLib.idle_add(listbox_row.add, box)
        listbox_row.name = app
        GLib.idle_add(listbox.add, listbox_row)

        GLib.idle_add(listbox.get_style_context().add_class, "parslinux-software-listbox-mostdown")

        listbox._progress_bar = progress_bar
        listbox._cancel_button = cancel_button
        if hasattr(self, "queue_widgets"):
            self.queue_widgets[app] = {
                "progress_bar": progress_bar,
                "cancel_button": cancel_button,
                "listbox": listbox,
            }

        return listbox

    def on_ui_header_queue_button_clicked(self, button):
        self.ui_right_stack_navigate_to("queue")
        self.remove_highlight_queue()

    def on_ui_queue_goto_discover_button_clicked(self, button):
        self.searching = False
        self.ui_leftupdates_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        self.ui_right_stack_navigate_to("discover")
        self.ui_leftcats_listbox.select_row(self.ui_leftcats_listbox.get_row_at_index(0))

    def start_kill_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_start_kill_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_start_kill_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_start_kill_process_exit)
        return pid

    def on_start_kill_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def on_start_kill_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

    def on_start_kill_process_exit(self, pid, status):
        self.Logger.info("on_start_kill_process_exit: {}".format(pid))

    def action_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_action_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_action_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_action_process_exit)
        return pid

    def on_action_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()
        self.Logger.info("{}".format(line))

        if not hasattr(self, "_queue_animation_started"):
            self._queue_animation_started = True
            self.start_highlight_queue()
            self.Logger.info("Queue animation started")

        return True

    def on_action_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()
        self.Logger.info("{}".format(line))

        if "dlstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_fraction(int(percent) / 100)
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Downloading"), percent))
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].set_sensitive(True)
        elif "pmstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_fraction(int(percent) / 100)
            if self.isinstalled:
                if self.isupgrade:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Upgrading"), percent))
                else:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Removing"), percent))
            else:
                self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Installing"), percent))
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].set_sensitive(False)
        elif re.match(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+:", line.strip()) and ".deb" in line:
            self.Logger.warning("connection error")
            self.error = True
            self.error_message += line
        elif re.match(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+:", line.strip()) and "dpkg --configure -a" in line:
            self.Logger.warning("dpkg --configure -a error")
            self.error = True
            self.dpkgconferror = True
        elif re.match(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+:", line.strip()) and "/var/lib/dpkg/lock-frontend" in line:
            self.Logger.warning("/var/lib/dpkg/lock-frontend error")
            self.error = True
            self.dpkglockerror = True
            self.dpkglockerror_message += line
        elif "parslinux-software-i386-start" in line:
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{}".format(_("i386 activating")))
        return True

    def on_action_process_exit(self, pid, status):
        if not self.error:
            if status == 0:
                self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_fraction(1)
                if self.isinstalled:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text(_("Removed: 100%"))
                else:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text(_("Installed: 100%"))
            else:
                self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text(_("Not Completed"))
        else:
            self.errormessage = _("<b><span color='red'>Connection Error!</span></b>")
            if self.dpkglockerror:
                self.errormessage = _("<b><span color='red'>Dpkg Lock Error!</span></b>")
            elif self.dpkgconferror:
                self.errormessage = _("<b><span color='red'>Dpkg Interrupt Error!</span></b>")

        cachestatus = self.Package.updatecache()
        if hasattr(self, "FlatpakManager"):
            self.FlatpakManager.refresh_installed()

        self.Logger.info("Cache Status: {}, Package Cache Status: {}".format(
            cachestatus, self.Package.control_package_cache(self.inprogress_app_name)))

        if status == 0 and not self.error and cachestatus:
            if self.Package.control_package_cache(self.inprogress_app_name):
                self.notify()
                self.send_downloaded_request(self.inprogress_app_name)
            else:
                if self.isinstalled:
                    self.notify()

        self.control_myapps(self.inprogress_app_name, self.inprogress_desktop, status, self.error, cachestatus)
        self.update_app_widget_label(self.inprogress_app_name)

        self.Logger.info("Exit Code: {}".format(status))

        self.inprogress = False
        self.inprogress_app_name = ""
        self.inprogress_command = ""
        self.inprogress_desktop = ""

        self.Logger.info(f"queue: {self.queue}")

        if len(self.queue) > 0:
            popped = self.queue[0]
            self.Logger.info(f"queue_pop: {popped}")
            self.queue.pop(0)
            if hasattr(self, "queue_widgets"):
                self.queue_widgets.pop(popped.get("name"), None)
            if self.ui_queue_flowbox.get_children():
                self.ui_queue_flowbox.remove(self.ui_queue_flowbox.get_children()[0])
            self.Logger.info(f"queue: {self.queue}")

        if self.isupgrade:
            self.get_upgradables()
            self.set_upgradables()

        if len(self.queue) > 0:
            self.action_package(self.queue[0]["name"], self.queue[0]["command"], self.queue[0]["desktop_id"],
                                self.queue[0]["upgrade"])
            self.Logger.info("action_package app: {}, command: {}, desktop_id: {}, upgrade: {}".format(
                self.queue[0]["name"], self.queue[0]["command"], self.queue[0]["desktop_id"],
                self.queue[0]["upgrade"]))
            progressbar = self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[
                0].get_children()[0].get_children()[3]
            if self.Package.isinstalled(self.inprogress_app_name):
                if self.Package.is_upgradable(self.inprogress_app_name) and self.queue[0]["upgrade"]:
                    progressbar.set_text("{}".format(_("Upgrading")))
                else:
                    progressbar.set_text("{}".format(_("Removing")))
            else:
                progressbar.set_text("{}".format(_("Installing")))
        else:
            self.bottomrevealer.set_reveal_child(False)
            self.ui_header_queue_button.set_visible(False)
            self.remove_highlight_queue()
            if hasattr(self, "_queue_animation_started"):
                del self._queue_animation_started
            if not self.error:
                self.ui_queue_stack.set_visible_child_name("completed")

        if self.error:
            self.bottomrevealer.set_reveal_child(True)
            self.bottomstack.set_visible_child_name("error")
            self.bottomerrorlabel.set_markup("<span color='red'>{}</span>".format(self.errormessage))

        if status == 256:
            self.errormessage = _("Only one software management tool is allowed to run at the same time.\n"
                                  "Please close the other application e.g. 'Update Manager', 'aptitude' or 'Synaptic' first.")
            self.bottomrevealer.set_reveal_child(True)
            self.bottomstack.set_visible_child_name("error")
            self.bottomerrorlabel.set_markup("<span color='red'>{}</span>".format(self.errormessage))
            if self.dpkglockerror:
                self.bottomerrordetails_button.set_visible(True)
                self.bottomerrordetails_label.set_markup(
                    "<b>{}</b>".format(GLib.markup_escape_text(self.dpkglockerror_message, -1)))

            elif self.Package.control_dpkg_interrupt():
                self.bottomstack.set_visible_child_name("interrupt")
                self.bottominterruptlabel.set_markup("<span color='red'><b>{}</b></span>".format(
                    _("dpkg interrupt detected. Click the 'Fix' button or\n"
                      "manually run 'sudo dpkg --configure -a' to fix the problem.")
                ))

        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.error_message = ""
        self.dpkglockerror_message = ""

    def apt_update_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_apt_update_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_apt_update_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_apt_update_process_exit)
        return pid

    def on_apt_update_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def on_apt_update_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def on_apt_update_process_exit(self, pid, status):
        self.Package.updatecache()
        GLib.idle_add(self.ui_header_aptupdate_spinner.stop)
        GLib.idle_add(self.ui_header_aptupdate_spinner.set_visible, False)
        if status == 0:
            try:
                timestamp = int(datetime.now().timestamp())
            except Exception as e:
                self.Logger.warning("timestamp Error: {}")
                self.Logger.exception("{}".format(e))
                timestamp = 0

            self.UserSettings.write_config(LastAutoAptUpdate=timestamp)

            old_upgradables = self.upgradables.copy()
            self.get_upgradables()
            if old_upgradables != self.upgradables:
                self.set_upgradables()

            self.auto_apt_update_finished = True

    def group_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_group_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_group_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_group_process_exit)
        return pid

    def on_group_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("on_group_process_stdout - line: {}".format(line))
        return True

    def on_group_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("on_group_process_stderr - line: {}".format(line))
        self.grouperrormessage = line
        return True

    def on_group_process_exit(self, pid, status):
        self.Logger.info("on_group_process_exit - status: {}".format(status))
        self.control_groups()
        if status != 0:
            self.ui_settings_password_info_label.set_markup(
                "<small><span color='red' weight='light'>{}</span></small>".format(self.grouperrormessage))
        else:
            self.ui_settings_password_info_label.set_text("")

    def tryfix_vte_process(self, command):
        if self.tryfix_vteterm:
            self.tryfix_vteterm.get_parent().remove(self.tryfix_vteterm)

        self.tryfix_vteterm = Vte.Terminal()
        self.update_vte_color(self.tryfix_vteterm)
        self.tryfix_vteterm.set_scrollback_lines(-1)
        tryfix_vte_menu = Gtk.Menu()
        tryfix_vte_menu_items = Gtk.MenuItem(label=_("Copy selected text"))
        tryfix_vte_menu.append(tryfix_vte_menu_items)
        tryfix_vte_menu_items.connect("activate", self.on_tryfix_vte_menu_action, self.tryfix_vteterm)
        tryfix_vte_menu_items.show()
        self.tryfix_vteterm.connect_object("event", self.on_tryfix_vte_event, tryfix_vte_menu)
        self.ui_tryfix_vte_sw.add(self.tryfix_vteterm)
        self.tryfix_vteterm.show_all()

        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        self.tryfix_vteterm.set_pty(pty)
        try:
            self.tryfix_vteterm.spawn_async(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
                -1,
                None,
                self.on_tryfix_vte_create_spawn_callback,
                None
            )
        except Exception as e:
            self.Logger.exception("{}".format(e))
            self.tryfix_vteterm.connect("child-exited", self.on_tryfix_vte_process_done)
            self.tryfix_vteterm.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
            )

    def on_tryfix_vte_menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def on_tryfix_vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def on_tryfix_vte_create_spawn_callback(self, terminal, pid, error, userdata):
        self.tryfix_vteterm.connect("child-exited", self.on_tryfix_vte_process_done)

    def on_tryfix_vte_process_done(self, obj, status):
        self.Logger.info("on_tryfix_vte_process_done: status: {}".format(status))
        self.ui_tryfix_spinner.stop()
        self.ui_tryfix_button.set_sensitive(True)
        if status == 0:
            self.Package = Package()
            if self.Package.updatecache():
                self.ui_tryfix_stack.set_visible_child_name("done")
                self.isbroken = False
                self.Package.getApps()
            else:
                self.ui_tryfix_stack.set_visible_child_name("error")
                self.isbroken = True
                self.Logger.warning("on_tryfix_vte_process_done: Error while updating Cache")

    def dpkgconfigure_vte_start_process(self, command):
        if self.dpkgconfigure_vteterm:
            self.dpkgconfigure_vteterm.get_parent().remove(self.dpkgconfigure_vteterm)

        self.dpkgconfigure_vteterm = Vte.Terminal()
        self.dpkgconfigure_vteterm.set_scrollback_lines(-1)
        dpkgconfigure_vte_menu = Gtk.Menu()
        dpkgconfigure_vte_menu_items = Gtk.MenuItem(label=_("Copy selected text"))
        dpkgconfigure_vte_menu.append(dpkgconfigure_vte_menu_items)
        dpkgconfigure_vte_menu_items.connect("activate", self.dpkgconfigure_vte_menu_action, self.dpkgconfigure_vteterm)
        dpkgconfigure_vte_menu_items.show()
        self.dpkgconfigure_vteterm.connect_object("event", self.dpkgconfigure_vte_event, dpkgconfigure_vte_menu)
        self.interrupt_vte_box.add(self.dpkgconfigure_vteterm)
        self.dpkgconfigure_vteterm.show_all()

        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        self.dpkgconfigure_vteterm.set_pty(pty)
        try:
            self.dpkgconfigure_vteterm.spawn_async(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
                -1,
                None,
                self.dpkgconfigure_vte_create_spawn_callback,
                None
            )
        except Exception as e:
            self.Logger.exception("{}".format(e))
            self.dpkgconfigure_vteterm.connect("child-exited", self.dpkgconfigure_vte_on_done)
            self.dpkgconfigure_vteterm.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
            )

    def dpkgconfigure_vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def dpkgconfigure_vte_menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def dpkgconfigure_vte_create_spawn_callback(self, terminal, pid, error, userdata):
        self.dpkgconfigure_vteterm.connect("child-exited", self.dpkgconfigure_vte_on_done)

    def dpkgconfigure_vte_on_done(self, terminal, status):
        self.Logger.info("dpkgconfigure_vte_on_done status: {}".format(status))

        self.dpkgconfiguring = False
        self.bottominterrupt_fix_button.set_sensitive(True)
        self.bottominterrupthide_button.set_sensitive(True)
        self.pop_interruptinfo_spinner.set_visible(False)
        self.pop_interruptinfo_spinner.stop()

        if status == 32256:
            self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("Error.")))
        else:
            self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("Process completed.")))
            self.pop_interruptinfo_ok_button.set_visible(True)
