#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  This file is part of solus-sc
#
#  Copyright © 2014-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#

from .details import PackageDetailsView
from gi.repository import Gtk, GLib


""" enum for the model fields """
INDEX_FIELD_DISPLAY = 0
INDEX_FIELD_NAME = 1
INDEX_FIELD_ICON = 2
INDEX_FIELD_ARROW = 3


class LoadingPage(Gtk.VBox):
    """ Simple loading page, nothing fancy. """

    spinner = None

    def __init__(self):
        Gtk.VBox.__init__(self)

        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(-1, 64)
        self.spinner.start()
        self.label = Gtk.Label("<big>Solving the Paradox Of Choice" + u"…"
                               "</big>")
        self.label.set_use_markup(True)

        self.pack_start(self.spinner, True, True, 0)
        self.pack_start(self.label, False, False, 0)
        self.label.set_property("margin", 20)


class ScPackageView(Gtk.VBox):

    scroll = None
    tview = None
    appsystem = None
    basket = None
    stack = None
    load_page = None
    details_view = None

    def handle_back(self):
        """ Go back to the main view """
        self.stack.set_visible_child_name("packages")

    def __init__(self, basket, appsystem):
        Gtk.VBox.__init__(self, 0)
        self.basket = basket
        self.appsystem = appsystem

        self.stack = Gtk.Stack()
        self.pack_start(self.stack, True, True, 0)

        self.load_page = LoadingPage()
        self.stack.add_named(self.load_page, "loading")

        # Set up the details view
        self.details_view = PackageDetailsView(self.appsystem)
        self.stack.add_named(self.details_view, "details")

        self.scroll = Gtk.ScrolledWindow(None, None)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.scroll.set_overlay_scrolling(False)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_property("kinetic-scrolling", True)
        self.stack.add_named(self.scroll, "packages")

        # Main treeview where it's all happening. Single click activate
        self.tview = Gtk.TreeView()
        self.tview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.tview.connect_after('row-activated', self.on_row_activated)
        self.tview.set_activate_on_single_click(True)

        # Defugly
        self.tview.set_property("enable-grid-lines", False)
        self.tview.set_property("headers-visible", False)
        self.scroll.add(self.tview)

        # img view
        ren = Gtk.CellRendererPixbuf()
        ren.set_property("stock-size", Gtk.IconSize.DIALOG)
        ren.set_padding(5, 2)
        column = Gtk.TreeViewColumn("Icon", ren, icon_name=2)
        self.tview.append_column(column)

        # Set up display columns
        ren = Gtk.CellRendererText()
        ren.set_padding(5, 5)
        column = Gtk.TreeViewColumn("Name", ren, markup=0)
        self.tview.append_column(column)
        self.tview.set_search_column(1)

        # Details
        ren = Gtk.CellRendererPixbuf()
        ren.set_padding(5, 5)
        column = Gtk.TreeViewColumn("Details", ren, icon_name=3)
        self.tview.append_column(column)
        ren.set_property("xalign", 1.0)

        self.stack.set_visible_child_name("loading")

    def init_view(self):
        model = Gtk.ListStore(str, str, str, str)
        model.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        # HAX: Allow me to test stuff.
        whitelist_packages = [
            "blender",
            "firefox",
            "font-clear-sans-ttf",
            "libreoffice-writer",
            "gnome-weather",
            "pitivi",
            "gimp",
            "steam",
            "totem",
        ]

        for pkg_name in self.basket.installdb.list_installed():
            if pkg_name not in whitelist_packages:
                continue
            pkg = self.basket.installdb.get_package(pkg_name)

            summary = self.appsystem.get_summary(pkg)
            summary = str(summary)
            if len(summary) > 76:
                summary = "%s…" % summary[0:76]

            summary = GLib.markup_escape_text(summary)

            name = str(pkg.name)
            p_print = "<b>%s</b> - %s\n%s" % (name, str(pkg.version),
                                              summary)
            icon = "package-x-generic"
            if pkg.icon is not None:
                icon = str(pkg.icon)

            model.append([p_print, pkg_name, icon, "go-next-symbolic"])

        self.tview.set_model(model)
        GLib.idle_add(self.finish_view)
        return False

    def finish_view(self):
        self.load_page.spinner.stop()
        self.stack.set_visible_child_name("packages")
        return False

    def on_row_activated(self, tview, path, column, udata=None):
        """ User clicked a row, now try to load the page """
        model = tview.get_model()
        row = model[path]

        pkg_name = row[INDEX_FIELD_NAME]
        pkg = self.basket.installdb.get_package(pkg_name)
        self.details_view.update_from_package(pkg)
        self.stack.set_visible_child_name("details")
