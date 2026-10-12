import os
import re
import html
import threading
import platform
import gettext
from datetime import datetime, timezone

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango, GdkPixbuf, GObject

from ODRSClient import ODRSClient

_ = gettext.gettext


class DetailMixin:
    """Uygulama detay sayfası, izin rozetleri, yorumlar ve değerlendirmeler kontrolcü mixin'i."""

    def set_rating_stars(self, average):
        sub_point = int("{:.1f}".format(average).split(".")[1])
        avg = int(average)

        def get_star_subname(fraction):
            if fraction >= 5:
                return "ps-rating-star-half"
            else:
                return "ps-rating-star-empty"

        if avg == 0:
            self.ui_ad_rating_star1_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 1:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 2:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 3:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 4:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 5:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)

    def set_rating_progressbar(self, total_count, count_1, count_2, count_3, count_4, count_5):
        self.ui_rating_count1_label.set_text("{}".format(count_1))
        self.ui_rating_count2_label.set_text("{}".format(count_2))
        self.ui_rating_count3_label.set_text("{}".format(count_3))
        self.ui_rating_count4_label.set_text("{}".format(count_4))
        self.ui_rating_count5_label.set_text("{}".format(count_5))
        if total_count != 0:
            self.ui_rating_prg1_progressbar.set_fraction(count_1 / total_count)
            self.ui_rating_prg2_progressbar.set_fraction(count_2 / total_count)
            self.ui_rating_prg3_progressbar.set_fraction(count_3 / total_count)
            self.ui_rating_prg4_progressbar.set_fraction(count_4 / total_count)
            self.ui_rating_prg5_progressbar.set_fraction(count_5 / total_count)
        else:
            self.ui_rating_prg1_progressbar.set_fraction(0)
            self.ui_rating_prg2_progressbar.set_fraction(0)
            self.ui_rating_prg3_progressbar.set_fraction(0)
            self.ui_rating_prg4_progressbar.set_fraction(0)
            self.ui_rating_prg5_progressbar.set_fraction(0)

    def set_comment_stars(self, point):
        self.comment_star_point = point
        if point == 0:
            self.ui_comment_star1_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star2_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            self.ui_comment_star1_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 1 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star2_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 2 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star3_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 3 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star4_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 4 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star5_image.set_from_icon_name(
                "ps-rating-star-full" if point == 5 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)

    def set_comment_own_stars(self, point):
        if point == 0:
            self.ui_comment_own_star1_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star2_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            self.ui_comment_own_star1_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 1 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star2_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 2 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star3_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 3 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star4_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 4 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star5_image.set_from_icon_name(
                "ps-rating-star-full" if point == 5 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)

    def clear_app_details(self):
        self.ui_ad_name.set_text("")
        self.ui_ad_subcategory_label.set_text("")
        self.ui_ad_top_category_label.set_text("")

        self.ui_ad_top_avgrate_label.set_text("")
        self.ui_ad_top_size_label.set_text("")
        self.ui_ad_top_depends_count_label.set_text("")
        self.ui_ad_description_label.set_text("")
        self.ui_ad_version_label.set_text("")
        self.ui_ad_size_label.set_text("")
        self.ui_ad_required_size_label.set_text("")
        self.ui_ad_type_label.set_text("")
        self.ui_ad_category_label.set_text("")
        self.ui_ad_license_label.set_text("")
        self.ui_ad_component_label.set_text("")
        self.ui_ad_maintainer_name_label.set_text("")
        self.ui_ad_maintainer_web_label.set_text("")
        self.ui_ad_maintainer_mail_label.set_text("")

        self.ui_ad_description_more_button.set_visible(False)

        self.ui_ad_important_label.set_text("")
        self.ui_ad_important_label.set_tooltip_text("")
        self.ui_ad_important_label.set_visible(False)

        self.ui_ad_remove_button.set_visible(False)
        self.ui_ad_disclaimer_button.set_visible(False)

        self.ui_ad_remove_list_box.set_visible(False)
        self.ui_ad_install_list_box.set_visible(False)
        self.ui_ad_broken_list_box.set_visible(False)

        self.ui_ad_more_comment_button.set_visible(False)

        self.ui_ad_bottom_avgrate_label.set_text("")
        self.ui_ad_bottom_rate_count_label.set_text("")

        self.set_rating_stars(0)
        self.set_rating_progressbar(0, 0, 0, 0, 0, 0)

        for row in self.ui_ad_image_box:
            self.ui_ad_image_box.remove(row)

        for row in self.ui_ad_comments_flowbox:
            self.ui_ad_comments_flowbox.remove(row)

        self.ui_ad_more_comment_button.name = "store"

        self.set_comment_stars(0)
        self.ui_comment_fullname_entry.set_text("")
        start, end = self.ui_comment_content_textbuffer.get_bounds()
        self.ui_comment_content_textbuffer.delete(start, end)
        self.ui_comment_error_label.set_text("")
        self.ui_comment_error_label.set_visible(False)
        self.ui_comment_send_button.set_sensitive(False)
        self.ui_comment_main_stack.set_visible_child_name("main")

        self.ui_comment_own = {}

        self.image_stack_names = []
        self.image_stack_current_index = 0
        self.image_original_pixbufs = {}
        for image in self.ui_image_stack:
            self.ui_image_stack.remove(image)

        for child in self.ui_ad_available_repos_box.get_children():
            self.ui_ad_available_repos_box.remove(child)

    def _load_flathub_appstream_async(self, app_name, details):
        flathub_client = getattr(self.Server, "flathub", None) or getattr(self.Server, "flathub_client", None)
        if not flathub_client:
            return

        def _fetch():
            stream = flathub_client.get_appstream(app_name)
            if not stream:
                return

            screenshots = []
            for s in stream.get("screenshots", []):
                sizes = s.get("sizes", [])
                if sizes:
                    chosen = None
                    for sz in sizes:
                        src = sz.get("src", "")
                        if "752" in src or "624" in src or "orig" in src:
                            chosen = src
                            break
                    if not chosen:
                        chosen = sizes[-1].get("src") or sizes[0].get("src")
                    if chosen:
                        screenshots.append(chosen)

            def _apply():
                if getattr(self, "ui_app_name", None) != app_name:
                    return False
                details["screenshots"] = screenshots
                if stream.get("developer_name"):
                    details["maintainer"] = [{
                        "name": stream.get("developer_name"),
                        "mail": "",
                        "website": stream.get("urls", {}).get("homepage", "")
                    }]
                    m_name = stream.get("developer_name")
                    m_web = stream.get("urls", {}).get("homepage", "")
                    self.ui_ad_maintainer_name_label.set_markup(GLib.markup_escape_text(m_name, -1) if m_name else "")
                    self.ui_ad_maintainer_web_label.set_markup(
                        f"<a title='{m_web}' href='{m_web}'>{m_web}</a>" if m_web else ""
                    )
                if stream.get("description"):
                    details["description"] = {"tr": stream.get("description"), "en": stream.get("description")}
                    self.set_ad_description_text(stream.get("description"))
                if stream.get("project_license"):
                    details["license"] = stream.get("project_license")
                    self.ui_ad_license_label.set_text(stream.get("project_license"))

                for image in screenshots:
                    img_uri = image if str(image).startswith("http") else (self.Server.serverurl + image)
                    self.AppImage.get_image(img_uri, app_name)
                return False

            GLib.idle_add(_apply)

        threading.Thread(target=_fetch, daemon=True).start()

    def set_app_details_page(self, app, source=1):
        """
        :param app: package name of application
        :param source: 1:store_app, 2:repo_app, 0:external_app
        """
        self.ui_app_name = ""
        self.ui_myapp_name_dic = ""

        if isinstance(app, dict):
            app_name, details = next(iter(app.items()))
        elif isinstance(app, str):
            app_name = app
            details = self.apps_full.get(app_name, {})
        else:
            self.Logger.warning("{} {} {}".format("set_app_details_page func ERROR for: ", app, source))
            return

        if not details:
            self.Logger.warning("{} details not found.".format(app_name))
            return

        self.Logger.info("app_name: {}".format(app_name))
        self.Logger.info("details: {}".format(details))

        self.ui_app_name = app_name

        self.clear_app_details()

        self.ui_ad_image_scrolledwindow.set_visible(source == 1)
        self.ui_ad_ratings_box.set_visible(source == 1)
        self.ui_ad_about_box.set_visible(source == 1 or source == 2)
        self.ui_ad_details_box.set_visible(source == 1 or source == 2)
        self.ui_ad_dependencies_box.set_visible(source == 1 or source == 2)
        self.ui_ad_availablerepos_box.set_visible(source == 1)
        self.ui_ad_top_stack.set_visible_child_name("stats" if source == 1 else "limited" if source == 2 else "external")
        self.ui_ad_action_stack.set_visible_child_name("action" if source == 1 or source == 2 else "external")

        self.ui_appdetails_scrolledwindow.set_vadjustment(Gtk.Adjustment())
        self.ui_right_stack_navigate_to("appdetails")

        # store app operations
        if source == 1:
            if getattr(self.Server, "is_flathub", False):
                if not details.get("screenshots"):
                    self._load_flathub_appstream_async(app_name, details)
                else:
                    for image in details.get("screenshots", []):
                        img_uri = image if str(image).startswith("http") else (self.Server.serverurl + image)
                        self.AppImage.get_image(img_uri, app_name)

            if not getattr(self.Server, "is_flathub", False):
                self.AppDetail.get_details(self.Server.serverurl + self.Server.serverdetails, {"mac": self.mac, "app": app_name})
                self.comment_limit = 10
                self.gnome_comment_limit = 10

            app_pretty_name = details.get("prettyname", {}).get(self.user_locale) or details.get("prettyname", {}).get("en", "{}".format(app_name.title()))
            app_category_name = ((details.get("category") or [{}])[0].get(self.user_locale, "") or "").title()
            app_subcategory_name = (details.get("subcategory") or [{}])[0].get(self.user_locale) or (details.get("subcategory") or [{}])[0].get("en") or ""

            self.ui_ad_name.set_text("{}".format(app_pretty_name))
            self.ui_ad_top_category_label.set_text("{}".format(app_category_name))
            self.ui_ad_subcategory_label.set_text("{}".format(app_subcategory_name))

            if details.get("icon") and os.path.exists(str(details.get("icon"))):
                self.ui_ad_icon.set_from_file(details["icon"])
            else:
                self.ui_ad_icon.set_from_icon_name(app_name, Gtk.IconSize.DIALOG)
            self.ui_ad_icon.set_pixel_size(68)

            self.set_ad_description_text(
                details.get("description", {}).get(self.user_locale)
                or details.get("description", {}).get("en")
                or ""
            )

            app_version = self.Package.installed_version(app_name)
            self.ui_ad_version_label.set_text("{}".format(app_version))

            maintainer_info = (details.get("maintainer") or [{}])[0]
            m_name = maintainer_info.get("name", "")
            m_mail = maintainer_info.get("mail", "")
            m_web = maintainer_info.get("website", "")
            self.ui_ad_maintainer_name_label.set_markup(GLib.markup_escape_text(m_name, -1) if m_name else "")
            self.ui_ad_maintainer_mail_label.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                GLib.markup_escape_text(m_mail, -1),
                GLib.markup_escape_text(m_mail, -1),
                GLib.markup_escape_text(m_mail, -1)) if m_mail else "")

            self.ui_ad_maintainer_web_label.set_markup("<a title='{}' href='{}'>{}</a>".format(
                GLib.markup_escape_text(m_web, -1),
                GLib.markup_escape_text(m_web, -1),
                GLib.markup_escape_text(m_web, -1)) if m_web else "")

            self.ui_ad_category_label.set_text(app_category_name)
            self.ui_ad_license_label.set_text(details.get("license") or "")
            self.display_app_sandbox_permissions(app_name)
            self.display_app_architecture_badges(app_name)
            self.load_odrs_ratings_and_reviews(app_name)

            codenames = [c.get("name") for c in (details.get("codename") or [])]
            for codename in codenames:
                label = Gtk.Label.new()
                label.set_markup("<b>{}</b>".format(codename.title()))
                label.get_style_context().add_class("parslinux-software-codename-label")
                label.set_alignment(0.5, 0.5)
                label.set_margin_left(4)
                label.set_margin_right(4)
                label.set_margin_top(4)
                label.set_margin_bottom(4)
                self.ui_ad_available_repos_box.pack_start(label, False, False, 0)
            self.ui_ad_available_repos_box.show_all()

            self.ui_comment_appname_label.set_markup("<b>{}</b>".format(app_pretty_name))
            self.ui_comment_subcategory_label.set_markup("{}".format(app_subcategory_name))
            self.ui_comment_icon_image.set_from_icon_name(app_name, Gtk.IconSize.DIALOG)
            self.ui_comment_icon_image.set_pixel_size(48)
            self.ui_comment_version_label.set_text("{}".format(app_version))
            self.ui_comment_fullname_entry.set_text("{}".format(self.UserSettings.user_real_name))

        # store app and repo app operations
        if source == 1 or source == 2:
            self.ui_ad_action_button.remove(self.ui_ad_action_button.get_children()[0])
            action_button_label = Gtk.Label.new()
            action_button_label.set_line_wrap(False)
            action_button_label.set_justify(Gtk.Justification.LEFT)
            action_button_label.set_ellipsize(Pango.EllipsizeMode.END)
            self.ui_ad_action_button.add(action_button_label)
            is_installed = self.Package.isinstalled(app_name)
            is_upgradable = self.Package.is_upgradable(app_name)
            if source == 1:
                is_openable = self.get_desktop_filename_from_app_name(app_name) != ""
            else:
                is_openable = details.get("id", False)
            if is_installed is not None:
                command = self.get_action_command(app_name, details)
                threading.Thread(target=self.app_detail_requireds_thread, args=(command,), daemon=True).start()
                if is_installed:
                    self.ui_ad_remove_button.set_visible(True)
                    self.ui_ad_remove_button.set_sensitive(True)
                    if is_upgradable:
                        self.set_button_class(self.ui_ad_action_button, 3)
                        action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                        self.ui_ad_action_button.name = 2
                    else:
                        if is_openable:
                            self.set_button_class(self.ui_ad_action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            self.ui_ad_action_button.name = 3
                        else:
                            self.set_button_class(self.ui_ad_action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            self.ui_ad_action_button.name = 9
                else:
                    self.set_button_class(self.ui_ad_action_button, 0)
                    action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                    self.ui_ad_action_button.name = 1
            else:
                self.set_button_class(self.ui_ad_action_button, 2)
                action_button_label.set_markup("<small>{}</small>".format(_("Not Found")))
                self.ui_ad_important_label.set_text(_("This app is not available in the repos of your version."))
                self.ui_ad_important_label.set_tooltip_text("")
                self.ui_ad_important_label.set_visible(True)
                self.ui_ad_sizetitle_label.set_text(_("Download Size"))
                self.ui_ad_required_sizetitle_label.set_text(_("Required Disk Space"))
                self.ui_ad_size_label.set_text("{}".format(_("None")))
                self.ui_ad_required_size_label.set_text("{}".format(_("None")))
                self.ui_ad_top_size_label.set_text("{}".format(_("None")))
            self.ui_ad_action_button.show_all()

            self.ui_ad_remove_button.name = 0

            app_in_queue = next((q for q in self.queue if q["name"] == app_name), None)
            if app_in_queue:
                if is_installed:
                    if is_upgradable and app_in_queue["upgrade"]:
                        self.ui_ad_action_button.set_label(_("Upgrading"))
                    else:
                        self.ui_ad_action_button.set_label(_("Removing"))
                else:
                    self.ui_ad_action_button.set_label(_("Installing"))
                self.ui_ad_action_button.set_sensitive(False)
                if self.ui_ad_remove_button.get_visible():
                    self.ui_ad_remove_button.set_sensitive(False)

            origin_info = self.Package.origins(app_name)
            component = getattr(origin_info, "component", "")
            origin = getattr(origin_info, "origin", "")
            if component == "non-free" or (details.get("component") or {}).get("name", "") == "non-free":
                self.ui_ad_disclaimer_button.set_visible(True)
                type_label = _("Non-Free")
            else:
                self.ui_ad_disclaimer_button.set_visible(False)
                type_label = _("Open Source")
            self.ui_ad_component_label.set_markup(f"{origin} {component}" if origin_info else _("None"))
            self.ui_ad_type_label.set_markup(type_label)

        # repo app and external app operations
        if source == 2 or source == 0:
            self.ui_ad_name.set_text(details["name"])
            try:
                if os.path.isfile(details["icon_name"]):
                    px = GdkPixbuf.Pixbuf.new_from_file_at_size(details["icon_name"], 68, 68)
                    self.ui_ad_icon.set_from_pixbuf(px)
                else:
                    self.ui_ad_icon.set_from_icon_name(details["icon_name"], Gtk.IconSize.DIALOG)
            except Exception as e:
                self.ui_ad_icon.set_from_icon_name("image-missing-symbolic", Gtk.IconSize.DIALOG)
            self.ui_ad_icon.set_pixel_size(68)

        # repo app operations
        if source == 2:
            self.ui_myapp_name_dic = {app_name: details}

            maintainer_name = ""
            maintainer_mail = ""
            maintainer_web = ""
            app_section = ""
            app_version = ""
            app_license = ""
            record = self.Package.get_record(app_name)
            if record:
                app_section = record.get("Section", "")
                app_version = record.get("Version", "")
                maintainer = record.get("Maintainer", "")
                maintainer_web = record.get("Homepage", "")
                app_license = record.get("License", "")
                try:
                    match = re.match(r"^(.*?)(?:\s*<([^>]+)>)?$", maintainer)
                    if match:
                        maintainer_name = (match.group(1) or "").strip()
                        maintainer_mail = (match.group(2) or "").strip()
                except Exception as e:
                    self.Logger.exception("{}".format(e))

            self.ui_ad_maintainer_name_label.set_markup(maintainer_name)
            self.ui_ad_maintainer_mail_label.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                GLib.markup_escape_text(maintainer_mail, -1),
                GLib.markup_escape_text(maintainer_mail, -1),
                GLib.markup_escape_text(maintainer_mail, -1)) if maintainer_mail else "-")

            self.ui_ad_maintainer_web_label.set_markup("<a title='{}' href='{}'>{}</a>".format(
                GLib.markup_escape_text(maintainer_web, -1),
                GLib.markup_escape_text(maintainer_web, -1),
                GLib.markup_escape_text(maintainer_web, -1)) if maintainer_web else "-")

            self.ui_ad_top_category_label.set_text("{}".format(app_section))
            self.ui_ad_subcategory_label.set_text("{}".format(app_name))
            self.ui_ad_version_label.set_text("{}".format(app_version))
            self.ui_ad_category_label.set_text("{}".format(app_section if app_section else "-"))

            self.set_ad_description_text(details["description"])

            if not app_license:
                app_license = self.Package.get_license_from_file(app_name)
            self.ui_ad_license_label.set_text("{}".format(app_license if app_license else "-"))

    def set_ad_description_text(self, text):
        full_text = text or ""
        if "<" in full_text and ">" in full_text:
            full_text = re.sub(r'<br\s*/?>', '\n', full_text)
            full_text = re.sub(r'</p>', '\n\n', full_text)
            full_text = re.sub(r'</li>', '\n', full_text)
            full_text = re.sub(r'<li[^>]*>', '• ', full_text)
            full_text = re.sub(r'<[^>]+>', '', full_text)
            full_text = html.unescape(full_text)
        full_text = full_text.strip()
        MAX_CHARS = 300
        MAX_LINES = 5
        line_count = full_text.count("\n")
        needs_read_more = len(full_text) > MAX_CHARS or line_count > MAX_LINES
        if needs_read_more:
            short_text = full_text
            if len(short_text) > MAX_CHARS:
                short_text = short_text[:MAX_CHARS]
            if line_count > MAX_LINES:
                lines = short_text.split("\n")
                short_text = "\n".join(lines[:MAX_LINES])
            self.ui_ad_description_more_button.set_visible(True)
            self.ui_ad_description_label.set_text(short_text)
        else:
            self.ui_ad_description_more_button.set_visible(False)
            self.ui_ad_description_label.set_text(full_text)
        self.ad_full_description_text = full_text

    def display_app_sandbox_permissions(self, app_name):
        if not hasattr(self, "ui_ad_permissions_box"):
            self.ui_ad_permissions_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
            self.ui_ad_permissions_box.set_margin_top(12)
            self.ui_ad_permissions_box.set_margin_bottom(12)
            self.ui_ad_details_box.pack_start(self.ui_ad_permissions_box, False, False, 0)

        self.ui_ad_permissions_box.foreach(self.ui_ad_permissions_box.remove)

        if not hasattr(self, "FlatpakManager") or not self.FlatpakManager.is_available():
            self.ui_ad_permissions_box.set_visible(False)
            return

        def _fetch_and_render():
            perms = self.FlatpakManager.get_permissions(app_name)
            is_installed = self.Package.isinstalled(app_name)
            overrides = self.FlatpakManager.get_permission_overrides(app_name) if is_installed else {}

            def _render():
                self.ui_ad_permissions_box.foreach(self.ui_ad_permissions_box.remove)
                if not perms or not perms.get("items"):
                    self.ui_ad_permissions_box.set_visible(False)
                    return

                self.ui_ad_permissions_box.set_visible(True)
                title = Gtk.Label.new()
                title.set_markup("<b>{}</b>".format(_("Sandbox & Güvenlik İzinleri")))
                title.props.halign = Gtk.Align.START
                self.ui_ad_permissions_box.pack_start(title, False, False, 4)

                flow = Gtk.FlowBox.new()
                flow.set_selection_mode(Gtk.SelectionMode.NONE)
                flow.set_max_children_per_line(3)
                flow.set_column_spacing(10)
                flow.set_row_spacing(8)

                for icon_name, desc in perms["items"]:
                    badge = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
                    badge.get_style_context().add_class("parslinux-software-frame")
                    badge.set_margin_start(4)
                    badge.set_margin_end(4)
                    badge.set_margin_top(2)
                    badge.set_margin_bottom(2)
                    img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
                    lbl = Gtk.Label.new()
                    lbl.set_markup(f"<small>{GLib.markup_escape_text(desc, -1)}</small>")
                    badge.pack_start(img, False, False, 4)
                    badge.pack_start(lbl, False, False, 4)
                    flow.insert(badge, -1)

                self.ui_ad_permissions_box.pack_start(flow, False, False, 0)

                # Interactive Permission Editor (Flatseal-like) for installed apps
                if is_installed and overrides:
                    expander = Gtk.Expander.new(_("İzinleri Düzenle (Flatseal Benzeri)"))
                    expander.set_margin_top(8)

                    edit_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
                    edit_box.set_margin_start(8)
                    edit_box.set_margin_end(8)
                    edit_box.set_margin_top(6)
                    edit_box.set_margin_bottom(6)

                    desc_lbl = Gtk.Label.new()
                    desc_lbl.set_markup("<small><i>{}</i></small>".format(
                        _("Uygulamanın sandbox izinlerini özelleştirin (Geçerli olması için uygulamayı yeniden başlatın):")
                    ))
                    desc_lbl.props.halign = Gtk.Align.START
                    edit_box.pack_start(desc_lbl, False, False, 4)

                    for key, pinfo in overrides.items():
                        row = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
                        row.set_margin_top(2)
                        row.set_margin_bottom(2)

                        icon = Gtk.Image.new_from_icon_name(pinfo["icon"], Gtk.IconSize.BUTTON)
                        lbl = Gtk.Label.new(pinfo["label"])
                        lbl.props.halign = Gtk.Align.START

                        switch = Gtk.Switch.new()
                        switch.set_active(pinfo["effective"])
                        switch.props.valign = Gtk.Align.CENTER

                        def _make_handler(k):
                            def _on_state_set(sw, state):
                                self.FlatpakManager.set_permission_override(app_name, k, state)
                                self.Logger.info(f"Permission {k} overridden to {state} for {app_name}")
                                GLib.idle_add(lambda: self.display_app_sandbox_permissions(app_name))
                                return False
                            return _on_state_set

                        switch.connect("state-set", _make_handler(key))

                        row.pack_start(icon, False, False, 4)
                        row.pack_start(lbl, False, False, 4)

                        if pinfo.get("overridden"):
                            tag = Gtk.Label.new()
                            tag.set_markup("<span foreground='#3498db'><small><b>(Özelleştirildi)</b></small></span>")
                            row.pack_start(tag, False, False, 6)

                        row.pack_end(switch, False, False, 4)
                        edit_box.pack_start(row, False, False, 2)

                    # Reset to defaults button
                    btn_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
                    btn_box.set_margin_top(6)
                    reset_btn = Gtk.Button.new_with_label(_("Varsayılan İzinlere Sıfırla"))
                    reset_btn.get_style_context().add_class("parslinux-software-button-warn")

                    def _on_reset(btn):
                        self.FlatpakManager.reset_permissions(app_name)
                        GLib.idle_add(lambda: self.display_app_sandbox_permissions(app_name))

                    reset_btn.connect("clicked", _on_reset)
                    btn_box.pack_start(reset_btn, False, False, 0)
                    edit_box.pack_start(btn_box, False, False, 4)

                    expander.add(edit_box)
                    self.ui_ad_permissions_box.pack_start(expander, False, False, 4)

                self.ui_ad_permissions_box.show_all()

            GLib.idle_add(_render)

        threading.Thread(target=_fetch_and_render, daemon=True).start()

    def display_app_architecture_badges(self, app_name):
        if not hasattr(self, "ui_ad_arches_box"):
            self.ui_ad_arches_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
            self.ui_ad_arches_box.set_margin_top(6)
            self.ui_ad_arches_box.set_margin_bottom(8)
            self.ui_ad_details_box.pack_start(self.ui_ad_arches_box, False, False, 0)

        self.ui_ad_arches_box.foreach(self.ui_ad_arches_box.remove)
        self.ui_ad_arches_box.set_visible(False)

        def _fetch_arches():
            flathub_client = getattr(self, "FlathubClient", None) or (
                getattr(self.Server, "FlathubClient", None) if hasattr(self, "Server") else None
            )
            if not flathub_client:
                return

            summary = flathub_client.get_app_summary(app_name)
            arches = summary.get("arches") or ["x86_64"]

            def _render():
                self.ui_ad_arches_box.foreach(self.ui_ad_arches_box.remove)
                self.ui_ad_arches_box.set_visible(True)

                title = Gtk.Label.new()
                title.set_markup("<b>{}</b>".format(_("Desteklenen Mimariler:")))
                self.ui_ad_arches_box.pack_start(title, False, False, 4)

                host_machine = platform.machine()
                arch_labels = {
                    "x86_64": "x86_64 (64-bit PC)",
                    "aarch64": "aarch64 (ARM 64)",
                    "riscv64": "riscv64 (RISC-V)",
                    "arm": "arm (32-bit)",
                }

                for arch in arches:
                    badge = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
                    badge.get_style_context().add_class("parslinux-software-frame")
                    lbl = Gtk.Label.new()
                    disp = arch_labels.get(arch, arch)
                    if arch == host_machine:
                        lbl.set_markup(f"<small><b>✓ {disp}</b></small>")
                    else:
                        lbl.set_markup(f"<small>{disp}</small>")
                    badge.pack_start(lbl, False, False, 6)
                    self.ui_ad_arches_box.pack_start(badge, False, False, 2)

                if host_machine in arches:
                    compat = Gtk.Label.new()
                    compat.set_markup("<span foreground='#2ecc71'><small><b>✓ Donanımınızla Tam Uyumlu</b></small></span>")
                    compat.set_margin_start(8)
                    self.ui_ad_arches_box.pack_start(compat, False, False, 0)

                self.ui_ad_arches_box.show_all()

            GLib.idle_add(_render)

        threading.Thread(target=_fetch_arches, daemon=True).start()

    def load_odrs_ratings_and_reviews(self, app_name):
        if not hasattr(self, "ODRSClient") or self.ODRSClient is None:
            self.ODRSClient = ODRSClient()

        def _on_feedback(ratings, reviews):
            if ratings and ratings.get("status"):
                avg = ratings.get("average", 0.0)
                count = ratings.get("count", 0)
                self.set_rating_stars(avg)
                self.ui_ad_top_avgrate_label.set_text(f"{avg:.1f}")
                self.ui_ad_bottom_avgrate_label.set_markup(f"<span font='54'><b>{avg:.1f}</b></span>")
                self.ui_ad_bottom_rate_count_label.set_text(_("{} Değerlendirme").format(count))
                self.set_rating_progressbar(
                    count,
                    ratings.get("star1", 0),
                    ratings.get("star2", 0),
                    ratings.get("star3", 0),
                    ratings.get("star4", 0),
                    ratings.get("star5", 0),
                )

            if hasattr(self, "ui_ad_comments_flowbox") and self.ui_ad_comments_flowbox:
                for child in self.ui_ad_comments_flowbox.get_children():
                    self.ui_ad_comments_flowbox.remove(child)

                if reviews:
                    for rev in reviews[:15]:
                        widget = self.create_comment_widget(rev, gnome=True)
                        self.ui_ad_comments_flowbox.insert(widget, -1)
                else:
                    empty_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
                    empty_box.set_margin_top(16)
                    empty_box.set_margin_bottom(16)
                    empty_lbl = Gtk.Label.new()
                    empty_lbl.set_markup(f"<span color='gray'>{_('Bu uygulama için henüz kullanıcı değerlendirmesi bulunmuyor.')}</span>")
                    empty_box.pack_start(empty_lbl, False, False, 0)
                    row = Gtk.ListBoxRow()
                    row.add(empty_box)
                    self.ui_ad_comments_flowbox.insert(row, -1)

                self.ui_ad_comments_flowbox.show_all()

        self.ODRSClient.fetch_feedback_async(app_name, _on_feedback, user_locale=getattr(self, "user_locale", "tr"))


        threading.Thread(target=_fetch_and_render, daemon=True).start()

    def app_detail_requireds_thread(self, app):
        app_detail_requireds = self.app_detail_requireds_worker(app)
        GLib.idle_add(self.app_detail_requireds_worker_done, app_detail_requireds)

    def app_detail_requireds_worker(self, app=None):
        return self.Package.required_changes(app)

    def app_detail_requireds_worker_done(self, adr):
        self.Logger.info("app_detail_requireds_worker_done")

        is_installed = self.Package.isinstalled(self.ui_app_name)
        if is_installed is not None:
            if is_installed:
                GLib.idle_add(self.ui_ad_sizetitle_label.set_text, _("Package Size"))
                GLib.idle_add(self.ui_ad_required_sizetitle_label.set_text, _("Installed Size"))
                GLib.idle_add(self.ui_ad_size_label.set_text, "{}".format(
                    self.Package.beauty_size(self.Package.get_size(self.ui_app_name))))
                GLib.idle_add(self.ui_ad_required_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["freed_size"])))
                GLib.idle_add(self.ui_ad_top_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["freed_size"])))
            else:
                GLib.idle_add(self.ui_ad_sizetitle_label.set_text, _("Download Size"))
                GLib.idle_add(self.ui_ad_required_sizetitle_label.set_text, _("Required Disk Space"))
                GLib.idle_add(self.ui_ad_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["download_size"])))
                GLib.idle_add(self.ui_ad_required_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["install_size"])))
                GLib.idle_add(self.ui_ad_top_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["install_size"])))

        if adr["to_delete"]:
            self.ui_ad_remove_list_label.set_text("{}".format(", ".join(adr["to_delete"])))
            self.ui_ad_remove_list_count_label.set_text("({})".format(len(adr["to_delete"])))
            self.ui_ad_remove_list_box.set_visible(True)
            self.ui_ad_top_depends_count_label.set_text("{}".format(len(adr["to_delete"])))

            importants = [i for i in self.important_packages if i in adr["to_delete"]]
            self.ui_ad_important_label.set_text(_("Important Package"))
            self.ui_ad_important_label.set_tooltip_text(_("Removing this package could impact system stability."))
            self.ui_ad_important_label.set_visible(importants)
        else:
            self.ui_ad_remove_list_box.set_visible(False)

        if adr["to_install"]:
            self.ui_ad_install_list_label.set_text("{}".format(", ".join(adr["to_install"])))
            self.ui_ad_install_list_count_label.set_text("({})".format(len(adr["to_install"])))
            self.ui_ad_install_list_box.set_visible(True)
            self.ui_ad_top_depends_count_label.set_text("{}".format(len(adr["to_install"])))
        else:
            self.ui_ad_install_list_box.set_visible(False)

        if adr["broken"]:
            self.ui_ad_broken_list_label.set_text("{}".format(", ".join(adr["broken"])))
            self.ui_ad_broken_list_count_label.set_text("({})".format(len(adr["broken"])))
            self.ui_ad_broken_list_box.set_visible(True)
        else:
            self.ui_ad_broken_list_box.set_visible(False)

        return False

    def on_ui_ad_install_list_eventbox_button_press_event(self, widget, event):
        state = not self.ui_ad_install_list_revealer.get_reveal_child()
        self.ui_ad_install_list_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_ad_install_list_image.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def on_ui_ad_remove_list_eventbox_button_press_event(self, widget, event):
        state = not self.ui_ad_remove_list_revealer.get_reveal_child()
        self.ui_ad_remove_list_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_ad_remove_list_image.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def on_ui_ad_broken_list_eventbox_button_press_event(self, widget, event):
        state = not self.ui_ad_broken_list_revealer.get_reveal_child()
        self.ui_ad_broken_list_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_ad_broken_list_image.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def format_date_as_ago(self, dt_utc):
        local_tz = datetime.now().astimezone().tzinfo

        try:
            if isinstance(dt_utc, (int, float)):
                dt_utc = datetime.fromtimestamp(dt_utc, tz=timezone.utc)
            elif isinstance(dt_utc, str):
                dt_utc = datetime.fromisoformat(dt_utc)
            else:
                return "{}".format(dt_utc)
        except Exception:
            return "{}".format(dt_utc)

        try:
            dt_local = dt_utc.astimezone(local_tz)
        except Exception:
            return "{}".format(dt_utc)

        now = datetime.now(local_tz)
        diff = now - dt_local
        seconds = diff.total_seconds()

        minutes = seconds / 60
        hours = minutes / 60
        days = hours / 24
        weeks = days / 7
        months = days / 30
        years = days / 365

        if seconds < 60:
            return _("{} seconds ago").format(int(seconds))
        elif minutes < 60:
            return _("{} minutes ago").format(int(minutes))
        elif hours < 24:
            return _("{} hours ago").format(int(hours))
        elif days < 7:
            return _("{} days ago").format(int(days))
        elif weeks < 4:
            return _("{} weeks ago").format(int(weeks))
        elif months < 12:
            return _("{} months ago").format(int(months))
        else:
            return _("{} years ago").format(int(years))

    def format_date_as_full(self, dt_utc):
        local_tz = datetime.now().astimezone().tzinfo

        try:
            if isinstance(dt_utc, (int, float)):
                dt_utc = datetime.fromtimestamp(dt_utc, tz=timezone.utc)
            elif isinstance(dt_utc, str):
                dt_utc = datetime.fromisoformat(dt_utc)
            else:
                return "{}".format(dt_utc)
        except Exception:
            return "{}".format(dt_utc)

        try:
            dt_local = dt_utc.astimezone(local_tz)
        except Exception:
            return "{}".format(dt_utc)

        return dt_local.strftime("%d-%m-%Y %H:%M")

    def rating_response_from_server(self, status, response=None, appname=None):
        if status:
            r_type = response.get("response-type", 0)
            if r_type == 10:
                if appname != self.ui_app_name:
                    return
                self.ui_comment_send_button.set_sensitive(True)
                if response["rating"]["status"]:
                    self.set_rating_stars(response["rating"]["rate"]["average"])
                    self.ui_ad_top_avgrate_label.set_text("{:.1f}".format(float(response["rating"]["rate"]["average"])))
                    self.ui_ad_bottom_avgrate_label.set_markup(
                        "<span font='54'><b>{:.1f}</b></span>".format(float(response["rating"]["rate"]["average"])))
                    self.ui_ad_bottom_rate_count_label.set_text(_("{} Ratings").format(response["rating"]["rate"]["count"]))

                    GLib.idle_add(self.set_rating_progressbar, response["rating"]["rate"]["count"],
                                  response["rating"]["rate"]["rates"]["1"], response["rating"]["rate"]["rates"]["2"],
                                  response["rating"]["rate"]["rates"]["3"], response["rating"]["rate"]["rates"]["4"],
                                  response["rating"]["rate"]["rates"]["5"])

                    self.ui_comment_main_stack.set_visible_child_name("done")
                else:
                    self.ui_comment_error_label.set_visible(True)
                    if response["rating"]["flood"]:
                        self.ui_comment_error_label.set_text(_("Please try again soon"))
                    else:
                        self.ui_comment_error_label.set_text(_("Error"))

            elif r_type == 12:
                self.ui_suggest_send_button.set_sensitive(True)
                if response["suggestapp"]["status"]:
                    self.ui_suggest_main_stack.set_visible_child_name("done")
                    self.clear_suggest_dialog()
                else:
                    self.ui_suggest_error_label.set_visible(True)
                    if response["suggestapp"]["flood"]:
                        self.ui_suggest_error_label.set_text("{}".format(_("Please try again soon")))
                    else:
                        self.ui_suggest_error_label.set_markup("{}".format(_("Error")))
        else:
            self.ui_comment_error_label.set_visible(True)
            self.ui_comment_error_label.set_text(_("Error"))
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(_("Error"))

    def app_details_from_server(self, status, response=None, appname=None):
        self.Logger.info("app_details_from_server, status: {}".format(status))
        self.Logger.info("app_details_from_server, appname: {}".format(appname))
        self.Logger.info("app_details_from_server, response:{}".format(response))

        if status and appname == self.ui_app_name:
            GLib.idle_add(self.ui_ad_top_avgrate_label.set_text,
                          "{:.1f}".format(float(response["details"]["rate"]["average"])))

            GLib.idle_add(self.ui_ad_top_download_label.set_text,
                          "{}".format(response["details"]["download"]["count"]))

            GLib.idle_add(self.ui_ad_bottom_avgrate_label.set_markup,
                          "<span font='54'><b>{:.1f}</b></span>".format(float(response["details"]["rate"]["average"])))

            GLib.idle_add(self.set_rating_stars, response["details"]["rate"]["average"])

            GLib.idle_add(self.ui_ad_bottom_rate_count_label.set_text,
                          "{} Ratings".format(response["details"]["rate"]["count"]))

            GLib.idle_add(self.set_rating_progressbar, response["details"]["rate"]["count"],
                          response["details"]["rate"]["rates"]["1"], response["details"]["rate"]["rates"]["2"],
                          response["details"]["rate"]["rates"]["3"], response["details"]["rate"]["rates"]["4"],
                          response["details"]["rate"]["rates"]["5"])

            self.ui_comment_main_stack.set_visible_child_name("main")
            if response["details"]["rate"]["individual"] == 0:
                self.ui_comment_mid_stack.set_visible_child_name("write")
                self.ui_comment_bottom_stack.set_visible_child_name("disclaimer")
                self.ui_comment_send_button.set_sensitive(True)
                self.ui_comment_own = {}
            else:
                self.ui_comment_mid_stack.set_visible_child_name("read")
                self.ui_comment_bottom_stack.set_visible_child_name("info")

                self.ui_comment_own_date_label.set_text("{}".format(self.format_date_as_ago(
                    response["details"]["individual"]["date"])))
                self.ui_comment_own_date_label.set_tooltip_text(self.format_date_as_full(
                    response["details"]["individual"]["date"]))

                self.ui_comment_own_fullname_label.set_text("{}".format(response["details"]["individual"]["author"]))
                self.ui_comment_own_content_label.set_text("{}".format(response["details"]["individual"]["comment"]))
                self.set_comment_own_stars(response["details"]["individual"]["rate"])

                if response["details"]["individual"]["recommentable"]:
                    self.ui_comment_mid_editable_stack.set_visible_child_name("edit")
                    if response["details"]["individual"]["comment"]:
                        self.ui_comment_info_label.set_text("{}".format(
                            _("Your comment is under review.")))
                    else:
                        self.ui_comment_info_label.set_text("{}".format(
                            _("You can also add a comment if you want.")))
                else:
                    self.ui_comment_mid_editable_stack.set_visible_child_name("read")
                    self.ui_comment_info_label.set_text("{}".format(
                        _("You wrote a review about the application before, thank you.")))

                self.ui_comment_own = {"fullname": response["details"]["individual"]["author"],
                                       "comment": response["details"]["individual"]["comment"],
                                       "point": response["details"]["rate"]["individual"]}

    def parslinux_comments_from_server(self, status, response=None, appname=None):
        self.Logger.info("parslinux_comments_from_server: {} {} {}".format(status, appname, response))
        if status and response and "comments" in response and appname == self.ui_app_name:
            self.ui_ad_more_comment_button.name = "store"

            def remove_store_rows():
                for child in self.ui_ad_comments_flowbox.get_children():
                    inner = child.get_child().get_children()[0]
                    if inner and inner.name == "store":
                        self.ui_ad_comments_flowbox.remove(child)
            GLib.idle_add(remove_store_rows)

            response_comment_len = len(response["comments"])
            GLib.idle_add(self.ui_ad_more_comment_button.set_visible, response_comment_len == self.comment_limit)
            GLib.idle_add(self.ui_ad_more_comment_button.set_sensitive, response_comment_len == self.comment_limit)

            for comment in response["comments"]:
                listbox = self.create_comment_widget(comment)
                GLib.idle_add(self.ui_ad_comments_flowbox.insert, listbox, -1)
            GLib.idle_add(self.ui_ad_comments_flowbox.show_all)

            if response_comment_len != self.comment_limit:
                if self.UserSettings.config_gnome_comments:
                    self.ui_ad_more_comment_button.name = "gnome"
                    gdic = {"user_hash": "0000000000000000000000000000000000000000",
                            "app_id": self.get_gnome_desktop_filename_from_app_name(self.ui_app_name),
                            "locale": self.user_locale, "distro": "Pars Linux", "version": "unknown", "limit": self.gnome_comment_limit}
                    self.GnomeComment.get_comments(self.Server.gnomecommentserver, gdic, self.ui_app_name)

    def gnome_comments_from_server(self, status, response=None, appname=None):
        self.Logger.info("gnome_comments_from_server: {} {} {}".format(status, appname, response))
        if status and response and appname == self.ui_app_name:
            def remove_gnome_rows():
                for child in self.ui_ad_comments_flowbox.get_children():
                    inner = child.get_child().get_children()[0]
                    if inner and inner.name == "gnome":
                        self.ui_ad_comments_flowbox.remove(child)
            GLib.idle_add(remove_gnome_rows)

            response_comment_len = len(response)
            GLib.idle_add(self.ui_ad_more_comment_button.set_visible, response_comment_len == self.gnome_comment_limit)
            GLib.idle_add(self.ui_ad_more_comment_button.set_sensitive, response_comment_len == self.gnome_comment_limit)

            required_keys = ["rating", "user_display", "date_created", "summary", "description", "distro", "version", "review_id"]

            for comment in response:
                if all(key in comment for key in required_keys):
                    if comment["review_id"] not in self.Server.blocked_gnome_reviews:
                        listbox = self.create_comment_widget(comment, True)
                        GLib.idle_add(self.ui_ad_comments_flowbox.insert, listbox, -1)
                    else:
                        self.Logger.info(f"Gnome comment blocked: {comment['review_id']}")
            GLib.idle_add(self.ui_ad_comments_flowbox.show_all)

    def on_ui_ad_more_comment_button_clicked(self, button):
        self.ui_ad_more_comment_button.set_sensitive(False)
        if button.name == "store":
            self.comment_limit = self.comment_limit + 10
        elif button.name == "gnome":
            self.gnome_comment_limit = self.gnome_comment_limit + 10
            gdic = {"user_hash": "0000000000000000000000000000000000000000",
                    "app_id": self.get_gnome_desktop_filename_from_app_name(self.ui_app_name),
                    "locale": self.user_locale, "distro": "Pars Linux", "version": "unknown", "limit": self.gnome_comment_limit}
            self.GnomeComment.get_comments(self.Server.gnomecommentserver, gdic, self.ui_app_name)

    def create_comment_widget(self, comment, gnome=False):
        if not gnome:
            if comment["distro"] is None or comment["distro"] == "":
                comment["distro"] = _("unknown")

            if comment["appversion"] is None or comment["appversion"] == "":
                comment["appversion"] = _("unknown")

            distro = comment["distro"]
            app_version = comment["appversion"]
            author = comment["author"]
            date = comment["date"]
            value = comment["value"]
            comment = comment["comment"]
        else:
            distro = comment["distro"]
            app_version = comment["version"]
            author = comment["user_display"]
            date = comment["date_created"]
            value = comment["rating"] / 20
            comment = "{}\n{}".format(comment["summary"], comment["description"])

        label_author = Gtk.Label.new()
        label_author.set_markup("<b>{}</b>".format(author))
        label_author.set_selectable(True)

        label_date = Gtk.Label.new()
        label_date.set_text("{}".format(self.format_date_as_ago(date)))
        label_date.set_tooltip_text("{}".format(self.format_date_as_full(date)))
        label_date.set_selectable(True)

        star_image_1 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 1 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_2 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 2 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_3 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 3 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_4 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 4 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_5 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 5 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)

        box_star = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box_star.pack_start(star_image_1, False, True, 0)
        box_star.pack_start(star_image_2, False, True, 0)
        box_star.pack_start(star_image_3, False, True, 0)
        box_star.pack_start(star_image_4, False, True, 0)
        box_star.pack_start(star_image_5, False, True, 0)

        box_top = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        box_top.pack_start(box_star, False, True, 0)
        box_top.pack_start(Gtk.Separator.new(Gtk.Orientation.VERTICAL), False, True, 0)
        box_top.pack_start(label_author, False, True, 0)
        box_top.pack_end(label_date, False, True, 0)

        label_comment = Gtk.Label.new()
        label_comment.set_text("{}".format(comment))
        label_comment.set_selectable(True)
        label_comment.set_line_wrap(True)
        label_comment.set_line_wrap_mode(1)
        label_comment.props.halign = Gtk.Align.START
        label_comment.set_xalign = 0.0

        label_distro = Gtk.Label.new()
        label_distro.set_markup("{}".format(distro))
        label_distro.set_selectable(True)

        label_appversion = Gtk.Label.new()
        label_appversion.set_markup("{}: {}".format(_("App"), app_version))
        label_appversion.set_selectable(True)

        box_bottom = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        box_bottom.pack_start(label_distro, False, True, 0)
        box_bottom.pack_start(label_appversion, False, True, 0)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        bottom_separator.get_style_context().add_class("parslinux-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 20)
        box.pack_start(box_top, False, True, 0)
        box.pack_start(label_comment, False, True, 0)
        box.pack_start(box_bottom, False, True, 0)
        box.pack_end(bottom_separator, False, True, 0)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(8)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox_row = Gtk.ListBoxRow()
        listbox_row.name = "store" if not gnome else "gnome"
        listbox_row.add(box)
        listbox.add(listbox_row)

        listbox.get_style_context().add_class("parslinux-software-listbox-mostdown")
        return listbox

    def on_ui_ad_description_more_button_clicked(self, button):
        button.set_visible(False)
        self.ui_ad_description_label.set_text(self.ad_full_description_text)

    def on_ui_write_comment_button_clicked(self, button):
        self.ui_comment_dialog.run()
        self.ui_comment_dialog.hide()

    def on_ui_comment_close_button_clicked(self, button):
        self.ui_comment_dialog.hide()

    def on_ui_comment_star_button_press_event(self, widget, event):
        star = int(widget.get_name())
        self.set_comment_stars(star)

    def on_ui_comment_own_edit_button_clicked(self, button):
        self.ui_comment_mid_stack.set_visible_child_name("write")
        self.ui_comment_bottom_stack.set_visible_child_name("disclaimer")
        self.ui_comment_send_button.set_sensitive(True)
        if self.ui_comment_own:
            self.ui_comment_fullname_entry.set_text(self.ui_comment_own["fullname"])
            start, end = self.ui_comment_content_textbuffer.get_bounds()
            self.ui_comment_content_textbuffer.delete(start, end)
            self.ui_comment_content_textbuffer.insert(
                self.ui_comment_content_textbuffer.get_end_iter(),
                "{}".format(self.ui_comment_own["comment"]))
            self.set_comment_stars(self.ui_comment_own["point"])

    def on_ui_comment_send_button_clicked(self, button):
        author = self.ui_comment_fullname_entry.get_text().strip()
        start, end = self.ui_comment_content_textbuffer.get_bounds()
        comment = self.ui_comment_content_textbuffer.get_text(start, end, False).strip()
        value = self.comment_star_point
        if value == 0 or comment == "" or author == "":
            self.ui_comment_error_label.set_visible(True)
            self.ui_comment_error_label.set_text(_("All fields must be filled."))
        else:
            version = self.Package.installed_version(self.ui_app_name)
            if version is None:
                version = ""
            dic = {"mac": self.mac, "author": author, "comment": comment, "value": value, "app": self.ui_app_name,
                   "installed": True, "appversion": version, "distro": self.user_distro_full,
                   "justrate": False}
            try:
                self.AppRequest.send(self.Server.serverurl + self.Server.serversendrate, dic, self.ui_app_name)
                self.ui_comment_send_button.set_sensitive(False)
            except Exception as e:
                self.ui_comment_error_label.set_visible(True)
                self.ui_comment_error_label.set_text(f"{e}")

    def on_ui_comment_content_textbuffer_insert_text(self, buffer, location, text, length):
        max_chars = 500
        current_len = buffer.get_char_count()
        new_len = len(text)
        if current_len + new_len > max_chars:
            GObject.signal_stop_emission_by_name(buffer, "insert-text")
            remaining = max_chars - current_len
            if remaining > 0:
                buffer.insert(location, text[:remaining])

    def on_ui_suggestapp_eventbox_button_press_event(self, widget, event):
        self.ui_suggest_main_stack.set_visible_child_name("main")
        self.ui_suggest_dialog.run()
        self.ui_suggest_dialog.hide()

    def on_ui_suggest_close_button_clicked(self, button):
        self.ui_suggest_dialog.hide()

    def on_ui_suggest_send_button_clicked(self, button):
        email_regex = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        url_regex = re.compile(r"^(https?://)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/.*)?$")

        def is_valid_email(email):
            return email_regex.match(email) is not None

        def is_valid_url(url):
            return url_regex.match(url) is not None

        app_name = self.ui_suggest_appname_entry.get_text().strip()
        app_web = self.ui_suggest_appweb_entry.get_text().strip()
        user_name = self.ui_suggest_username_entry.get_text().strip()
        user_mail = self.ui_suggest_usermail_entry.get_text().strip()
        start, end = self.ui_suggest_why_textbuffer.get_bounds()
        why = self.ui_suggest_why_textbuffer.get_text(start, end, False).strip()

        if not all([app_name, app_web, user_name, user_mail, why]):
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(_("All fields must be filled."))
            return

        if not is_valid_email(user_mail):
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(_("Please enter a valid e-mail address."))
            return

        if not is_valid_url(app_web):
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(_("Please enter a valid website."))
            return

        dic = {"app_name": app_name, "app_web": app_web, "user_name": user_name, "user_mail": user_mail, "why": why,
               "mac": self.mac, "distro": self.user_distro_full}
        try:
            self.AppRequest.send(self.Server.serverurl + self.Server.serversendsuggest, dic)
            self.ui_suggest_send_button.set_sensitive(False)
        except Exception as e:
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(f"{e}")

    def on_ui_suggest_why_textbuffer_insert_text(self, buffer, location, text, length):
        max_chars = 500
        current_len = buffer.get_char_count()
        new_len = len(text)
        if current_len + new_len > max_chars:
            GObject.signal_stop_emission_by_name(buffer, "insert-text")
            remaining = max_chars - current_len
            if remaining > 0:
                buffer.insert(location, text[:remaining])

    def clear_suggest_dialog(self):
        self.ui_suggest_appname_entry.set_text("")
        self.ui_suggest_appweb_entry.set_text("")
        self.ui_suggest_username_entry.set_text("")
        self.ui_suggest_usermail_entry.set_text("")
        self.ui_suggest_error_label.set_text("")
        self.ui_suggest_error_label.set_visible(False)
        start, end = self.ui_suggest_why_textbuffer.get_bounds()
        self.ui_suggest_why_textbuffer.delete(start, end)
