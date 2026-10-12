# Claude AI Assistant Guide (CLAUDE.md)

This document provides architectural context, commands, and coding standards for AI assistants (such as Claude Code and Google Antigravity) working on the **Pars Linux Software Center** repository.

---

## 1. Project Overview & Context

- **Repository:** Pars Linux Software Center (`parslinux-software`)
- **Architecture:** Fully independent modern software store tailored for Pars Linux and all Linux distributions.
- **Core Technology:** Python 3, GTK+ 3 (PyGObject), Glade XML UI (`ui/MainWindow.glade`), Flathub REST API v2, Flatpak CLI.
- **Package Management:** Powered entirely by Flathub as the primary universal application catalog and Flatpak as the local package management engine, supporting Arch Linux, Pars Linux, Fedora, and Debian derivatives alike with zero legacy repository dependencies.

---

## 2. Key Directories & File Structure

```
├── parslinux-software           # Executable launcher script
├── parslinux-software.conf      # Configuration (server = https://flathub.org/api/v2, backend = flathub)
├── docs/                        # Complete technical & user documentation
├── icons/                       # 20 FreeDesktop category SVGs (ps-cat-*.svg) & rating stars
│   └── hicolor/scalable/       # Standard XDG icon theme structure
├── src/
│   ├── Main.py                  # Gtk.Application entry point
│   ├── MainWindow.py            # Primary UI coordinator inheriting from controllers/
│   ├── controllers/             # Modular UI controllers (mixins)
│   │   ├── SliderMixin.py       # Hero banner carousel & timer transitions
│   │   ├── ImageGalleryMixin.py # App screenshots gallery & modal preview
│   │   ├── SearchMixin.py       # Search debouncing, Meilisearch, category switches, settings
│   │   ├── DetailMixin.py       # App detail view, metadata, permissions, action buttons
│   │   ├── QueueMixin.py        # Asynchronous installation/removal queue & status
│   │   └── InstalledMixin.py    # Flatpak & system installed application views
│   ├── FlathubClient.py         # Flathub v2 REST API client, 2-tier disk cache, Meilisearch
│   ├── FlatpakManager.py        # Flatpak CLI management (list, install, uninstall, update, launch)
│   ├── Server.py                # Server router bridging FlathubClient to apps.json/cats.json
│   ├── Package.py               # Package abstraction layer (supports Flatpak & optional APT)
│   ├── Actions.py               # Execution engine for package install/remove/update
│   ├── AppImage.py              # Async Gio/GdkPixbuf stream loader for screenshots
│   └── UserSettings.py          # Configuration parser (~/.config/parslinux/)
└── ui/
    └── MainWindow.glade         # GTK3 XML UI layout definition
```

---

## 3. Essential Development & Testing Commands

### Syntax & Compile Check:
```bash
python3 -m py_compile setup.py src/*.py src/controllers/*.py
```

### Running Locally:
```bash
./parslinux-software
# or
python3 src/Main.py
```

### Mixin Verification & Contracts:
```bash
python3 scratch/verify_mixins.py
```

### FlowBox Stability & Zero-Flicker Test:
```bash
python3 scratch/test_flowbox_stability.py
```

### Headless Verification (Non-blocking):
```bash
python3 scratch/test_mainwindow_headless.py
```

### Integration Test (Flathub API & Flatpak):
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from FlathubClient import FlathubClient; from FlatpakManager import FlatpakManager; c = FlathubClient(); m = FlatpakManager(); print('Flathub:', c.check_connection(), 'Installed Flatpaks:', len(m.get_installed_apps()))"
```

---

## 4. Critical Engineering Rules

1. **Flathub & Flatpak Architecture Independence:**
   - The project is 100% independent and relies exclusively on Flathub REST API v2 and the modern Flatpak ecosystem. Never introduce legacy or single-distribution repository endpoints.
2. **Never Hardcode Debian-Specific Dependencies:**
   - Always wrap `apt`, `apt_pkg`, `distro`, `psutil`, and `netifaces` imports in `try/except ImportError:` with graceful fallbacks.
3. **Modular Mixin Architecture:**
   - Do NOT add new monolithic methods directly into `MainWindow.py`. Maintain domain separation in `src/controllers/*Mixin.py`. `MainWindow` acts as a central coordinator.
4. **FlowBox Zero-Flicker Rules:**
   - NEVER clear `ui_parslinuxapps_flowbox` children using `remove(child)` during category or search transitions.
   - Maintain the persistent registry `self._flowbox_app_ids = set()`.
   - Build cards synchronously via `_create_app_card_sync` and use incremental addition via `_append_apps_to_flowbox`.
   - Rely exclusively on GTK native `invalidate_filter()` and `invalidate_sort()` for 0ms flicker-free filtering.
5. **Thread Safety in GTK+ 3:**
   - GTK is not thread-safe. NEVER call GTK widget methods directly from background threads or worker pools. ALWAYS use `GLib.idle_add(callback, *args)`.
6. **Pango Markup Escaping:**
   - Application summaries, developer names, and URLs fetched from Flathub often contain `&`, `<`, `>`. Always wrap strings passed to `set_markup()` in `GLib.markup_escape_text(text, -1)` to prevent Pango markup parse errors and GUI crashes.
7. **Clean HTML Descriptions:**
   - Flathub descriptions arrive in raw HTML format. Clean HTML tags (`<p>`, `<br>`, `<li>`) before displaying them in plain GTK labels.
8. **Settings Safety:**
   - Both HeaderBar and Sidebar access the Settings view. Always check for `getattr(self, 'server', None)` and `getattr(self, 'package', None)` existence before making calls that assume a populated package catalog.

