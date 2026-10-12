#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright: 2026 Pars Linux Developers <dev@parslinux.org>
# This file is part of parslinux-software.
# parslinux-software is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.

import sys

import gi

from MainWindow import MainWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="org.parslinux.software",
                         flags=Gio.ApplicationFlags(8), **kwargs)
        self.window = None
        GLib.set_prgname("org.parslinux.software")

        self.add_main_option(
            "details",
            ord("d"),
            GLib.OptionFlags(0),
            GLib.OptionArg(1),
            "Details page of application",
            None,
        )

        # self.add_main_option(
        #     "remove",
        #     ord("r"),
        #     GLib.OptionFlags(0),
        #     GLib.OptionArg(1),
        #     "Remove page of application",
        #     None,
        # )

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = MainWindow(self)
        else:
            self.window.control_args()
        self.window.MainWindow.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()
        self.args = options
        self.activate()
        return 0


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
