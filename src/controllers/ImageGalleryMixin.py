import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf


class ImageGalleryMixin:
    """Ekran görüntüleri, popover galeri ve resim etkileşimleri kontrolcü mixin'i."""

    def add_to_image_popover(self, pixbuf, uri):
        name = uri.rsplit("/", 1)[-1].split(".", 1)[0]
        self.image_original_pixbufs[name] = pixbuf.copy()

        image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.image_stack_names.append(name)

        GLib.idle_add(self.ui_image_stack.add_named, image, "{}".format(name))

    def round_corners(self, pixbuf, radius):
        width = pixbuf.get_width()
        height = pixbuf.get_height()

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        ctx.arc(radius, radius, radius, 3.1415, 3.1415 * 1.5)
        ctx.arc(width - radius, radius, radius, 3.1415 * 1.5, 0)
        ctx.arc(width - radius, height - radius, radius, 0, 3.1415 * 0.5)
        ctx.arc(radius, height - radius, radius, 3.1415 * 0.5, 3.1415)
        ctx.close_path()

        ctx.clip()
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        ctx.paint()

        new_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)
        return new_pixbuf

    def app_image_from_server(self, status, pixbuf=None, uri=None, app_name=""):
        self.Logger.info(
            f"app_image_from_server: status: {status}, "
            f"app_name: {app_name}, "
            f"ui_app_name: {self.ui_app_name}, "
            f"pixbuf: {'OK' if pixbuf else pixbuf}, uri: {uri}"
        )

        if status and app_name == self.ui_app_name:
            name = uri.rsplit("/", 1)[-1].split(".", 1)[0]
            original_width = pixbuf.get_width()
            original_height = pixbuf.get_height()
            fixed_height = 256
            scaled = pixbuf.scale_simple(
                int(original_width * fixed_height / original_height), fixed_height, GdkPixbuf.InterpType.BILINEAR)
            image = Gtk.Image.new_from_pixbuf(self.round_corners(scaled, 7))
            image.get_style_context().add_class("parslinux-software-screenshot")
            image.name = name
            GLib.idle_add(self.ui_ad_image_box.add, image)
            GLib.idle_add(self.ui_ad_image_box.show_all)

            self.add_to_image_popover(pixbuf, uri)
            GLib.idle_add(self.ui_image_stack.show_all)

    def on_ui_image_prev_button_clicked(self, button):
        if not self.image_stack_names:
            return

        self.image_stack_current_index -= 1
        if self.image_stack_current_index < 0:
            self.image_stack_current_index = len(self.image_stack_names) - 1

        name = self.image_stack_names[self.image_stack_current_index]
        self.ui_image_stack.set_visible_child_name(name)

    def on_ui_image_next_button_clicked(self, button):
        if not self.image_stack_names:
            return

        self.image_stack_current_index += 1
        if self.image_stack_current_index >= len(self.image_stack_names):
            self.image_stack_current_index = 0

        name = self.image_stack_names[self.image_stack_current_index]
        self.ui_image_stack.set_visible_child_name(name)

    def on_ui_image_fullscreen_button_clicked(self, button):
        self.imgfullscreen_count += 1
        if self.imgfullscreen_count % 2 == 1:
            self.resize_popover_image(True)
            self.ui_image_resize_image.set_from_icon_name("view-restore-symbolic", Gtk.IconSize.BUTTON)
        else:
            self.resize_popover_image()
            self.ui_image_resize_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)

    def on_ui_image_popover_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Left:
            self.on_ui_image_prev_button_clicked(widget)
            return True
        elif event.keyval == Gdk.KEY_Right:
            self.on_ui_image_next_button_clicked(widget)
            return True
        elif event.keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.on_ui_image_fullscreen_button_clicked(widget)
            return True

    def resize_popover_image(self, fullscreen=False):
        size = self.MainWindow.get_size()

        if not fullscreen:
            basewidth = size.width - size.width / 3
            self.ui_image_popover.set_size_request(0, 0)
            self.ui_image_resize_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)
        else:
            basewidth = size.width - 125
            self.ui_image_popover.set_size_request(size.width, size.height)
            self.ui_image_resize_image.set_from_icon_name("view-restore-symbolic", Gtk.IconSize.BUTTON)

        for name in self.image_stack_names:
            image = self.ui_image_stack.get_child_by_name(name)

            pixbuf = self.image_original_pixbufs.get(name)
            if pixbuf is None:
                continue

            orig_w = pixbuf.get_width()
            orig_h = pixbuf.get_height()

            hsize = (basewidth * orig_h) / orig_w

            if hsize + 110 > size.height:
                hsize = size.height - 110
                basewidth = (hsize * orig_w) / orig_h

            scaled = pixbuf.scale_simple(int(basewidth), int(hsize), GdkPixbuf.InterpType.BILINEAR)
            image.set_from_pixbuf(scaled)

    def on_ui_image_close_button_clicked(self, button):
        self.ui_image_popover.popdown()

    def on_ui_ad_image_button_press(self, widget, event):
        source = event.get_source_device().get_source()
        self.ui_ad_image_is_touch = (source == Gdk.InputSource.TOUCHSCREEN)

        if not self.ui_ad_image_is_touch and event.button != 1:
            return

        self.ui_ad_image_dragging = True
        self.ui_ad_image_last_x = event.x
        self.ui_ad_image_total_drag = 0

    def on_ui_ad_image_mouse_drag(self, widget, event):
        if self.ui_ad_image_dragging:
            adj = self.ui_ad_image_scrolledwindow.get_hadjustment()
            dx = self.ui_ad_image_last_x - event.x
            adj.set_value(adj.get_value() + dx)
            self.ui_ad_image_total_drag += abs(dx)
            self.ui_ad_image_last_x = event.x

    def on_ui_ad_image_button_release(self, widget, event):
        def get_clicked_image(event):
            adj = self.ui_ad_image_scrolledwindow.get_hadjustment()
            scroll_x = adj.get_value()
            x_in_box = scroll_x + event.x

            for child in self.ui_ad_image_box.get_children():
                if not isinstance(child, Gtk.Image):
                    continue
                alloc = child.get_allocation()
                if alloc.x <= x_in_box <= alloc.x + alloc.width:
                    return child
            return None

        if not self.ui_ad_image_dragging:
            return

        self.ui_ad_image_dragging = False

        clicked_image = get_clicked_image(event)
        if clicked_image is None:
            return

        if self.ui_ad_image_is_touch:
            if self.ui_ad_image_total_drag < self.ui_ad_image_drag_touch_threshold:
                self.Logger.info("Fullscreen Image (Touchscreen)")
                clicked_image_name = clicked_image.name
                if clicked_image_name in self.image_stack_names:
                    self.image_stack_current_index = self.image_stack_names.index(clicked_image_name)
                self.ui_image_stack.set_visible_child_name(clicked_image_name)
                self.imgfullscreen_count = 0
                self.resize_popover_image()
                self.ui_image_popover.popup()
            return

        if event.button == 1 and self.ui_ad_image_total_drag < self.ui_ad_image_drag_threshold:
            self.Logger.info("Fullscreen Image (Mouse or Touchpad)")
            clicked_image_name = clicked_image.name
            if clicked_image_name in self.image_stack_names:
                self.image_stack_current_index = self.image_stack_names.index(clicked_image_name)
            self.ui_image_stack.set_visible_child_name(clicked_image_name)
            self.imgfullscreen_count = 0
            self.resize_popover_image()
            self.ui_image_popover.popup()
