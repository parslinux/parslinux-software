#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import grp
import locale
import os
import re
import subprocess
import threading
import json
import cairo
from pathlib import Path
from hashlib import md5
from datetime import datetime, timezone
from locale import gettext as _
import gi

try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    netifaces = None
    HAS_NETIFACES = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

locale.bindtextdomain('parslinux-software', '/usr/share/locale')
locale.textdomain('parslinux-software')

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Vte", "2.91")
from gi.repository import GLib, Gtk, GObject, Notify, GdkPixbuf, Gdk, Vte, Pango

from Package import Package
from Server import Server

from AppImage import AppImage
from AppDetail import AppDetail
from AppRequest import AppRequest
from GnomeComment import GnomeComment
from UserSettings import UserSettings
from Utils import Utils
from Logger import Logger
from FlatpakManager import FlatpakManager


from controllers.SliderMixin import SliderMixin
from controllers.ImageGalleryMixin import ImageGalleryMixin
from controllers.SearchMixin import SearchMixin
from controllers.DetailMixin import DetailMixin
from controllers.QueueMixin import QueueMixin
from controllers.InstalledMixin import InstalledMixin

class MainWindow(SliderMixin, ImageGalleryMixin, SearchMixin, DetailMixin, QueueMixin, InstalledMixin):
    def __init__(self, application):
        self.Application = application

        self.Logger = Logger(__name__)
        self.FlatpakManager = FlatpakManager()

        self.MainWindowUIFileName = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        try:
            self.GtkBuilder = Gtk.Builder.new_from_file(self.MainWindowUIFileName)
            self.GtkBuilder.connect_signals(self)
        except GObject.GError as e:
            self.Logger.warning("Error reading GUI file")
            self.Logger.exception("{}".format(e))
            raise

        self.user_locale = self.get_user_locale()
        self.Logger.info("user_locale: {}".format(self.user_locale))

        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.dpkglockerror_message = ""
        self.error_message = ""

        self.searching = False
        self.app_action_buttons = {}
        self.queue_widgets = {}

        self.bottomrevealer = self.GtkBuilder.get_object("bottomrevealer")

        self.bottomerrorlabel = self.GtkBuilder.get_object("bottomerrorlabel")
        self.bottomerrorbutton = self.GtkBuilder.get_object("bottomerrorbutton")

        self.bottominterruptlabel = self.GtkBuilder.get_object("bottominterruptlabel")
        self.bottominterrupt_fix_button = self.GtkBuilder.get_object("bottominterrupt_fix_button")
        self.bottominterrupthide_button = self.GtkBuilder.get_object("bottominterrupthide_button")

        self.pop_interruptinfo_label = self.GtkBuilder.get_object("pop_interruptinfo_label")
        self.pop_interruptinfo_spinner = self.GtkBuilder.get_object("pop_interruptinfo_spinner")
        self.pop_interruptinfo_ok_button = self.GtkBuilder.get_object("pop_interruptinfo_ok_button")
        self.interruptpopover = self.GtkBuilder.get_object("interruptpopover")

        self.bottomerrordetails_popover = self.GtkBuilder.get_object("bottomerrordetails_popover")
        self.bottomerrordetails_label = self.GtkBuilder.get_object("bottomerrordetails_label")
        self.bottomerrordetails_button = self.GtkBuilder.get_object("bottomerrordetails_button")

        self.mainstack = self.GtkBuilder.get_object("mainstack")
        self.homestack = self.GtkBuilder.get_object("homestack")
        self.bottomstack = self.GtkBuilder.get_object("bottomstack")

        self.ui_back_button = self.GtkBuilder.get_object("ui_back_button")
        self.ui_back_button.set_sensitive(False)

        self.splashspinner = self.GtkBuilder.get_object("splashspinner")
        self.splashbar = self.GtkBuilder.get_object("splashbar")
        self.splashlabel = self.GtkBuilder.get_object("splashlabel")
        self.splashbarstatus = True

        # myapps remove popup
        self.ui_myapp_pop_stack = self.GtkBuilder.get_object("ui_myapp_pop_stack")
        self.ui_myapp_pop_spinner = self.GtkBuilder.get_object("ui_myapp_pop_spinner")
        self.ui_myapp_pop_sw = self.GtkBuilder.get_object("ui_myapp_pop_sw")

        self.ui_myapp_pop_app = self.GtkBuilder.get_object("ui_myapp_pop_app")
        self.ui_myapp_pop_package = self.GtkBuilder.get_object("ui_myapp_pop_package")
        self.ui_myapp_pop_uninstall_button = self.GtkBuilder.get_object("ui_myapp_pop_uninstall_button")

        self.ui_myapp_pop_toremove_label = self.GtkBuilder.get_object("ui_myapp_pop_toremove_label")
        self.ui_myapp_pop_toinstall_label = self.GtkBuilder.get_object("ui_myapp_pop_toinstall_label")
        self.ui_myapp_pop_broken_label = self.GtkBuilder.get_object("ui_myapp_pop_broken_label")
        self.ui_myapp_pop_fsize_label = self.GtkBuilder.get_object("ui_myapp_pop_fsize_label")
        self.ui_myapp_pop_dsize_label = self.GtkBuilder.get_object("ui_myapp_pop_dsize_label")
        self.ui_myapp_pop_isize_label = self.GtkBuilder.get_object("ui_myapp_pop_isize_label")

        self.ui_myapp_pop_disclaimer_remove_label = self.GtkBuilder.get_object("ui_myapp_pop_disclaimer_remove_label")

        self.ui_myapp_pop_notfound_image = self.GtkBuilder.get_object("ui_myapp_pop_notfound_image")
        self.ui_myapp_pop_notfound_name = self.GtkBuilder.get_object("ui_myapp_pop_notfound_name")

        self.ui_myapp_pop_toremove_box = self.GtkBuilder.get_object("ui_myapp_pop_toremove_box")
        self.ui_myapp_pop_toinstall_box = self.GtkBuilder.get_object("ui_myapp_pop_toinstall_box")
        self.ui_myapp_pop_broken_box = self.GtkBuilder.get_object("ui_myapp_pop_broken_box")
        self.ui_myapp_pop_fsize_box = self.GtkBuilder.get_object("ui_myapp_pop_fsize_box")
        self.ui_myapp_pop_dsize_box = self.GtkBuilder.get_object("ui_myapp_pop_dsize_box")
        self.ui_myapp_pop_isize_box = self.GtkBuilder.get_object("ui_myapp_pop_isize_box")

        self.ui_myapps_combobox = self.GtkBuilder.get_object("ui_myapps_combobox")
        self.ui_myapps_du_progress_box = self.GtkBuilder.get_object("ui_myapps_du_progress_box")
        self.ui_myapps_du_spinner = self.GtkBuilder.get_object("ui_myapps_du_spinner")
        self.ui_myapps_du_progress_label = self.GtkBuilder.get_object("ui_myapps_du_progress_label")

        self.ui_right_stack = self.GtkBuilder.get_object("ui_right_stack")

        self.ui_discover_scrolledwindow = self.GtkBuilder.get_object("ui_discover_scrolledwindow")
        self.ui_parslinuxapps_scrolledwindow = self.GtkBuilder.get_object("ui_parslinuxapps_scrolledwindow")
        self.ui_installedapps_scrolledwindow = self.GtkBuilder.get_object("ui_installedapps_scrolledwindow")

        self.ui_currentcat_label = self.GtkBuilder.get_object("ui_currentcat_label")
        self.ui_currentcat_image = self.GtkBuilder.get_object("ui_currentcat_image")

        self.ui_top_searchentry = self.GtkBuilder.get_object("ui_top_searchentry")
        self.ui_top_searchentry.set_sensitive(False)
        self.ui_top_searchentry.props.primary_icon_activatable = True
        self.ui_top_searchentry.props.primary_icon_sensitive = True

        self.ui_repoapps_flowbox = self.GtkBuilder.get_object("ui_repoapps_flowbox")
        self.ui_repotitle_box = self.GtkBuilder.get_object("ui_repotitle_box")

        self.ui_parslinuxapps_flowbox = self.GtkBuilder.get_object("ui_parslinuxapps_flowbox")
        self.ui_parslinuxapps_flowbox.set_filter_func(self.parslinuxapps_filter_function)
        self.ui_parslinuxapps_flowbox.set_sort_func(self.parslinuxapps_sort_func)
        self._flowbox_app_ids = set()

        self.ui_parslinuxapps_title_stack = self.GtkBuilder.get_object("ui_parslinuxapps_title_stack")
        self.ui_searchterm_label = self.GtkBuilder.get_object("ui_searchterm_label")

        self.ui_trend_flowbox = self.GtkBuilder.get_object("ui_trend_flowbox")
        self.ui_mostdown_flowbox = self.GtkBuilder.get_object("ui_mostdown_flowbox")
        self.ui_recent_flowbox = self.GtkBuilder.get_object("ui_recent_flowbox")
        self.ui_editor_flowbox = self.GtkBuilder.get_object("ui_editor_flowbox")

        self.ui_trendapps_flowbox = self.GtkBuilder.get_object("ui_trendapps_flowbox")
        self.ui_mostdownapps_flowbox = self.GtkBuilder.get_object("ui_mostdownapps_flowbox")
        self.ui_recentapps_flowbox = self.GtkBuilder.get_object("ui_recentapps_flowbox")

        self.ui_upgradableapps_flowbox = self.GtkBuilder.get_object("ui_upgradableapps_flowbox")
        self.ui_upgradableapps_box = self.GtkBuilder.get_object("ui_upgradableapps_box")
        self.ui_upgradableapps_count_label = self.GtkBuilder.get_object("ui_upgradableapps_count_label")
        self.ui_upgradables_combobox = self.GtkBuilder.get_object("ui_upgradables_combobox")
        self.ui_installedapps_box = self.GtkBuilder.get_object("ui_installedapps_box")
        self.ui_installedapps_flowbox = self.GtkBuilder.get_object("ui_installedapps_flowbox")
        self.ui_installedapps_flowbox.set_filter_func(self.installedapps_filter_function)

        self.ui_appdetails_scrolledwindow = self.GtkBuilder.get_object("ui_appdetails_scrolledwindow")

        self.ui_ad_name = self.GtkBuilder.get_object("ui_ad_name")
        self.ui_ad_icon = self.GtkBuilder.get_object("ui_ad_icon")
        self.ui_ad_subcategory_label = self.GtkBuilder.get_object("ui_ad_subcategory_label")
        self.ui_ad_top_category_label = self.GtkBuilder.get_object("ui_ad_top_category_label")
        self.ui_ad_top_avgrate_label = self.GtkBuilder.get_object("ui_ad_top_avgrate_label")
        self.ui_ad_top_download_label = self.GtkBuilder.get_object("ui_ad_top_download_label")
        self.ui_ad_top_size_label = self.GtkBuilder.get_object("ui_ad_top_size_label")
        self.ui_ad_top_depends_count_label = self.GtkBuilder.get_object("ui_ad_top_depends_count_label")
        self.ui_ad_action_button = self.GtkBuilder.get_object("ui_ad_action_button")
        self.ui_ad_disclaimer_button = self.GtkBuilder.get_object("ui_ad_disclaimer_button")
        self.ui_ad_remove_button = self.GtkBuilder.get_object("ui_ad_remove_button")
        self.ui_ad_image_box = self.GtkBuilder.get_object("ui_ad_image_box")

        self.ui_disclaimer_popover = self.GtkBuilder.get_object("ui_disclaimer_popover")

        self.ui_ad_top_stack = self.GtkBuilder.get_object("ui_ad_top_stack")
        self.ui_ad_action_stack = self.GtkBuilder.get_object("ui_ad_action_stack")
        self.ui_ad_about_box = self.GtkBuilder.get_object("ui_ad_about_box")
        self.ui_ad_details_box = self.GtkBuilder.get_object("ui_ad_details_box")
        self.ui_ad_dependencies_box = self.GtkBuilder.get_object("ui_ad_dependencies_box")
        self.ui_ad_availablerepos_box = self.GtkBuilder.get_object("ui_ad_availablerepos_box")
        self.ui_ad_ratings_box = self.GtkBuilder.get_object("ui_ad_ratings_box")

        self.ui_ad_image_scrolledwindow = self.GtkBuilder.get_object("ui_ad_image_scrolledwindow")
        self.ui_ad_image_scrolledwindow.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.ui_ad_image_scrolledwindow.connect("button-press-event", self.on_ui_ad_image_button_press)
        self.ui_ad_image_scrolledwindow.connect("motion-notify-event", self.on_ui_ad_image_mouse_drag)
        self.ui_ad_image_scrolledwindow.connect("button-release-event", self.on_ui_ad_image_button_release)
        self.ui_ad_image_dragging = False
        self.ui_ad_image_last_x = 0
        self.ui_ad_image_total_drag = 0
        self.ui_ad_image_drag_threshold = 8
        self.ui_ad_image_drag_touch_threshold = 2
        self.ui_ad_image_is_touch = False

        self.ui_ad_description_label = self.GtkBuilder.get_object("ui_ad_description_label")
        self.ui_ad_description_more_button = self.GtkBuilder.get_object("ui_ad_description_more_button")
        self.ui_ad_version_label = self.GtkBuilder.get_object("ui_ad_version_label")
        self.ui_ad_sizetitle_label = self.GtkBuilder.get_object("ui_ad_sizetitle_label")
        self.ui_ad_size_label = self.GtkBuilder.get_object("ui_ad_size_label")
        self.ui_ad_required_sizetitle_label = self.GtkBuilder.get_object("ui_ad_required_sizetitle_label")
        self.ui_ad_required_size_label = self.GtkBuilder.get_object("ui_ad_required_size_label")
        self.ui_ad_type_label = self.GtkBuilder.get_object("ui_ad_type_label")
        self.ui_ad_category_label = self.GtkBuilder.get_object("ui_ad_category_label")
        self.ui_ad_license_label = self.GtkBuilder.get_object("ui_ad_license_label")
        self.ui_ad_component_label = self.GtkBuilder.get_object("ui_ad_component_label")
        self.ui_ad_maintainer_name_label = self.GtkBuilder.get_object("ui_ad_maintainer_name_label")
        self.ui_ad_maintainer_web_label = self.GtkBuilder.get_object("ui_ad_maintainer_web_label")
        self.ui_ad_maintainer_mail_label = self.GtkBuilder.get_object("ui_ad_maintainer_mail_label")
        self.ui_ad_available_repos_box = self.GtkBuilder.get_object("ui_ad_available_repos_box")
        self.ui_ad_important_label = self.GtkBuilder.get_object("ui_ad_important_label")

        self.ui_ad_install_list_box = self.GtkBuilder.get_object("ui_ad_install_list_box")
        self.ui_ad_install_list_eventbox = self.GtkBuilder.get_object("ui_ad_install_list_eventbox")
        self.ui_ad_install_list_image = self.GtkBuilder.get_object("ui_ad_install_list_image")
        self.ui_ad_install_list_revealer = self.GtkBuilder.get_object("ui_ad_install_list_revealer")
        self.ui_ad_install_list_label = self.GtkBuilder.get_object("ui_ad_install_list_label")
        self.ui_ad_install_list_count_label = self.GtkBuilder.get_object("ui_ad_install_list_count_label")

        self.ui_ad_remove_list_box = self.GtkBuilder.get_object("ui_ad_remove_list_box")
        self.ui_ad_remove_list_eventbox = self.GtkBuilder.get_object("ui_ad_remove_list_eventbox")
        self.ui_ad_remove_list_image = self.GtkBuilder.get_object("ui_ad_remove_list_image")
        self.ui_ad_remove_list_revealer = self.GtkBuilder.get_object("ui_ad_remove_list_revealer")
        self.ui_ad_remove_list_label = self.GtkBuilder.get_object("ui_ad_remove_list_label")
        self.ui_ad_remove_list_count_label = self.GtkBuilder.get_object("ui_ad_remove_list_count_label")

        self.ui_ad_broken_list_box = self.GtkBuilder.get_object("ui_ad_broken_list_box")
        self.ui_ad_broken_list_eventbox = self.GtkBuilder.get_object("ui_ad_broken_list_eventbox")
        self.ui_ad_broken_list_image = self.GtkBuilder.get_object("ui_ad_broken_list_image")
        self.ui_ad_broken_list_revealer = self.GtkBuilder.get_object("ui_ad_broken_list_revealer")
        self.ui_ad_broken_list_label = self.GtkBuilder.get_object("ui_ad_broken_list_label")
        self.ui_ad_broken_list_count_label = self.GtkBuilder.get_object("ui_ad_broken_list_count_label")

        self.ui_ad_bottom_avgrate_label = self.GtkBuilder.get_object("ui_ad_bottom_avgrate_label")
        self.ui_ad_bottom_rate_count_label = self.GtkBuilder.get_object("ui_ad_bottom_rate_count_label")

        self.ui_ad_rating_star1_image = self.GtkBuilder.get_object("ui_ad_rating_star1_image")
        self.ui_ad_rating_star2_image = self.GtkBuilder.get_object("ui_ad_rating_star2_image")
        self.ui_ad_rating_star3_image = self.GtkBuilder.get_object("ui_ad_rating_star3_image")
        self.ui_ad_rating_star4_image = self.GtkBuilder.get_object("ui_ad_rating_star4_image")
        self.ui_ad_rating_star5_image = self.GtkBuilder.get_object("ui_ad_rating_star5_image")

        self.ui_rating_prg1_progressbar = self.GtkBuilder.get_object("ui_rating_prg1_progressbar")
        self.ui_rating_prg2_progressbar = self.GtkBuilder.get_object("ui_rating_prg2_progressbar")
        self.ui_rating_prg3_progressbar = self.GtkBuilder.get_object("ui_rating_prg3_progressbar")
        self.ui_rating_prg4_progressbar = self.GtkBuilder.get_object("ui_rating_prg4_progressbar")
        self.ui_rating_prg5_progressbar = self.GtkBuilder.get_object("ui_rating_prg5_progressbar")

        self.ui_rating_count1_label = self.GtkBuilder.get_object("ui_rating_count1_label")
        self.ui_rating_count2_label = self.GtkBuilder.get_object("ui_rating_count2_label")
        self.ui_rating_count3_label = self.GtkBuilder.get_object("ui_rating_count3_label")
        self.ui_rating_count4_label = self.GtkBuilder.get_object("ui_rating_count4_label")
        self.ui_rating_count5_label = self.GtkBuilder.get_object("ui_rating_count5_label")

        self.ui_ad_comments_flowbox = self.GtkBuilder.get_object("ui_ad_comments_flowbox")
        self.ui_ad_more_comment_button = self.GtkBuilder.get_object("ui_ad_more_comment_button")

        self.ui_comment_dialog = self.GtkBuilder.get_object("ui_comment_dialog")
        self.ui_comment_main_stack = self.GtkBuilder.get_object("ui_comment_main_stack")
        self.ui_comment_mid_stack = self.GtkBuilder.get_object("ui_comment_mid_stack")
        self.ui_comment_mid_editable_stack = self.GtkBuilder.get_object("ui_comment_mid_editable_stack")
        self.ui_comment_bottom_stack = self.GtkBuilder.get_object("ui_comment_bottom_stack")
        self.ui_comment_icon_image = self.GtkBuilder.get_object("ui_comment_icon_image")
        self.ui_comment_appname_label = self.GtkBuilder.get_object("ui_comment_appname_label")
        self.ui_comment_subcategory_label = self.GtkBuilder.get_object("ui_comment_subcategory_label")
        self.ui_comment_version_label = self.GtkBuilder.get_object("ui_comment_version_label")
        self.ui_comment_fullname_entry = self.GtkBuilder.get_object("ui_comment_fullname_entry")
        self.ui_comment_content_textview = self.GtkBuilder.get_object("ui_comment_content_textview")
        self.ui_comment_content_textbuffer = self.GtkBuilder.get_object("ui_comment_content_textbuffer")
        self.ui_comment_send_button = self.GtkBuilder.get_object("ui_comment_send_button")
        self.ui_comment_error_label = self.GtkBuilder.get_object("ui_comment_error_label")
        self.ui_comment_info_label = self.GtkBuilder.get_object("ui_comment_info_label")
        self.ui_comment_star1_image = self.GtkBuilder.get_object("ui_comment_star1_image")
        self.ui_comment_star2_image = self.GtkBuilder.get_object("ui_comment_star2_image")
        self.ui_comment_star3_image = self.GtkBuilder.get_object("ui_comment_star3_image")
        self.ui_comment_star4_image = self.GtkBuilder.get_object("ui_comment_star4_image")
        self.ui_comment_star5_image = self.GtkBuilder.get_object("ui_comment_star5_image")
        self.ui_comment_own_star1_image = self.GtkBuilder.get_object("ui_comment_own_star1_image")
        self.ui_comment_own_star2_image = self.GtkBuilder.get_object("ui_comment_own_star2_image")
        self.ui_comment_own_star3_image = self.GtkBuilder.get_object("ui_comment_own_star3_image")
        self.ui_comment_own_star4_image = self.GtkBuilder.get_object("ui_comment_own_star4_image")
        self.ui_comment_own_star5_image = self.GtkBuilder.get_object("ui_comment_own_star5_image")
        self.ui_comment_own_fullname_label = self.GtkBuilder.get_object("ui_comment_own_fullname_label")
        self.ui_comment_own_content_label = self.GtkBuilder.get_object("ui_comment_own_content_label")
        self.ui_comment_own_edit_button = self.GtkBuilder.get_object("ui_comment_own_edit_button")
        self.ui_comment_own_date_label = self.GtkBuilder.get_object("ui_comment_own_date_label")

        self.ui_suggest_dialog = self.GtkBuilder.get_object("ui_suggest_dialog")
        self.ui_suggest_main_stack = self.GtkBuilder.get_object("ui_suggest_main_stack")
        self.ui_suggest_appname_entry = self.GtkBuilder.get_object("ui_suggest_appname_entry")
        self.ui_suggest_appweb_entry = self.GtkBuilder.get_object("ui_suggest_appweb_entry")
        self.ui_suggest_username_entry = self.GtkBuilder.get_object("ui_suggest_username_entry")
        self.ui_suggest_usermail_entry = self.GtkBuilder.get_object("ui_suggest_usermail_entry")
        self.ui_suggest_appweb_entry = self.GtkBuilder.get_object("ui_suggest_appweb_entry")
        self.ui_suggest_why_textview = self.GtkBuilder.get_object("ui_suggest_why_textview")
        self.ui_suggest_why_textbuffer = self.GtkBuilder.get_object("ui_suggest_why_textbuffer")
        self.ui_suggest_error_label = self.GtkBuilder.get_object("ui_suggest_error_label")
        self.ui_suggest_send_button = self.GtkBuilder.get_object("ui_suggest_send_button")

        self.ui_image_popover = self.GtkBuilder.get_object("ui_image_popover")
        self.ui_image_stack = self.GtkBuilder.get_object("ui_image_stack")
        self.ui_image_resize_image = self.GtkBuilder.get_object("ui_image_resize_image")

        self.ui_myapp_details_popover = self.GtkBuilder.get_object("ui_myapp_details_popover")

        self.ui_headermenu_popover = self.GtkBuilder.get_object("ui_headermenu_popover")
        self.ui_headermenu_button = self.GtkBuilder.get_object("ui_headermenu_button")

        self.ui_header_queue_button = self.GtkBuilder.get_object("ui_header_queue_button")
        self.ui_header_aptupdate_spinner = self.GtkBuilder.get_object("ui_header_aptupdate_spinner")

        self.aboutdialog = self.GtkBuilder.get_object("aboutdialog")
        self.aboutdialog.set_program_name(_("Pars Linux Software Center"))
        if self.aboutdialog.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About Pars Linux Software Center"))
            about_headerbar.pack_start(Gtk.Image.new_from_icon_name("parslinux-software", Gtk.IconSize.LARGE_TOOLBAR))
            about_headerbar.show_all()
            self.aboutdialog.set_titlebar(about_headerbar)

        self.ui_settings_dark_switch = self.GtkBuilder.get_object("ui_settings_dark_switch")
        self.ui_settings_animations_switch = self.GtkBuilder.get_object("ui_settings_animations_switch")
        self.ui_settings_gcomments_switch = self.GtkBuilder.get_object("ui_settings_gcomments_switch")
        self.ui_settings_update_switch = self.GtkBuilder.get_object("ui_settings_update_switch")
        self.ui_settings_available_switch = self.GtkBuilder.get_object("ui_settings_available_switch")

        self.ui_settings_update_label = self.GtkBuilder.get_object("ui_settings_update_label")

        self.ui_settings_cache_button = self.GtkBuilder.get_object("ui_settings_cache_button")
        self.ui_settings_cache_info_label = self.GtkBuilder.get_object("ui_settings_cache_info_label")
        self.ui_settings_cache_size_label = self.GtkBuilder.get_object("ui_settings_cache_size_label")
        self.ui_settings_password_button = self.GtkBuilder.get_object("ui_settings_password_button")
        self.ui_settings_password_info_label = self.GtkBuilder.get_object("ui_settings_password_info_label")

        self.ui_tryfix_stack = self.GtkBuilder.get_object("ui_tryfix_stack")
        self.ui_tryfix_button = self.GtkBuilder.get_object("ui_tryfix_button")
        self.ui_tryfix_spinner = self.GtkBuilder.get_object("ui_tryfix_spinner")
        self.ui_tryfix_spinner = self.GtkBuilder.get_object("ui_tryfix_spinner")
        self.ui_tryfix_cancel_button = self.GtkBuilder.get_object("ui_tryfix_cancel_button")
        self.ui_tryfix_confirm_button = self.GtkBuilder.get_object("ui_tryfix_confirm_button")
        self.ui_tryfix_done_button = self.GtkBuilder.get_object("ui_tryfix_done_button")


        self.noserverlabel = self.GtkBuilder.get_object("noserverlabel")

        self.current_category = "discover"
        self.cat_all = {
            "name": "tümü" if self.user_locale == "tr" else "all",
            "icon": "all",
            "number": 0
        }

        self.mac = self.getMac()

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)
        self.MainWindow.set_title(_("Pars Linux Software Center"))
        self.control_display()
        self.mainstack.set_visible_child_name("splash")

        self.isinstalled = None
        self.isupgrade = False

        self.dpkgconfiguring = False

        self.ui_comment_own = {}

        self.ui_app_name = ""

        self.inprogress_app_name = ""
        self.inprogress_command = ""
        self.inprogress_desktop = ""

        self.queue = []
        self.inprogress = False

        self.isbroken = False

        self.connection_error_after = False
        self.auto_apt_update_finished = False

        self.Server = None
        self.Package = None
        self.apps = {}
        self.apps_full = {}
        self.cats = []

        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""
        self.myapp_toremove_icon = ""

        self.important_packages = ["parslinux-desktop", "parslinux-base", "parslinux-software",
                                   "xfce4-session", "gnome-session",
                                   "cinnamon", "cinnamon-session"]

        self.i386_packages = ["wine"]

        self.errormessage = ""
        self.grouperrormessage = ""

        self.ad_full_description_text = ""

        self.imgfullscreen_count = 0

        self.slider_current_page = 0

        self.comment_star_point = 0

        self.stack_history = []

        self.repo_final_list = []

        self.slider_timer_id = None
        self.slider_pause_id = None
        self.pause_active = False
        self.slider_auto_time = 6
        self.slider_pause_time = 10
        self.slider_slogan_max_chars = 30

        self.server_cat_all = {}

        settings = Gtk.Settings.get_default()
        layout = settings.get_property("gtk-decoration-layout") or ""
        self.Logger.info(f"decoration_layout: {layout}")

        # remove icon from left side of decoration
        parts = layout.split(":", 1)
        left = parts[0]
        right = parts[1] if len(parts) > 1 else None
        left_items = [item.strip() for item in left.split(",") if item.strip() and item.strip() != "icon"]
        left_clean = ",".join(left_items)
        if right is None:
            new_layout = left_clean
        else:
            new_left = left_clean
            new_right = right
            if new_left == "" and new_right != "":
                new_layout = f":{new_right}"
            elif new_left != "" and new_right == "":
                new_layout = f"{new_left}:"
            elif new_left != "" and new_right != "":
                new_layout = f"{new_left}:{new_right}"
            else:
                new_layout = ":"

        settings.set_property("gtk-decoration-layout", new_layout)
        self.Logger.info(f"new_decoration_layout: {new_layout}")

        theme_name = "{}".format(settings.get_property('gtk-theme-name')).lower().strip()
        self.Logger.info(f"theme_name: {theme_name}")

        cssProvider = Gtk.CssProvider()
        if theme_name.startswith("parslinux") or theme_name.startswith("adwaita"):
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/adwaita.css")
        else:
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/base.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.tryfix_vteterm = None
        self.ui_tryfix_vte_sw = self.GtkBuilder.get_object("ui_tryfix_vte_sw")

        self.dpkgconfigure_vteterm = None
        self.interrupt_vte_box = self.GtkBuilder.get_object("interrupt_vte_box")

        self.ui_queue_flowbox = self.GtkBuilder.get_object("ui_queue_flowbox")
        self.ui_queue_stack = self.GtkBuilder.get_object("ui_queue_stack")

        self.ui_leftcats_box = self.GtkBuilder.get_object("ui_leftcats_box")
        self.ui_leftcats_listbox = self.GtkBuilder.get_object("ui_leftcats_listbox")
        self.ui_leftupdates_listbox = self.GtkBuilder.get_object("ui_leftupdates_listbox")
        self.ui_leftupdates_separator = self.GtkBuilder.get_object("ui_leftupdates_separator")
        self.ui_leftinstalled_listbox = self.GtkBuilder.get_object("ui_leftinstalled_listbox")
        self.ui_slider_stack = self.GtkBuilder.get_object("ui_slider_stack")
        self.ui_slider_overlay = self.GtkBuilder.get_object("ui_slider_overlay")

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.aboutdialog.set_version(version)
        except:
            pass

        self.home_trend_count = 8
        self.home_most_down_count = 8
        self.home_recent_count = 4

        self.myapps_du_cancel_event = None

        self.status_server_apps = False
        self.status_server_icons = False
        self.status_server_images = False
        self.status_server_cats = False
        self.status_server_home = False

        self.AppImage = AppImage()
        self.AppImage.app_image_from_server = self.app_image_from_server

        self.AppDetail = AppDetail()
        self.AppDetail.app_details_from_server = self.app_details_from_server

        self.AppRequest = AppRequest()
        self.AppRequest.rating_response_from_server = self.rating_response_from_server

        self.GnomeComment = GnomeComment()
        self.GnomeComment.gnome_comments_from_server = self.gnome_comments_from_server

        

        self.utils()
        self.usersettings()
        self.prepend_server_icons()

        self.user_distro_full = "{}, ({})".format(self.UserSettings.user_distro, self.user_desktop_env)
        self.Logger.info("{}".format(self.user_distro_full))

        if self.UserSettings.config_dark_theme:
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = True

        self.MainWindow.show_all()

        self.hide_some_widgets()

        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()
        self.Logger.info("start done")

    def getMac(self):
        mac = ""
        if HAS_NETIFACES and netifaces:
            try:
                try:
                    AF_LINK = netifaces.AF_LINK
                except:
                    AF_LINK = 17
                gateway_info = netifaces.gateways()
                default_gateways = gateway_info['default']
                for family in default_gateways:
                    interface = default_gateways[family][1]
                    if AF_LINK in netifaces.ifaddresses(interface):
                        mac = netifaces.ifaddresses(interface)[AF_LINK][0]["addr"].upper()
                    break
            except Exception:
                pass
        if not mac and HAS_PSUTIL and psutil:
            try:
                import socket
                nics = psutil.net_if_addrs()
                nics.pop('lo', None)
                for i in nics:
                    for j in nics[i]:
                        if hasattr(socket, 'AF_PACKET') and j.family == socket.AF_PACKET:
                            mac = j.address.upper()
                            break
                        elif getattr(j, "family", None) == 17:
                            mac = j.address.upper()
                            break
                    if mac:
                        break
            except Exception:
                pass
        return mac or "00:00:00:00:00:00"

    def get_user_locale(self):
        lang = os.getenv("LANG")
        if lang:
            lang = lang.split(".", 1)[0].split("_", 1)[0]
        if not lang:
            loc = locale.getlocale()[0]
            if loc:
                lang = loc.split("_", 1)[0]
        lang = (lang or "en").lower()
        return lang if lang in ("tr", "en") else "en"

    # def on_MainWindow_configure_event(self, widget, event):
    #     width, height = widget.get_size()
    #     self.Logger.info("Size: {} x {}".format(width, height))

    def control_display(self):
        self.display_width = 1920
        width = 1071
        height = 750
        s = 1
        w = 1920
        h = 1080
        try:
            def get_active_monitor():
                display = Gdk.Display.get_default()
                monitor = display.get_primary_monitor()
                if monitor:
                    self.Logger.info("monitor from get_primary_monitor")
                    return monitor
                device_manager = display.get_device_manager()
                pointer = device_manager.get_client_pointer()
                if pointer:
                    screen, x, y = pointer.get_position()
                    monitor_num = screen.get_monitor_at_point(x, y)
                    if monitor_num >= 0:
                        self.Logger.info("monitor from pointer position")
                        return display.get_monitor(monitor_num)
                self.Logger.info("monitor from get_monitor(0)")
                return display.get_monitor(0)

            monitor = get_active_monitor()
            geometry = monitor.get_geometry()
            w = geometry.width
            h = geometry.height
            s = monitor.get_scale_factor()

            self.display_width = w

            if w > 1920 or h > 1080:
                width = int(w * 0.5578)
                height = int(h * 0.6944)

            if w <= 1370 or h <= 768:
                width = 1028
                height = 661

            if w <= 1024:
                width = 925

            self.MainWindow.resize(width, height)

        except Exception as e:
            self.Logger.warning("Error in controlDisplay")
            self.Logger.exception("{}".format(e))

        self.Logger.info("window w:{} h:{} | monitor w:{} h:{} s:{}".format(width, height, w, h, s))

    def hide_some_widgets(self):
        self.ui_myapps_du_progress_box.set_visible(False)
        self.ui_header_queue_button.set_visible(False)
        self.ui_header_aptupdate_spinner.set_visible(False)
        self.ui_upgradables_combobox.set_visible(False)
        self.ui_suggest_error_label.set_visible(False)
        self.bottomerrordetails_button.set_visible(False)
        self.ui_repotitle_box.set_visible(False)
        self.ui_ad_description_more_button.set_visible(False)

    def worker(self):
        GLib.idle_add(self.splashspinner.start)
        self.set_animations()
        self.package()
        self.server()

    def start_auto_apt_update_control(self):
        if getattr(self.Server, "is_flathub", False):
            self.auto_apt_update_finished = True
            return
        if self.Server.connection and self.UserSettings.config_auto_apt_update:
            waittime = 86400
            if self.UserSettings.config_force_apt_update_time == 0:
                waittime = self.Server.apt_uptime
            else:
                waittime = self.UserSettings.config_force_apt_update_time
            if self.UserSettings.config_last_apt_update + waittime < int(datetime.now().timestamp()):
                GLib.idle_add(self.ui_header_aptupdate_spinner.start)
                GLib.idle_add(self.ui_header_aptupdate_spinner.set_visible, True)
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/AutoAptUpdate.py"]
                self.apt_update_process(command)
            else:
                self.auto_apt_update_finished = True
        else:
            self.auto_apt_update_finished = True

    def control_software_update(self):
        return

    def control_available_apps(self):
        if self.Server.connection:
            self.set_available_apps(available=self.UserSettings.config_only_available)

    def control_args(self):
        if "details" in self.Application.args.keys():
            app_found = False
            myapps_found = False
            app = self.Application.args["details"]
            try:
                if app.endswith(".parsapp"):
                    if os.path.isfile(app):
                        appfile = open(app, "r")
                        app = appfile.read().strip()
            except Exception as e:
                self.Logger.exception("{}".format(e))
            try:
                package_name = ""
                app_name_without_desktop = app.replace(".desktop", "").strip()
                for key, details in self.apps_full.items():
                    candidates = [
                        key,
                        (details.get("desktop") or "").replace(".desktop", ""),
                        (details.get("gnomename") or "").replace(".desktop", "")
                    ]
                    extras = (details.get("desktopextras") or "").replace(" ", "")
                    if extras:
                        candidates.extend(e.replace(".desktop", "") for e in extras.split(",") if e)
                    if app_name_without_desktop in candidates:
                        app_found = True
                        package_name = key
                        break
                if app_found:
                    GLib.idle_add(self.set_app_details_page, package_name)
            except Exception as e:
                self.Logger.exception("{}".format(e))
            try:
                if not app_found:
                    app_name_with_desktop = app
                    if not app.endswith(".desktop"):
                        app_name_with_desktop = f"{app}.desktop"
                    for fbc in self.ui_installedapps_flowbox:
                        myapp_dic = fbc.get_children()[0].get_children()[0].name
                        if myapp_dic["id"] == app_name_with_desktop:
                            myapps_found = True
                            threading.Thread(target=self.myappsdetail_page_worker_thread,
                                             args=(myapp_dic["filename"], myapp_dic,), daemon=True).start()
                    if not myapps_found:
                        app_name = app.replace(".desktop", "").strip()
                        details = {"name": app_name, "icon_name": "ps-repo-package-symbolic",
                                   "description": self.Package.adv_description(app), "repo_app": True}
                        self.set_app_details_page({app_name: details}, source=2)
                        self.Logger.info(f"control_args: {app} not found")
                        pass
            except Exception as e:
                self.Logger.exception("{}".format(e))

    def set_initial_home(self):
        self.Logger.info("in set_initial_home")

        GLib.idle_add(self.mainstack.set_visible_child_name, "home")
        if self.Server.connection:
            if not self.isbroken:
                GLib.idle_add(self.homestack.set_visible_child_name, "parslinuxhome")
                GLib.idle_add(self.ui_top_searchentry.set_sensitive, True)
            else:
                GLib.idle_add(self.homestack.set_visible_child_name, "fixapt")
        else:
            GLib.idle_add(self.homestack.set_visible_child_name, "noserver")
            GLib.idle_add(self.noserverlabel.set_markup, "<b>{}\n\n{}\n\n{}: {}</b>".format(
                _("Could not connect to server."),
                self.Server.error_message,
                _("Server address"),
                self.Server.serverurl))

        GLib.idle_add(self.splashspinner.stop)
        GLib.idle_add(self.splashlabel.set_text, "")

        self.Logger.info("set_initial_home done.")

    def prepend_server_icons(self):
        icon_theme = Gtk.IconTheme.get_default()
        local_icons = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons"))
        local_images = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images"))
        installed_icons = "/usr/share/parslinux/parslinux-software/icons"
        if os.path.exists(local_images):
            icon_theme.prepend_search_path(local_images)
        if os.path.exists(local_icons):
            icon_theme.prepend_search_path(local_icons)
        if os.path.exists(installed_icons):
            icon_theme.prepend_search_path(installed_icons)
        if hasattr(self, "UserSettings"):
            icon_theme.prepend_search_path(self.UserSettings.app_icons_dir)
            icon_theme.prepend_search_path(self.UserSettings.cat_icons_dir)

    def package(self):
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Updating Cache")))
        self.Package = Package()
        if self.Package.updatecache():
            self.isbroken = False
            self.Package.getApps()
        else:
            self.isbroken = True
            self.Logger.warning("Error while updating Cache")

        self.Logger.info("package completed")

    def utils(self):
        self.Utils = Utils()
        desktop_env = self.Utils.get_desktop_env()
        desktop_env_vers = self.Utils.get_desktop_env_version(desktop_env)
        session = self.Utils.get_session_type()
        self.user_desktop_env = "{} {}, {}".format(desktop_env, desktop_env_vers, session)

    def usersettings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.create_default_config()
        self.UserSettings.read_config()

        self.Logger.info(f"config_animations: {self.UserSettings.config_animations}")
        self.Logger.info(f"config_only_available: {self.UserSettings.config_only_available}")
        self.Logger.info(f"config_gnome_comments: {self.UserSettings.config_gnome_comments}")
        self.Logger.info(f"config_dark_theme: {self.UserSettings.config_dark_theme}")
        self.Logger.info(f"config_auto_apt_update: {self.UserSettings.config_auto_apt_update}")
        self.Logger.info(f"config_last_apt_update: {self.UserSettings.config_last_apt_update}")
        self.Logger.info(f"config_force_apt_update_time: {self.UserSettings.config_force_apt_update_time}")

    def server(self):
        self.Server = Server()

        conffile = "/etc/parslinux/parslinux-software.conf"
        local_conf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "parslinux-software.conf")
        if not os.path.exists(conffile) and os.path.exists(local_conf):
            conffile = local_conf

        self.repo_perm = 1
        self.myapps_perm = 1
        try:
            if os.path.exists(conffile):
                conf = open(os.path.join(conffile), "r").read()
                # strip all whitespaces to get more accurate results
                conf = conf.replace(" ", "")

                for line in conf.splitlines():
                    if not line.startswith("#"):
                        if line.startswith("server="):
                            self.Server.serverurl = line.split("server=")[1]
                        if line.startswith("repo="):
                            self.repo_perm = line.split("repo=")[1]
                        if line.startswith("myapps="):
                            self.myapps_perm = line.split("myapps=")[1]
        except Exception as e:
            self.Logger.exception("{}".format(e))

        if not self.Server.serverurl:
            self.Server.serverurl = "https://flathub.org/api/v2"
        else:
            self.Logger.info("{}".format("server url getted from new type config"))

        try:
            self.repo_perm = int(self.repo_perm)
        except:
            self.Logger.warning("repo key's value must be int. 1 or 0. So setting to default value 1")
            self.repo_perm = 1

        try:
            self.myapps_perm = int(self.myapps_perm)
        except:
            self.Logger.warning("myapps_perm key's value must be int. 1 or 0. So setting to default value 1")
            self.myapps_perm = 1

        self.Logger.info("server url: {}".format(self.Server.serverurl))
        self.Logger.info("repo permission: {}".format(self.repo_perm))
        self.Logger.info("myapps permission: {}".format(self.myapps_perm))

        # self.Server.ServerAppsURLControlCB = self.ServerAppsURLControlCB
        self.Server.ServerHashesCB = self.ServerHashesCB
        self.Server.ServerFilesCB = self.ServerFilesCB

        # self.Logger.info("Controlling server")
        # GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Controlling server")))
        # self.Server.control_server(self.Server.serverurl + "/api/v2/test")

        self.Logger.info("Controlling server hashes")
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Controlling server hashes")))
        self.Server.get_hashes(self.Server.serverurl + self.Server.serverhash)

        self.Logger.info("server func done")

    def update_offline_banner(self):
        is_offline = getattr(self.Server, "is_offline", False) or not self.Server.connection
        ui_home_box = getattr(self, "ui_parslinux_home_box", None)
        if not ui_home_box and hasattr(self, "GtkBuilder"):
            ui_home_box = self.GtkBuilder.get_object("ui_parslinux_home_box")
            if ui_home_box:
                self.ui_parslinux_home_box = ui_home_box

        if not hasattr(self, "ui_offline_infobar") or self.ui_offline_infobar is None:
            if ui_home_box:
                self.ui_offline_infobar = Gtk.InfoBar()
                self.ui_offline_infobar.set_message_type(Gtk.MessageType.WARNING)
                content = self.ui_offline_infobar.get_content_area()
                msg_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
                icon = Gtk.Image.new_from_icon_name("network-offline-symbolic", Gtk.IconSize.BUTTON)
                lbl = Gtk.Label.new()
                lbl.set_markup("<b>{}</b> - {}".format(_("Offline Mode"), _("Network is unreachable. Showing cached and locally installed applications.")))
                lbl.set_line_wrap(True)
                msg_box.pack_start(icon, False, False, 0)
                msg_box.pack_start(lbl, False, False, 0)
                content.add(msg_box)
                ui_home_box.pack_start(self.ui_offline_infobar, False, False, 0)
                ui_home_box.reorder_child(self.ui_offline_infobar, 0)

        if hasattr(self, "ui_offline_infobar") and self.ui_offline_infobar:
            self.ui_offline_infobar.set_visible(is_offline)
            if is_offline:
                self.ui_offline_infobar.show_all()

    def afterServers(self):
        GLib.idle_add(self.update_offline_banner)
        GLib.idle_add(self.set_initial_home)
        GLib.idle_add(self.control_available_apps)
        GLib.idle_add(self.set_categories)
        GLib.idle_add(self.set_applications)
        GLib.idle_add(self.get_upgradables)
        GLib.idle_add(self.set_upgradables)
        GLib.idle_add(self.set_slider)
        GLib.idle_add(self.set_most_apps)
        GLib.idle_add(self.start_auto_apt_update_control)
        GLib.idle_add(self.control_software_update)

        GLib.idle_add(self.set_myapps)

    # def ServerAppsURLControlCB(self, status):
    #     self.Logger.info("ServerAppsURLControlCB : {}".format(status))
    #
    #     if not status:
    #         self.Server.serverurl = self.Server.serverurl.replace("https://", "http://")
    #         self.Logger.info("{}".format(self.Server.serverurl))
    #
    #     self.Logger.info("Controlling server hashes")
    #     GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Controlling server hashes")))
    #     self.Server.get_hashes(self.Server.serverurl + self.Server.serverhash)

    def ServerHashesCB(self, status, response=None):
        self.Logger.info("ServerHashesCB : {}".format(status))

        def compare_md5_re_download(local_file, server_md5):
            if not Path(local_file).exists():
                return True
            local_md5 = md5(open(local_file, "rb").read()).hexdigest()
            return local_md5 != server_md5

        if status:
            # download_apps = compare_md5_re_download(self.UserSettings.apps_dir + self.UserSettings.apps_archive, response["md5"]["apps"])
            download_apps = True
            # download_home = compare_md5_re_download(self.UserSettings.home_dir + self.UserSettings.home_archive, response["md5"]["home"])
            download_home = True

            download_icons = compare_md5_re_download(self.UserSettings.icons_dir + self.UserSettings.icons_archive, response["md5"]["icons"])
            download_images = compare_md5_re_download(self.UserSettings.images_dir + self.UserSettings.images_archive, response["md5"]["images"])
            download_cats = compare_md5_re_download(self.UserSettings.cats_dir + self.UserSettings.cats_archive, response["md5"]["cats"])

            self.Logger.info("download_apps: {}".format(download_apps))
            self.Logger.info("download_icons: {}".format(download_icons))
            self.Logger.info("download_images: {}".format(download_images))
            self.Logger.info("download_cats: {}".format(download_cats))
            self.Logger.info("download_home: {}".format(download_home))

            self.status_server_apps = not download_apps
            self.status_server_icons = not download_icons
            self.status_server_images = not download_images
            self.status_server_cats = not download_cats
            self.status_server_home = not download_home

            if download_apps or download_icons or download_images or download_cats or download_home:

                self.Logger.info("Getting application metadata from server")
                GLib.idle_add(self.splashlabel.set_markup,
                              "<b>{}</b>".format(_("Getting application metadata from server")))

                if download_apps:
                    self.Logger.info("Getting applications from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting applications from server")))

                    # self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_apps_archive,
                    #                      download_location=self.UserSettings.apps_dir + self.UserSettings.apps_archive,
                    #                      server_md5=response["md5"]["apps"], type="apps")
                    self.Server.get_file(url=self.Server.serverurl + self.Server.serverapps,
                                         download_location=self.UserSettings.apps_dir + self.UserSettings.apps_archive,
                                         type="apps", save_file=False)
                if download_icons:
                    self.Logger.info("Getting icons from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting icons from server")))

                    self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_icons_archive,
                                         download_location=self.UserSettings.icons_dir + self.UserSettings.icons_archive,
                                         server_md5=response["md5"]["icons"], type="icons")

                if download_images:
                    self.Logger.info("Getting images from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting icons from server")))

                    self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_images_archive,
                                         download_location=self.UserSettings.images_dir + self.UserSettings.images_archive,
                                         server_md5=response["md5"]["images"], type="images")

                if download_cats:
                    self.Logger.info("Getting categories from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting categories from server")))

                    self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_cats_archive,
                                         download_location=self.UserSettings.cats_dir + self.UserSettings.cats_archive,
                                         server_md5=response["md5"]["cats"], type="cats")
                if download_home:
                    self.Logger.info("Getting homepage from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting homepage from server")))
                    # self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_home_archive,
                    #                      download_location=self.UserSettings.home_dir + self.UserSettings.home_archive,
                    #                      server_md5=response["md5"]["home"], type="home")
                    self.Server.get_file(url=self.Server.serverurl + self.Server.serverhomepage,
                                         download_location=self.UserSettings.home_dir + self.UserSettings.home_archive,
                                         type="home", save_file=False)

            else:
                self.ServerFilesCB(True, "ok")
        else:
            if not self.connection_error_after:
                self.Server.connection = False
                GLib.idle_add(self.afterServers)
                self.connection_error_after = True

    def ServerFilesCB(self, status, type="", response=None):
        self.Logger.info("ServerFilesCB {} : {}".format(type, status))

        if status:
            if type == "apps":
                self.status_server_apps = True
                self.apps = dict(sorted(response.items(),
                                        key=lambda item: locale.strxfrm(item[1]["prettyname"][self.user_locale])))
                self.apps_full = self.apps.copy()
            elif type == "icons":
                self.status_server_icons = True
            elif type == "images":
                self.status_server_images = True
            elif type == "cats":
                self.status_server_cats = True
            elif type == "home":
                self.status_server_home = True
                self.Server.editor_app_list = response.get("editor_apps", [])
                self.Server.slider_app_list = response.get("slider_apps", [])
                self.Server.most_down_app_list = response.get("most_down_apps", [])
                self.Server.trend_app_list = response.get("trend_apps", [])
                self.Server.recent_app_list = response.get("recent_apps", [])
                pass
                self.Server.blocked_gnome_reviews = response.get("blocked_gnome_reviews", [])
                self.Server.apt_uptime = response.get("apt_uptime", self.Server.apt_uptime)
                self.slider_auto_time = response.get("slider_auto_time", self.slider_auto_time)
                self.slider_pause_time = response.get("slider_pause_time", self.slider_pause_time)
                self.slider_slogan_max_chars = response.get("slider_slogan_max_chars", self.slider_slogan_max_chars)
                self.server_cat_all = response.get("cat_all") or {}
                self.home_trend_count = response.get("home_trend_count", self.home_trend_count)
                self.home_most_down_count = response.get("home_most_down_count", self.home_most_down_count)
                self.home_recent_count = response.get("home_recent_count", self.home_recent_count)
                self.important_packages = response.get("important_packages") or self.important_packages
                self.i386_packages = response.get("i386_packages") or self.i386_packages

            if self.status_server_apps and self.status_server_icons and self.status_server_images and self.status_server_cats and self.status_server_home:

                with open(self.UserSettings.cats_dir + self.UserSettings.cats_file, 'r', encoding='utf-8') as f:
                    response = json.load(f)
                    self.cats = response.get("categories", [])

                self.prepend_server_icons()

                self.Logger.info("Preparing the application interface")
                GLib.idle_add(self.splashlabel.set_markup,
                              "<b>{}</b>".format(_("Preparing the application interface")))

                self.Server.connection = not getattr(self.Server, "is_offline", False)
                GLib.idle_add(self.afterServers)
        else:
            if not self.connection_error_after:
                self.Server.connection = False
                GLib.idle_add(self.afterServers)
                self.connection_error_after = True

    # def controlServer(self):
    #     if self.Server.connection:
    #         self.Logger.info("Controlling {}".format(self.Server.serverurl))
    #         self.AppDetail.control(self.Server.serverurl + "/api/v2/test")
    #         self.AppRequest.control(self.Server.serverurl + "/api/v2/test")

    def set_applications(self, force=False):
        self.Logger.info(f"in set_applications (force={force})")
        if not hasattr(self, "_flowbox_app_ids"):
            self._flowbox_app_ids = set()

        # If FlowBox is already populated and this is not a forced reload,
        # just append any apps that are not yet in the flowbox, then invalidate filter.
        if not force and self._flowbox_app_ids:
            missing = [details for app, details in self.apps.items() if app not in self._flowbox_app_ids]
            if missing:
                GLib.idle_add(self._append_apps_to_flowbox, missing)
            else:
                GLib.idle_add(self.ui_parslinuxapps_flowbox.invalidate_filter)
            return

        self._set_apps_token = getattr(self, "_set_apps_token", 0) + 1
        current_token = self._set_apps_token

        def _clear_and_load():
            if not self.ui_parslinuxapps_flowbox:
                return False
            for row in list(self.ui_parslinuxapps_flowbox.get_children()):
                self.ui_parslinuxapps_flowbox.remove(row)
            self._flowbox_app_ids.clear()

            if not getattr(self, "Server", None) or not getattr(self.Server, "connection", False) or not self.apps:
                return False

            items = list(self.apps.items())
            INITIAL_BATCH = 36
            first_batch = items[:INITIAL_BATCH]
            remainder = items[INITIAL_BATCH:]

            for app, details in first_batch:
                listbox = self.create_app_widget(app, details)
                self._flowbox_app_ids.add(app)
                self.ui_parslinuxapps_flowbox.insert(listbox, -1)

            self.ui_parslinuxapps_flowbox.show_all()
            self.ui_parslinuxapps_flowbox.invalidate_filter()

            if remainder:
                self._load_next_apps_chunk(remainder, 0, current_token)
            return False

        GLib.idle_add(_clear_and_load)
        self.Logger.info("set_applications done")

    def _append_apps_to_flowbox(self, app_list):
        if not self.ui_parslinuxapps_flowbox or not app_list:
            return False
        if not hasattr(self, "_flowbox_app_ids"):
            self._flowbox_app_ids = set()

        added_any = False
        for item in app_list:
            app_name = item.get("name") if isinstance(item, dict) else item
            if not app_name or app_name in self._flowbox_app_ids:
                continue
            details = item if isinstance(item, dict) else (self.apps_full.get(app_name) if hasattr(self, "apps_full") else None)
            listbox = self.create_app_widget(app_name, details)
            self._flowbox_app_ids.add(app_name)
            self.ui_parslinuxapps_flowbox.insert(listbox, -1)
            added_any = True

        if added_any:
            self.ui_parslinuxapps_flowbox.show_all()
        self.ui_parslinuxapps_flowbox.invalidate_filter()
        return False

    def _load_next_apps_chunk(self, remaining_items, start_idx, token):
        if token != getattr(self, "_set_apps_token", None):
            return False

        CHUNK_SIZE = 24
        end_idx = min(start_idx + CHUNK_SIZE, len(remaining_items))
        chunk = remaining_items[start_idx:end_idx]

        if not hasattr(self, "_flowbox_app_ids"):
            self._flowbox_app_ids = set()

        for app, details in chunk:
            if app not in self._flowbox_app_ids:
                listbox = self.create_app_widget(app, details)
                self._flowbox_app_ids.add(app)
                self.ui_parslinuxapps_flowbox.insert(listbox, -1)

        self.ui_parslinuxapps_flowbox.show_all()
        self.ui_parslinuxapps_flowbox.invalidate_filter()

        if end_idx < len(remaining_items):
            GLib.idle_add(self._load_next_apps_chunk, remaining_items, end_idx, token, priority=GLib.PRIORITY_LOW)
        return False

    def parslinuxapps_sort_func(self, row1, row2):
        try:
            lb1 = row1.get_child() or (row1.get_children()[0] if row1.get_children() else None)
            lb2 = row2.get_child() or (row2.get_children()[0] if row2.get_children() else None)
            if not lb1 or not lb2:
                return 0

            app1 = getattr(lb1, "app_name", "")
            d1 = getattr(lb1, "app_details", None) or (self.apps_full.get(app1, {}) if hasattr(self, "apps_full") else {})
            app2 = getattr(lb2, "app_name", "")
            d2 = getattr(lb2, "app_details", None) or (self.apps_full.get(app2, {}) if hasattr(self, "apps_full") else {})

            mode = getattr(self, "_current_sort_mode", 0)
            if mode == 0:  # Name
                name1 = d1.get("prettyname", {}) if isinstance(d1, dict) else {}
                n1 = name1.get(self.user_locale, name1.get("en", app1)) if isinstance(name1, dict) else str(name1 or app1)
                name2 = d2.get("prettyname", {}) if isinstance(d2, dict) else {}
                n2 = name2.get(self.user_locale, name2.get("en", app2)) if isinstance(name2, dict) else str(name2 or app2)
                return 1 if locale.strxfrm(str(n1)) > locale.strxfrm(str(n2)) else -1
            elif mode == 1:  # Download
                dl1 = (d1.get("download", 0) if isinstance(d1, dict) else 0, d1.get("rate_average", 0) if isinstance(d1, dict) else 0)
                dl2 = (d2.get("download", 0) if isinstance(d2, dict) else 0, d2.get("rate_average", 0) if isinstance(d2, dict) else 0)
                return -1 if dl1 > dl2 else (1 if dl1 < dl2 else 0)
            elif mode == 2:  # Popularity
                pop1 = (d1.get("popularity", d1.get("rate_average", 0)) if isinstance(d1, dict) else 0, d1.get("download", 0) if isinstance(d1, dict) else 0)
                pop2 = (d2.get("popularity", d2.get("rate_average", 0)) if isinstance(d2, dict) else 0, d2.get("download", 0) if isinstance(d2, dict) else 0)
                return -1 if pop1 > pop2 else (1 if pop1 < pop2 else 0)
            elif mode == 3:  # Last added / Date
                date1 = d1.get("date", "") if isinstance(d1, dict) else ""
                date2 = d2.get("date", "") if isinstance(d2, dict) else ""
                return -1 if str(date1) > str(date2) else (1 if str(date1) < str(date2) else 0)
            return 0
        except Exception:
            return 0

    def create_app_widget(self, app, details=None, number=0, repo_app=False):

        if repo_app:
            details = {"name": app, "icon_name": "ps-repo-package-symbolic",
                       "description": self.Package.adv_description(app), "repo_app": True}

        if details and details.get("icon") and os.path.exists(str(details.get("icon"))):
            app_icon = Gtk.Image.new_from_file(details["icon"])
        else:
            app_icon = Gtk.Image.new_from_icon_name(app if not repo_app else "ps-repo-package-symbolic", Gtk.IconSize.DND)
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("parslinux-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        prettyname = "{}".format(self.get_pretty_name_from_app_name(app) if not repo_app else app)

        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(prettyname))
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23 if number==0 else 21)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)
        app_name.props.halign = Gtk.Align.START

        action_button = Gtk.Button.new()
        action_button.connect("clicked", self.app_widget_action_clicked)
        action_button.props.halign = Gtk.Align.END
        action_button.props.valign = Gtk.Align.CENTER
        action_button.set_hexpand(True)
        action_button.set_size_request(77, -1)
        if hasattr(self, "app_action_buttons"):
            self.app_action_buttons.setdefault(app, []).append(action_button)

        action_button_label = Gtk.Label.new()
        action_button_label.set_line_wrap(False)
        action_button_label.set_justify(Gtk.Justification.LEFT)
        action_button_label.set_max_width_chars(6)
        action_button_label.set_ellipsize(Pango.EllipsizeMode.END)

        is_installed = self.Package.isinstalled(app) if getattr(self, "Package", None) else False
        is_upgradable = self.Package.is_upgradable(app) if getattr(self, "Package", None) else False
        is_openable = self.get_desktop_filename_from_app_name(app) != ""
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

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(GLib.markup_escape_text(
            self.get_sub_category_name_from_app_name(app), -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(23 if number==0 else 21)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)
        summary_label.set_margin_start(1)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)
        box_app.set_margin_end(8)

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 16)
        if number != 0:
            number_label = Gtk.Label.new()
            number_label.set_markup("{}".format(number))
            number_label.props.halign = Gtk.Align.CENTER
            number_label.props.valign = Gtk.Align.CENTER
            box_h.pack_start(number_label, False, True, 0)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_start(action_button, False, True, 0)
        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        if 1024 < self.display_width <= 1370:
            bottom_separator.set_size_request(333, -1)
        bottom_separator.get_style_context().add_class("parslinux-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect("row-activated", self.on_app_listbox_row_activated if not repo_app else self.on_repoapp_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        listbox_row.add(box)
        listbox_row.name = {app: details} if details else app
        listbox.add(listbox_row)
        listbox.get_style_context().add_class("parslinux-software-listbox-mostdown")

        listbox.app_name = app
        listbox.app_details = details or (self.apps_full.get(app, {}) if hasattr(self, "apps_full") else {})
        return listbox

    def set_most_apps(self):
        # GLib.idle_add(lambda: self.ui_mostdown_flowbox.foreach(lambda child: self.ui_mostdown_flowbox.remove(child)))
        # GLib.idle_add(lambda: self.ui_recent_flowbox.foreach(lambda child: self.ui_recent_flowbox.remove(child)))
        # GLib.idle_add(lambda: self.ui_editor_flowbox.foreach(lambda child: self.ui_editor_flowbox.remove(child)))

        if self.Server.connection:
            self.Logger.info("in set_most_apps")
            GLib.idle_add(self.set_trend_apps)
            GLib.idle_add(self.set_editor_apps)
            GLib.idle_add(self.set_mostdown_apps)
            GLib.idle_add(self.set_recent_apps)

    def set_editor_apps(self):
        self.Logger.info("in set_editor_apps")

        GLib.idle_add(lambda: self.ui_editor_flowbox.foreach(lambda child: self.ui_editor_flowbox.remove(child)))

        for editor_app in self.Server.editor_app_list:

            editor_app_name = editor_app["name"]
            editor_app_pretty_name = self.get_pretty_name_from_app_name(editor_app_name)
            editor_app_sub_categoy = self.get_sub_category_name_from_app_name(editor_app_name)

            app_image = Gtk.Image.new()
            app_image.set_pixel_size(200)
            app_image.set_hexpand(True)
            app_image.props.halign = Gtk.Align.FILL

            css = """
            .parslinux-software-editor {{
                background-image: url("{}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: 8px;
            }}
            """.format(os.path.join(self.UserSettings.editor_images_dir, "{}.png".format(editor_app_name)))
            style_provider = Gtk.CssProvider()
            style_provider.load_from_data(str.encode(css))
            app_image.get_style_context().add_class("parslinux-software-editor")
            app_image.get_style_context().add_provider(style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            app_name = Gtk.Label.new()
            app_name.set_markup("<b>{}</b>".format(editor_app_pretty_name))
            app_name.set_line_wrap(False)
            app_name.set_justify(Gtk.Justification.LEFT)
            app_name.set_max_width_chars(23)
            app_name.set_ellipsize(Pango.EllipsizeMode.END)
            app_name.props.halign = Gtk.Align.START

            app_icon = Gtk.Image.new_from_icon_name(editor_app_name, Gtk.IconSize.DND)
            app_icon.set_pixel_size(32)
            app_icon.get_style_context().add_class("parslinux-software-mostapp-icon")
            app_icon.props.halign = Gtk.Align.CENTER
            app_icon.props.valign = Gtk.Align.CENTER

            action_button = Gtk.Button.new()
            action_button.connect("clicked", self.app_widget_action_clicked)
            action_button.props.halign = Gtk.Align.END
            action_button.props.valign = Gtk.Align.CENTER
            action_button.set_hexpand(True)
            action_button.set_size_request(77, -1)
            if hasattr(self, "app_action_buttons"):
                self.app_action_buttons.setdefault(editor_app_name, []).append(action_button)

            action_button_label = Gtk.Label.new()
            action_button_label.set_line_wrap(False)
            action_button_label.set_justify(Gtk.Justification.LEFT)
            action_button_label.set_max_width_chars(6)
            action_button_label.set_ellipsize(Pango.EllipsizeMode.END)

            is_installed = self.Package.isinstalled(editor_app_name)
            is_upgradable = self.Package.is_upgradable(editor_app_name)
            is_openable = self.get_desktop_filename_from_app_name(editor_app_name) != ""
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

            summary_label = Gtk.Label.new()
            summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(editor_app_sub_categoy))
            summary_label.props.halign = Gtk.Align.START
            summary_label.set_line_wrap(False)
            summary_label.set_max_width_chars(22)
            summary_label.set_ellipsize(Pango.EllipsizeMode.END)

            box_v = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
            box_v.props.valign = Gtk.Align.CENTER
            box_v.pack_start(app_name, False, True, 0)
            box_v.pack_start(summary_label, False, True, 0)
            box_v.set_margin_end(12)

            box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box_h.pack_start(app_icon, False, True, 0)
            box_h.pack_start(box_v, False, True, 0)
            box_h.pack_start(action_button, False, True, 0)
            box_h.set_margin_start(5)
            box_h.set_margin_end(5)
            box_h.set_margin_top(5)
            box_h.set_margin_bottom(5)

            bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
            bottom_separator.props.valign = Gtk.Align.END
            GLib.idle_add(bottom_separator.get_style_context().add_class, "parslinux-software-mostdown-bottom-seperator")

            box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
            box.pack_start(app_image, False, True, 0)
            box.pack_start(box_h, True, True, 0)
            box.pack_start(bottom_separator, True, True, 0)
            box.set_margin_start(5)
            box.set_margin_end(5)
            box.set_margin_top(5)

            listbox = Gtk.ListBox.new()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            listbox.connect("row-activated", self.on_app_listbox_row_activated)
            listbox_row = Gtk.ListBoxRow()
            GLib.idle_add(listbox_row.add, box)
            listbox_row.name = editor_app_name
            GLib.idle_add(listbox.add, listbox_row)

            GLib.idle_add(listbox.get_style_context().add_class, "parslinux-software-listbox-mostdown")
            GLib.idle_add(self.ui_editor_flowbox.insert, listbox, -1)

        GLib.idle_add(self.ui_editor_flowbox.show_all)

    def set_trend_apps(self):
        self.Logger.info("in set_trend_apps")
        GLib.idle_add(lambda: self.ui_trend_flowbox.foreach(lambda child: self.ui_trend_flowbox.remove(child)))
        counter = 0
        for app in self.Server.trend_app_list[:self.home_trend_count]:
            counter += 1
            listbox = self.create_app_widget(app["name"], None, counter)
            GLib.idle_add(self.ui_trend_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_trend_flowbox.show_all)

        GLib.idle_add(lambda: self.ui_trendapps_flowbox.foreach(lambda child: self.ui_trendapps_flowbox.remove(child)))
        counter = 0
        for app in self.Server.trend_app_list:
            counter += 1
            listbox = self.create_app_widget(app["name"], None, counter)
            GLib.idle_add(self.ui_trendapps_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_trendapps_flowbox.show_all)

    def set_mostdown_apps(self):
        self.Logger.info("in set_mostdown_apps")
        GLib.idle_add(lambda: self.ui_mostdown_flowbox.foreach(lambda child: self.ui_mostdown_flowbox.remove(child)))
        for app in self.Server.most_down_app_list[:self.home_most_down_count]:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_mostdown_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_mostdown_flowbox.show_all)

        GLib.idle_add(lambda: self.ui_mostdownapps_flowbox.foreach(lambda child: self.ui_mostdownapps_flowbox.remove(child)))
        for app in self.Server.most_down_app_list:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_mostdownapps_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_mostdownapps_flowbox.show_all)

    def set_recent_apps(self):
        self.Logger.info("in set_recent_apps")
        GLib.idle_add(lambda: self.ui_recent_flowbox.foreach(lambda child: self.ui_recent_flowbox.remove(child)))
        for app in self.Server.recent_app_list[:self.home_recent_count]:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_recent_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_recent_flowbox.show_all)

        GLib.idle_add(lambda: self.ui_recentapps_flowbox.foreach(lambda child: self.ui_recentapps_flowbox.remove(child)))
        for app in self.Server.recent_app_list:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_recentapps_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_recentapps_flowbox.show_all)

    def on_app_listbox_row_activated(self, listbox, row):
        # unselect the flowbox
        GLib.idle_add(listbox.get_parent().get_parent().unselect_all)
        self.set_app_details_page(row.name)

    def on_repoapp_listbox_row_activated(self, listbox, row):
        # unselect the flowbox
        GLib.idle_add(listbox.get_parent().get_parent().unselect_all)
        self.set_app_details_page(row.name, source=2)

    def get_pretty_name_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return name

        pretty = details.get("prettyname", {})
        return pretty.get(self.user_locale) or pretty.get("en") or name

    def get_category_name_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return _("Unknown")

        category_list = details.get("category") or []
        if not category_list:
            return _("Unknown")

        value = category_list[0].get(self.user_locale) or category_list[0].get("en") or _("Unknown")

        return value.title()

    def get_sub_category_name_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return ""

        subcat_list = details.get("subcategory") or []
        if not subcat_list:
            return ""

        subcat = subcat_list[0]
        value = subcat.get(self.user_locale) or subcat.get("en") or ""

        return value.title()

    def get_description_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return _("Unknown")

        desc = details.get("description", {})
        return desc.get(self.user_locale) or desc.get("en") or _("Unknown")

    def get_desktop_filename_from_app_name(self, name):
        if hasattr(self, "FlatpakManager") and self.FlatpakManager.is_installed(name):
            return f"{name}.desktop"
        details = self.apps_full.get(name)
        return details.get("desktop") if details else ""

    def get_gnome_desktop_filename_from_app_name(self, name):
        details = self.apps_full.get(name)
        return details.get("gnomename") if details else ""

    def onDestroy(self, widget):
        self.MainWindow.destroy()

    def set_animations(self):
        if self.UserSettings.config_animations:
            trans_type = Gtk.StackTransitionType.CROSSFADE
            duration = 200
        else:
            trans_type = Gtk.StackTransitionType.NONE
            duration = 0

        stacks = [
            self.mainstack,
            self.homestack,
            self.bottomstack,
            self.ui_right_stack,
            self.ui_slider_stack,
            self.ui_parslinuxapps_title_stack,
            self.ui_ad_action_stack,
            self.ui_ad_top_stack,
            self.ui_queue_stack,
            self.ui_tryfix_stack,
            self.ui_comment_main_stack,
            self.ui_comment_mid_stack,
            self.ui_comment_mid_editable_stack,
            self.ui_comment_bottom_stack,
            self.ui_image_stack,
            self.ui_myapp_pop_stack,
            self.ui_suggest_main_stack,
        ]

        for stack in stacks:
            if stack:
                stack.set_transition_type(trans_type)
                stack.set_transition_duration(duration)

    def set_button_class(self, button, state):
        '''
        state 0 = app is not installed
        state 1 = app is installed
        state 2 = app is not found
        state 3 = app is upgradable
        state 4 = app is openable
        '''
        if state == 1:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("openup-action"):
                button.get_style_context().remove_class("openup-action")
            button.get_style_context().add_class("destructive-action")
            button.set_sensitive(True)
        elif state == 0:
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            if button.get_style_context().has_class("openup-action"):
                button.get_style_context().remove_class("openup-action")
            button.get_style_context().add_class("suggested-action")
            button.set_sensitive(True)
        elif state == 2:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            if button.get_style_context().has_class("openup-action"):
                button.get_style_context().remove_class("openup-action")
            button.set_sensitive(False)
        elif state == 3:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            button.get_style_context().add_class("openup-action")
            button.set_sensitive(True)
        elif state == 4:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            button.get_style_context().add_class("openup-action")
            button.set_sensitive(True)

    def on_main_key_press_event(self, widget, event):
        if self.mainstack.get_visible_child_name() == "home":
            if self.homestack.get_visible_child_name() == "parslinuxhome":

                entry = self.ui_top_searchentry
                buf = entry.get_buffer()

                if entry.is_focus():
                    return False

                if event.string.isdigit() or event.string.isalpha():
                    buf.delete_text(0, -1)
                    entry.grab_focus()
                    buf.insert_text(0, event.string, -1)
                    entry.set_position(-1)
                    return True

        return False

    def on_menu_settings_clicked(self, button=None):
        if hasattr(self, "ui_headermenu_button") and self.ui_headermenu_button:
            self.ui_headermenu_button.grab_focus()
        self.ui_right_stack_navigate_to("settings")
        if hasattr(self, "ui_headermenu_popover") and self.ui_headermenu_popover:
            self.ui_headermenu_popover.popdown()

        self.ui_leftcats_listbox.unselect_all()
        self.ui_leftupdates_listbox.unselect_all()
        if button is not None:
            self.ui_leftinstalled_listbox.unselect_all()

        self.UserSettings.read_config()

        self.ui_settings_animations_switch.set_state(self.UserSettings.config_animations)
        self.ui_settings_available_switch.set_state(self.UserSettings.config_only_available)
        self.ui_settings_gcomments_switch.set_state(self.UserSettings.config_gnome_comments)
        self.ui_settings_dark_switch.set_state(self.UserSettings.config_dark_theme)
        self.ui_settings_update_switch.set_state(self.UserSettings.config_auto_apt_update)

        self.control_groups()
        self.set_cache_size()

        self.set_settings_tooltips()
        self.load_flatpak_remotes_ui()

    def load_flatpak_remotes_ui(self):
        ui_settings_box = getattr(self, "ui_settings_box", None)
        if not ui_settings_box and hasattr(self, "GtkBuilder"):
            ui_settings_box = self.GtkBuilder.get_object("ui_settings_box")
            if ui_settings_box:
                self.ui_settings_box = ui_settings_box

        if not ui_settings_box:
            return

        if not hasattr(self, "ui_settings_remotes_box") or self.ui_settings_remotes_box is None:
            remotes_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
            remotes_box.set_margin_top(18)
            remotes_box.set_margin_bottom(18)

            sep = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
            remotes_box.pack_start(sep, False, False, 6)

            header_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            icon = Gtk.Image.new_from_icon_name("folder-remote-symbolic", Gtk.IconSize.BUTTON)
            title = Gtk.Label.new()
            title.set_markup("<b>{}</b>".format(_("Flatpak Yazılım Kaynakları (Depolar)")))
            title.props.halign = Gtk.Align.START

            add_btn = Gtk.Button.new_with_label(_("Yeni Depo Ekle"))
            add_btn.get_style_context().add_class("suggested-action")
            add_btn.props.valign = Gtk.Align.CENTER
            add_btn.connect("clicked", lambda b: self.show_add_remote_dialog())

            header_h.pack_start(icon, False, False, 0)
            header_h.pack_start(title, False, False, 0)
            header_h.pack_end(add_btn, False, False, 0)
            remotes_box.pack_start(header_h, False, False, 6)

            listbox = Gtk.ListBox.new()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            listbox.get_style_context().add_class("parslinux-software-listbox-mostdown")
            remotes_box.pack_start(listbox, False, False, 4)

            self.ui_settings_remotes_box = remotes_box
            self.ui_remotes_listbox = listbox
            ui_settings_box.pack_start(remotes_box, False, False, 0)

        for child in self.ui_remotes_listbox.get_children():
            self.ui_remotes_listbox.remove(child)

        remotes = []
        if hasattr(self, "FlatpakManager"):
            remotes = self.FlatpakManager.get_remotes()

        if not remotes:
            row = Gtk.ListBoxRow()
            empty_lbl = Gtk.Label.new()
            empty_lbl.set_markup("<span color='gray'>{}</span>".format(_("Tanımlı Flatpak deposu bulunamadı.")))
            empty_lbl.set_margin_top(12)
            empty_lbl.set_margin_bottom(12)
            row.add(empty_lbl)
            self.ui_remotes_listbox.add(row)
        else:
            for rem in remotes:
                row = Gtk.ListBoxRow()
                row_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
                row_box.set_margin_start(12)
                row_box.set_margin_end(12)
                row_box.set_margin_top(8)
                row_box.set_margin_bottom(8)

                rem_icon = Gtk.Image.new_from_icon_name("network-server-symbolic", Gtk.IconSize.BUTTON)

                info_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
                info_box.props.halign = Gtk.Align.START
                name_lbl = Gtk.Label.new()
                name_lbl.set_markup("<b>{}</b> ({})".format(GLib.markup_escape_text(rem["title"], -1), GLib.markup_escape_text(rem["name"], -1)))
                name_lbl.props.halign = Gtk.Align.START

                url_lbl = Gtk.Label.new()
                url_lbl.set_markup("<small><span color='gray'>{}</span></small>".format(GLib.markup_escape_text(rem["url"], -1)))
                url_lbl.props.halign = Gtk.Align.START
                url_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                url_lbl.set_max_width_chars(45)

                info_box.pack_start(name_lbl, False, False, 0)
                info_box.pack_start(url_lbl, False, False, 0)

                scope_badge = Gtk.Label.new()
                scope_text = _("Kullanıcı") if rem["scope"] == "user" else _("Sistem")
                scope_badge.set_markup(f"<small><b>[{scope_text}]</b></small>")
                scope_badge.props.valign = Gtk.Align.CENTER

                row_box.pack_start(rem_icon, False, False, 0)
                row_box.pack_start(info_box, True, True, 0)
                row_box.pack_end(scope_badge, False, False, 4)

                if rem["scope"] == "user":
                    del_btn = Gtk.Button.new()
                    del_btn.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
                    del_btn.set_relief(Gtk.ReliefStyle.NONE)
                    del_btn.set_tooltip_text(_("Bu depoyu kaldır"))
                    del_btn.props.valign = Gtk.Align.CENTER
                    r_name = rem["name"]
                    del_btn.connect("clicked", lambda b, rn=r_name: self.on_remove_remote_clicked(rn))
                    row_box.pack_end(del_btn, False, False, 0)

                row.add(row_box)
                self.ui_remotes_listbox.add(row)

        self.ui_settings_remotes_box.show_all()

    def on_remove_remote_clicked(self, remote_name):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Depoyu Kaldır"),
        )
        dialog.format_secondary_text(_("'{}' deposunu sistemden silmek istediğinize emin misiniz?").format(remote_name))
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            if hasattr(self, "FlatpakManager"):
                success, msg = self.FlatpakManager.remove_remote(remote_name, is_user=True)
                if success:
                    self.notify(_("Depo Kaldırıldı"), _("'{}' deposu başarıyla silindi.").format(remote_name))
                    self.load_flatpak_remotes_ui()
                else:
                    self.notify(_("Hata"), msg)

    def show_add_remote_dialog(self):
        dialog = Gtk.Dialog(
            title=_("Yeni Flatpak Deposu Ekle"),
            transient_for=self.window,
            flags=0
        )
        dialog.add_buttons(
            _("İptal"), Gtk.ResponseType.CANCEL,
            _("Ekle"), Gtk.ResponseType.OK
        )
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_start(16)
        content_area.set_margin_end(16)
        content_area.set_margin_top(16)
        content_area.set_margin_bottom(16)

        preset_combo = Gtk.ComboBoxText()
        preset_combo.append("custom", _("Özel Depo (Custom URL)"))
        preset_combo.append("flathub_beta", "Flathub Beta (https://flathub.org/beta-repo/flathub-beta.flatpakrepo)")
        preset_combo.append("gnome_nightly", "GNOME Nightly (https://nightly.gnome.org/gnome-nightly.flatpakrepo)")
        preset_combo.append("flathub_official", "Flathub Resmî (https://dl.flathub.org/repo/flathub.flatpakrepo)")
        preset_combo.set_active(0)

        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("Örn: flathub-beta")

        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("https://...")

        presets = {
            "flathub_beta": ("flathub-beta", "https://flathub.org/beta-repo/flathub-beta.flatpakrepo"),
            "gnome_nightly": ("gnome-nightly", "https://nightly.gnome.org/gnome-nightly.flatpakrepo"),
            "flathub_official": ("flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"),
        }

        def on_preset_changed(combo):
            active_id = combo.get_active_id()
            if active_id in presets:
                p_name, p_url = presets[active_id]
                name_entry.set_text(p_name)
                url_entry.set_text(p_url)

        preset_combo.connect("changed", on_preset_changed)

        box_preset = Gtk.Box.new(Gtk.Orientation.VERTICAL, 4)
        box_preset.pack_start(Gtk.Label(label=_("Hazır Depo Şablonu:"), halign=Gtk.Align.START), False, False, 0)
        box_preset.pack_start(preset_combo, False, False, 0)

        box_name = Gtk.Box.new(Gtk.Orientation.VERTICAL, 4)
        box_name.pack_start(Gtk.Label(label=_("Depo Adı:"), halign=Gtk.Align.START), False, False, 0)
        box_name.pack_start(name_entry, False, False, 0)

        box_url = Gtk.Box.new(Gtk.Orientation.VERTICAL, 4)
        box_url.pack_start(Gtk.Label(label=_("Depo URL / .flatpakrepo Adresi:"), halign=Gtk.Align.START), False, False, 0)
        box_url.pack_start(url_entry, False, False, 0)

        content_area.pack_start(box_preset, False, False, 4)
        content_area.pack_start(box_name, False, False, 4)
        content_area.pack_start(box_url, False, False, 4)
        content_area.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            url = url_entry.get_text().strip()
            dialog.destroy()
            if name and url and hasattr(self, "FlatpakManager"):
                success, msg = self.FlatpakManager.add_remote(name, url, is_user=True)
                if success:
                    self.notify(_("Depo Eklendi"), _("'{}' deposu başarıyla sisteme kaydedildi.").format(name))
                    self.load_flatpak_remotes_ui()
                else:
                    self.notify(_("Depo Eklenemedi"), msg)
        else:
            dialog.destroy()

    def on_ui_back_button_clicked(self, button):
        # If there is no history, there is nowhere to go back to.
        if not self.stack_history:
            return

        # Get the previous page from history.
        previous = self.stack_history.pop()

        # Navigate back without recording this transition in history.
        # Using navigate_to ensures the back button visibility is updated.
        self.ui_right_stack_navigate_to(previous, record=False)

    def ui_right_stack_navigate_to(self, page_name, record=True):
        current = self.ui_right_stack.get_visible_child_name()

        # Do nothing if trying to navigate to the current page.
        if current == page_name:
            return

        # When moving forward (record=True), push the current page into history
        # unless it's already the last entry (prevents duplicates).
        if record and current:
            if not self.stack_history or self.stack_history[-1] != current:
                self.stack_history.append(current)

        # Perform the actual page switch.
        # Back navigation sets record=False to avoid polluting history.
        self.ui_right_stack.set_visible_child_name(page_name)

        # Update back button availability after the page change.
        self.update_back_button_visibility()

    def update_back_button_visibility(self):
        current = self.ui_right_stack.get_visible_child_name()

        # Disable the back button when on the root page (discover).
        self.ui_back_button.set_sensitive(current != "discover")

    def set_cache_size(self):
        cachedir = getattr(self.Server, "cachedir", None) or self.UserSettings.cache_dir
        cache_size = self.Utils.get_path_size(cachedir)
        self.Logger.info("{} : {} bytes".format(cachedir, cache_size))
        size_str = GLib.format_size(cache_size) if isinstance(cache_size, int) else (self.Package.beauty_size(cache_size) if getattr(self, "Package", None) else str(cache_size))
        self.ui_settings_cache_size_label.set_markup("<b>({})</b>".format(size_str))

    def control_groups(self):
        try:
            self.usergroups = [g.gr_name for g in grp.getgrall() if self.UserSettings.user_name in g.gr_mem]
        except Exception as e:
            self.Logger.exception("control_groups: {}".format(e))
            self.usergroups = []

        if self.usergroups:
            self.ui_settings_password_button.set_visible(True)
            if "parslinux-software" in self.usergroups:
                self.ui_settings_password_button.set_label(_("Deactivate"))
                self.set_button_class(self.ui_settings_password_button, 1)
            else:
                self.ui_settings_password_button.set_label(_("Activate"))
                self.set_button_class(self.ui_settings_password_button, 0)
            self.ui_settings_password_button.set_sensitive(True)
        else:
            self.ui_settings_password_button.set_visible(False)

    def set_settings_tooltips(self):
        if self.UserSettings.config_force_apt_update_time != 0:
            self.ui_settings_update_label.set_tooltip_text(
                "{} {} {}\n{}: {}\n\n{} ( {} )".format(
                    _("Allows the package manager cache to be updated again on the next application start if"),
                    self.displayTime(self.Server.apt_uptime),
                    _("have passed since the last successful update."),
                    _("Last successful update time is"),
                    datetime.fromtimestamp(self.UserSettings.config_last_apt_update),
                    _("The value in your configuration file is used as the wait time."),
                    self.displayTime(self.UserSettings.config_force_apt_update_time)
                ))
            apt_uptime = getattr(self.Server, "apt_uptime", 86400) if self.Server else 86400
            self.ui_settings_update_label.set_tooltip_text("{} {} {}\n{}: {}".format(
                _("Allows the package manager cache to be updated again on the next application start if"),
                self.displayTime(apt_uptime),
                _("have passed since the last successful update."),
                _("Last successful update time is"),
                datetime.fromtimestamp(self.UserSettings.config_last_apt_update)
            ))

    def on_menu_about_clicked(self, button):
        self.ui_headermenu_popover.popdown()
        self.aboutdialog.run()
        self.aboutdialog.hide()

    def on_ui_trend_seeall_eventbox_button_release_event(self, widget, event):
        self.ui_right_stack_navigate_to("trendapps")

    def on_ui_mostdown_seeall_eventbox_button_release_event(self, widget, event):
        self.ui_right_stack_navigate_to("mostdownapps")

    def on_ui_recent_seeall_eventbox_button_release_event(self, widget, event):
        self.ui_right_stack_navigate_to("recentapps")

    def displayTime(self, seconds, granularity=5):
        result = []
        intervals = (
            (_("weeks"), 604800),  # 60 * 60 * 24 * 7
            (_("days"), 86400),  # 60 * 60 * 24
            (_("hours"), 3600),  # 60 * 60
            (_("minutes"), 60),
            (_("seconds"), 1),
        )
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])

    def on_ui_settings_dark_switch_state_set(self, switch, state):
        user_config_dark = self.UserSettings.config_dark_theme
        if state != user_config_dark:
            self.Logger.info("Updating dark theme state as {}".format(state))
            self.UserSettings.write_config(DarkTheme=state)
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = state
            self.usersettings()

    def on_ui_settings_animations_switch_state_set(self, switch, state):
        user_config_animations = self.UserSettings.config_animations
        if state != user_config_animations:
            self.Logger.info("Updating animations state as {}".format(state))
            self.UserSettings.write_config(Animations=state)
            self.usersettings()

            if self.UserSettings.config_animations:
                self.start_slider_timer()
            else:
                self.stop_slider_timer()

            self.set_animations()

    def on_ui_settings_gcomments_switch_state_set(self, switch, state):
        user_config_gcomments = self.UserSettings.config_gnome_comments
        if state != user_config_gcomments:
            self.Logger.info("Updating gnome comments state as {}".format(state))
            self.UserSettings.write_config(GnomeComments=state)
            self.usersettings()

    def on_ui_settings_update_switch_state_set(self, switch, state):
        user_config_update = self.UserSettings.config_auto_apt_update
        if state != user_config_update:
            self.Logger.info("Updating auto apt update state as {}".format(state))
            self.UserSettings.write_config(AutoAptUpdate=state)
            self.usersettings()

    def on_ui_settings_available_switch_state_set(self, switch, state):
        user_config_available = self.UserSettings.config_only_available
        if state != user_config_available:
            self.Logger.info("Updating show available apps state")
            self.UserSettings.write_config(OnlyAvailableApps=state)
            self.usersettings()
            self.set_available_apps(available=state)
            GLib.idle_add(self.set_applications)

    def on_ui_settings_cache_button_clicked(self, button):
        state, message = self.Server.delete_cache()
        if state:
            self.ui_settings_cache_button.set_sensitive(False)
            self.ui_settings_cache_button.set_label(_("Cleared"))
            self.ui_settings_cache_info_label.set_markup(_("Cache files cleared, please close and reopen the application"))
        else:
            self.ui_settings_cache_button.set_sensitive(True)
            self.ui_settings_cache_button.set_label(_("Error"))
            self.ui_settings_cache_info_label.set_markup("{}".format(message))
        self.set_cache_size()

    def on_ui_settings_password_button_clicked(self, button):
        self.ui_settings_password_button.set_sensitive(False)
        self.ui_settings_password_info_label.set_text("")
        self.grouperrormessage = ""
        if "parslinux-software" in self.usergroups:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Group.py", "del",
                       self.UserSettings.user_name]
        else:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Group.py", "add",
                       self.UserSettings.user_name]
        self.group_process(command)

    def set_available_apps(self, available):
        self.apps = {
            app: details
            for app, details in self.apps_full.items()
            if (
                    (available and (self.Package.isinstalled(app) is not None or any(
                        code["name"] == self.UserSettings.user_codename for code in details["codename"])))
                    or
                    (not available)
            )
        }

    def on_bottomerrorbutton_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_retrybutton_clicked(self, button):
        self.connection_error_after = False
        self.mainstack.set_visible_child_name("splash")
        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()

    def on_bottominterrupt_fix_button_clicked(self, button):
        self.bottominterrupt_fix_button.set_sensitive(False)
        self.bottominterrupthide_button.set_sensitive(False)

        self.pop_interruptinfo_spinner.set_visible(True)
        self.pop_interruptinfo_spinner.start()

        self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("The process is in progress. Please wait...")))

        self.pop_interruptinfo_ok_button.set_visible(False)

        self.interruptpopover.set_relative_to(button)
        self.interruptpopover.popup()

        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py", "dpkgconfigure"]

        if not self.dpkgconfiguring:
            self.dpkgconfigure_vte_start_process(command)
            self.dpkgconfiguring = True
        else:
            self.Logger.info("dpkgconfiguring in progress")

    def on_pop_interruptinfo_ok_button_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)
        self.interruptpopover.popdown()

    def on_bottominterrupthide_button_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_bottomerrordetails_button_clicked(self, button):
        self.bottomerrordetails_popover.popup()

    def on_ui_tryfix_button_clicked(self, button):
        self.ui_tryfix_stack.set_visible_child_name("info")

    def on_ui_tryfix_confirm_button_clicked(self, button):
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py",
                   "fixapt"]
        self.ui_tryfix_stack.set_visible_child_name("main")
        self.ui_tryfix_button.set_sensitive(False)
        self.ui_tryfix_spinner.start()
        self.tryfix_vte_process(command)

    def on_ui_tryfix_cancel_button_clicked(self, button):
        self.ui_tryfix_stack.set_visible_child_name("main")

    def on_ui_tryfix_done_button_clicked(self, button):
        GLib.idle_add(self.afterServers)

    def update_vte_color(self, vte):
        style_context = self.MainWindow.get_style_context()
        background_color = style_context.get_background_color(Gtk.StateFlags.NORMAL);
        foreground_color = style_context.get_color(Gtk.StateFlags.NORMAL);
        vte.set_color_background(background_color)
        vte.set_color_foreground(foreground_color)

    def send_downloaded_request(self, appname):
        try:
            installed = self.Package.isinstalled(appname)
            if installed is None:
                installed = False
            version = self.Package.installed_version(appname)
            if version is None:
                version = ""
            dic = {"mac": self.mac, "app": appname, "installed": installed, "appversion": version,
                   "distro": self.user_distro_full}
            self.AppRequest.send(self.Server.serverurl + self.Server.serversenddownload, dic)
        except Exception as e:
            self.Logger.warning("send_downloaded_request Error")
            self.Logger.exception("{}".format(e))

    def control_myapps(self, actionedappname, actionedappdesktop, status, error, cachestatus):
        self.Logger.info("in control_myapps")
        if status == 0 and not error and cachestatus:
            if self.isinstalled:
                if self.isupgrade:
                    return
                self.Logger.info("{} removing from myapps".format(actionedappdesktop))
                desktop_id = actionedappdesktop.rsplit('/', 1)[-1]
                for fbc in self.ui_installedapps_flowbox:
                    # get desktop id from open button widget name
                    if fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].name == desktop_id:
                        if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                            self.Logger.info("in pop_myapp popdown")
                            self.ui_myapp_details_popover.set_relative_to(self.ui_installedapps_flowbox)
                            self.ui_myapp_details_popover.popdown()
                        self.ui_installedapps_flowbox.remove(fbc)
            else:
                self.Logger.info("{} adding to myapps".format(actionedappdesktop))
                valid, dic = self.Package.parse_desktopfile(os.path.basename(actionedappdesktop))
                if valid:
                    self.add_to_myapps_ui(dic)
                    GLib.idle_add(self.ui_installedapps_flowbox.show_all)
                    self.ui_installedapps_flowbox.set_sort_func(self.installedapps_sort_func)
            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in pop_myapp details status=0")
                self.ui_myapp_pop_uninstall_button.set_sensitive(False)
                self.ui_myapp_details_popover.popdown()
        else:
            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in pop_myapp details status!=0")
                self.ui_myapp_pop_uninstall_button.set_sensitive(True)

    def notify(self, message_summary="", message_body=""):
        try:
            if Notify.is_initted():
                Notify.uninit()

            if message_summary == "" and message_body == "":
                Notify.init(_("Pars Linux Software Center"))
                if self.isinstalled:
                    notification = Notify.Notification.new("{} {}".format(
                        self.get_pretty_name_from_app_name(self.inprogress_app_name),_("Updated") if self.isupgrade else _("Removed")))
                else:
                    notification = Notify.Notification.new("{} {}".format(
                        self.get_pretty_name_from_app_name(self.inprogress_app_name), _("Installed")))
                try:
                    notification.set_app_icon("parslinux-software")
                except AttributeError:
                    notification.set_image_from_pixbuf(
                        Gtk.IconTheme.get_default().load_icon("parslinux-software", 64, Gtk.IconLookupFlags(16)))
                except Exception as e:
                    self.Logger.exception("{}".format(e))
            else:
                Notify.init(_("Pars Linux Software Center"))
                notification = Notify.Notification.new(message_summary, message_body, "parslinux-software")
            notification.show()
        except Exception as e:
            self.Logger.exception("{}".format(e))

