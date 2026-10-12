import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango


class SliderMixin:
    """Slider ve ana sayfa afiş geçişleri için kontrolcü mixin'i."""

    def set_slider(self):
        if not self.Server.connection:
            return
        for child in list(self.ui_slider_stack.get_children()):
            self.ui_slider_stack.remove(child)

        stack_counter = 0
        for slider_app in self.Server.slider_app_list:

            slider_app_name = slider_app["name"]
            slider_app_pretty_name = slider_app["prettyname"].get(self.user_locale) or slider_app["prettyname"].get("en")
            slider_app_slogan = slider_app["slogan"].get(self.user_locale) or slider_app["slogan"].get("en")

            label_name = Gtk.Label.new()
            label_name.props.halign = Gtk.Align.START
            label_name.set_markup("<span color='white'><b>{}</b></span>".format(GLib.markup_escape_text(str(slider_app_pretty_name or ""), -1)))

            label_slogan = Gtk.Label.new()
            label_slogan.props.halign = Gtk.Align.START
            label_slogan.set_line_wrap(True)
            label_slogan.set_max_width_chars(self.slider_slogan_max_chars)
            label_slogan.set_lines(4)
            label_slogan.set_ellipsize(Pango.EllipsizeMode.END)
            label_slogan.set_markup("<span size='x-large' color='white'>{}</span>".format(GLib.markup_escape_text(str(slider_app_slogan or ""), -1)))

            vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
            vbox.props.valign = Gtk.Align.CENTER
            vbox.set_border_width(6)
            vbox.pack_start(label_name, False, False, 0)
            vbox.pack_start(label_slogan, False, False, 0)
            vbox.set_margin_start(24)

            hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            hbox.pack_start(vbox, True, True, 0)
            hbox.show_all()

            css = """
            .parslinux-software-slider {{
                background-image: url("{}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: right;
                border-radius: 8px;
            }}
            """.format(os.path.join(self.UserSettings.slider_images_dir, "{}.svg".format(slider_app_name)))

            style_provider = Gtk.CssProvider()
            style_provider.load_from_data(str.encode(css))

            flowbox = Gtk.FlowBox()
            flowbox.set_min_children_per_line(1)
            flowbox.set_max_children_per_line(1)
            flowbox.set_row_spacing(0)
            flowbox.set_column_spacing(0)
            flowbox.set_homogeneous(True)
            flowbox.connect("child-activated", self.on_slider_app_activated)

            flowbox_child = Gtk.FlowBoxChild()
            flowbox_child.name = slider_app_name
            flowbox_child.add(hbox)
            flowbox_child.set_size_request(-1, 200)
            flowbox_child.get_style_context().add_class("parslinux-software-slider")
            flowbox_child.get_style_context().add_provider(style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            flowbox.add(flowbox_child)

            self.ui_slider_stack.add_named(flowbox, "{}".format(stack_counter))
            stack_counter += 1

        # Slider back button
        btn_prev = Gtk.Button()
        btn_prev.set_image(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON))
        btn_prev.set_valign(Gtk.Align.END)
        btn_prev.set_halign(Gtk.Align.END)
        btn_prev.set_margin_end(50)
        btn_prev.set_margin_bottom(10)
        btn_prev.connect("clicked", self.on_ui_slider_left_button_clicked)
        GLib.idle_add(self.ui_slider_overlay.add_overlay, btn_prev)

        # Slider next button
        btn_next = Gtk.Button()
        btn_next.set_image(Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON))
        btn_next.set_valign(Gtk.Align.END)
        btn_next.set_halign(Gtk.Align.END)
        btn_next.set_margin_end(10)
        btn_next.set_margin_bottom(10)
        btn_next.connect("clicked", self.on_ui_slider_right_button_clicked)
        GLib.idle_add(self.ui_slider_overlay.add_overlay, btn_next)

        GLib.idle_add(self.ui_slider_overlay.show_all)

        if self.UserSettings.config_animations:
            self.start_slider_timer()

    def on_slider_app_activated(self, flow_box, child):
        self.set_app_details_page(child.name)

    def on_ui_slider_right_button_clicked(self, button):
        self.pause_auto_slider()
        self._slide_next_page()

    def on_ui_slider_left_button_clicked(self, button):
        self.pause_auto_slider()
        self._slide_prev_page()

    def _slide_next_page(self):
        slider_stack_len = len(self.ui_slider_stack.get_children())

        def get_next_page(page):
            for i in range(1, slider_stack_len + 1):
                if self.ui_slider_stack.get_child_by_name(str(page + i)) is not None:
                    return page + i
            return 0

        next_page = get_next_page(self.slider_current_page)
        self.ui_slider_stack.set_visible_child_name(str(next_page))
        self.slider_current_page = next_page

    def _slide_prev_page(self):
        slider_stack_len = len(self.ui_slider_stack.get_children())

        def get_prev_page(page):
            for i in range(1, slider_stack_len + 1):
                if self.ui_slider_stack.get_child_by_name(str(page - i)) is not None:
                    return page - i
            return slider_stack_len - 1

        prev_page = get_prev_page(self.slider_current_page)
        self.ui_slider_stack.set_visible_child_name(str(prev_page))
        self.slider_current_page = prev_page

    def _auto_slide(self):
        self._slide_next_page()
        return True

    def start_slider_timer(self):
        if not self.UserSettings.config_animations:
            return

        if self.slider_timer_id is None and not self.pause_active:
            self.slider_timer_id = GLib.timeout_add_seconds(self.slider_auto_time, self._auto_slide)

    def stop_slider_timer(self):
        if self.slider_timer_id is not None:
            GLib.source_remove(self.slider_timer_id)
            self.slider_timer_id = None

    def pause_auto_slider(self):
        self.stop_slider_timer()

        self.pause_active = True

        if self.slider_pause_id is not None:
            GLib.source_remove(self.slider_pause_id)

        self.slider_pause_id = GLib.timeout_add_seconds(self.slider_pause_time, self._resume_after_pause)

    def _resume_after_pause(self):
        self.pause_active = False
        self.slider_pause_id = None

        if self.UserSettings.config_animations:
            self.start_slider_timer()

        return False
