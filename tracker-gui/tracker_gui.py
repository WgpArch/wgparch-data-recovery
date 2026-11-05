#!/usr/bin/env python3
"""WgpArch Job Tracker - Reliable GTK4 ListView"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, GObject, Pango
import yaml
import sqlite3
import os
import sys

# Force dark theme
Adw.init()
Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)

class JobObject(GObject.Object):
    __gtype_name__ = "JobObject"
    reference_number = GObject.Property(type=str)
    customer_name = GObject.Property(type=str)
    file_type = GObject.Property(type=str)
    status = GObject.Property(type=str)
    created_at = GObject.Property(type=str)

    def __init__(self, ref="", name="", ftype="", status="", date=""):
        super().__init__()
        self.reference_number = ref or "N/A"
        self.customer_name = name or "Unknown"
        self.file_type = ftype or "-"
        self.status = status or "Received"
        self.created_at = date[:10] if date else ""

class TrackerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="WgpArch Job Tracker")
        self.set_default_size(1000, 650)

        # Load config & DB
        config_path = os.path.expanduser("~/.config/wgparch-data-recovery/config.yaml")
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        db_path = os.path.expanduser(self.config['database']['path'])
        self.conn = sqlite3.connect(db_path)

        # Main Layout
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(box)

        # Header
        header = Adw.HeaderBar()
        title = Gtk.Label(label=f"Job Tracker • R{self.config['business']['analysis_fee']} Analysis Fee")
        title.add_css_class("title")
        header.set_title_widget(title)
        box.append(header)

        # Toolbar
        toolbar = Gtk.Box(spacing=6, margin_top=6, margin_bottom=6, margin_start=12, margin_end=12)
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh_btn.connect("clicked", self.load_jobs)
        toolbar.append(refresh_btn)
        
        self.count_label = Gtk.Label(hexpand=True, xalign=1)
        self.count_label.add_css_class("dim-label")
        toolbar.append(self.count_label)
        box.append(toolbar)

        # LIST VIEW SETUP (The reliable way)
        self.list_store = Gio.ListStore(item_type=JobObject)
        selection = Gtk.SingleSelection(model=self.list_store)

        list_view = Gtk.ListView(model=selection, factory=None)
        list_view.set_show_separators(True)

        # Create a factory that builds rows dynamically
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_row)
        factory.connect("bind", self._bind_row)
        list_view.set_factory(factory)

        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True, margin_start=12, margin_end=12, margin_bottom=12)
        scrolled.set_child(list_view)
        box.append(scrolled)

        self.load_jobs(None)

    def _setup_row(self, factory, list_item):
        """Build the row widget with EXPLICIT sizing"""
        box = Gtk.Box(spacing=12, margin_top=8, margin_bottom=8, margin_start=6, margin_end=6)
        
        # Ref Column - Fixed width, Z003 font
        ref_lbl = Gtk.Label(xalign=0)
        ref_lbl.set_size_request(100, -1)
        ref_lbl.add_css_class("monospace")
        ref_lbl.add_css_class("caption")
        box.append(ref_lbl)
        
        # Name Column - Expands to fill available space
        name_lbl = Gtk.Label(xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        name_lbl.set_size_request(150, -1)
        box.append(name_lbl)
        
        # Type Column
        type_lbl = Gtk.Label(xalign=0)
        type_lbl.set_size_request(80, -1)
        box.append(type_lbl)
        
        # Status Column
        status_lbl = Gtk.Label(xalign=0)
        status_lbl.set_size_request(90, -1)
        box.append(status_lbl)
        
        # Date Column
        date_lbl = Gtk.Label(xalign=0)
        date_lbl.set_size_request(90, -1)
        date_lbl.add_css_class("dim-label")
        box.append(date_lbl)

        # ✅ NEW: Download Button
        dl_btn = Gtk.Button.new_from_icon_name("document-open-symbolic")
        dl_btn.set_tooltip_text("Open Download Link")
        # Validate R2 and cloud links before enabling button
        cursor = self.conn.execute(
            "SELECT download_link FROM jobs WHERE reference_number = ?", 
            (job.reference_number,)
        )
        row = cursor.fetchone()
        link = row[0] if row else ""
        dl_btn.set_size_request(36, 36)
        box.append(dl_btn)

        list_item.set_child(box)

    def _bind_row(self, factory, list_item):
        """Update row widgets with data + FORCE TEXT COLOR"""
        job = list_item.get_item()
        box = list_item.get_child()
        
        # Get children safely
        labels = []
        child = box.get_first_child()
        while child:
            if isinstance(child, Gtk.Label):
                labels.append(child)
            child = child.get_next_sibling()
        
        if len(labels) == 5:
            # Set text
            labels[0].set_text(job.reference_number)
            labels[1].set_text(job.customer_name)
            labels[2].set_text(job.file_type)
            labels[4].set_text(job.created_at)
            
            # Status with color AND explicit foreground
            s_lbl = labels[3]
            s_lbl.set_text(job.status)
            
            # Reset all classes first
            for cls in ["accent", "warning", "success", "error"]:
                s_lbl.remove_css_class(cls)
            
            # Apply status color + force white text for visibility
            s_lbl.add_css_class("body")
            if job.status == "Received": 
                s_lbl.add_css_class("accent")
            elif job.status == "Analyzing": 
                s_lbl.add_css_class("warning")
            elif job.status == "Repaired": 
                s_lbl.add_css_class("success")

    def load_jobs(self, btn):
        self.list_store.remove_all()
        
        # Flexible schema detection
        cursor = self.conn.execute("PRAGMA table_info(jobs)")
        cols = {row[1]: row[1] for row in cursor.fetchall()}
        
        ref = cols.get('reference_number', 'NULL as reference_number')
        name = cols.get('customer_name', cols.get('name', 'NULL as customer_name'))
        ftype = cols.get('file_type', cols.get('type', 'NULL as file_type'))
        status = cols.get('status', 'NULL as status')
        date = cols.get('created_at', cols.get('date', 'NULL as created_at'))
        
        query = f"SELECT {ref}, {name}, {ftype}, {status}, {date} FROM jobs ORDER BY {date} DESC LIMIT 100"
        
        try:
            for row in self.conn.execute(query):
                job = JobObject(
                    ref=row[0], name=row[1], ftype=row[2], 
                    status=row[3], date=str(row[4]) if row[4] else ""
                )
                self.list_store.append(job)
            self.count_label.set_text(f"{len(self.list_store)} jobs loaded")
        except Exception as e:
            self.count_label.set_text(f"Error: {e}")

class TrackerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wgparch.tracker")
    
    def do_activate(self):
        TrackerWindow(self).present()

if __name__ == "__main__":
    TrackerApp().run(sys.argv)
