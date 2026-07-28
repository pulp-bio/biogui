# QtWidgets → QML Migration Notes

This is a scoping document for a long-term, incremental migration of BioGUI's UI layer from
QtWidgets to QML. It is not a schedule or a commitment — it's a map of what has to change, in
what rough order, and why, so the migration can proceed gradually without losing track of the
overall shape.

## Can `data_sources/` be kept as-is?

**Not the files as currently laid out, but the I/O logic itself needs no rewrite.**

Every file under `biogui/data_sources/` (e.g. `serial.py`) currently defines *two* classes in one
file: a pure-QtCore `*DataSourceWorker` (`QObject`/`QThread`/`Signal` only) and a QtWidgets
`*ConfigWidget` (the form shown in "Add data source"). Because they share a file, and because
`base.py`/`__init__.py` import `QWidget` unconditionally (just for type hints and the abstract
`DataSourceConfigWidget`), a worker class can't currently be imported without dragging in
QtWidgets.

The fix is a **mechanical split** — worker → its own QtCore-only file, config widget → its own
QtWidgets file — not a behavioral rewrite. The two `wulpus`/`wulpus_pro` platform families go
further and embed a `QDialog`-popping config callback directly in/next to the interface file;
those need the same treatment, since it's the same worker/config-UI entanglement at the plugin
level.

## What's already portable unchanged

- `biogui/controllers/streaming_controller.py`, `biogui/controllers/signal_filters.py` — pure
  QtCore/numpy/scipy, zero QtWidgets.
- Most `biogui/platforms/*/interface_*.py` decode modules — pure numpy, no Qt at all (exceptions:
  the wulpus family, see above).
- The `*DataSourceWorker` classes themselves (post-split).
- `main.py`'s `SocketListener` (remote start/stop over TCP).
- No `QSettings` usage anywhere (plain JSON/dicts) — nothing to migrate there.

The acquisition/streaming core was already built in a QtCore-clean style, mostly as a side effect
of using QObject/QThread for worker plumbing. The rewrite is concentrated in the view and
controller layers.

## What has to change, in broad terms

1. **App bootstrap** (`biogui/biogui.py`) — `BioGUI(QApplication)` directly builds and shows a
   `QMainWindow`. A QML app needs `QGuiApplication` + `QQmlApplicationEngine` loading a root
   `.qml` file instead. Treat this as the *last* step, not the first.

2. **`MainController`** (`biogui/controllers/main_controller.py`, 971 lines — the single biggest
   item) — currently reaches directly into `MainWindow`'s named child widgets everywhere: sets
   models on `dataSourceTree`, toggles button `setEnabled`, constructs and `.exec()`s dialogs
   inline, calls `mainWin.addPlotWidget`/`removePlotWidget`, pops `QMessageBox` directly, and
   defines a `QStyledItemDelegate` with manual `QPainter` row-drawing plus a widget
   `eventFilter`. QML needs this turned into a real view-model: properties/signals/models only,
   no widget-name reach-through, no inline dialog popping.

3. **`ModuleController`** and the three pluggable modules (`modules/trigger.py`,
   `forwarding.py`, `teleprompter.py`) — each currently does
   `mainWin.moduleContainer.layout().addWidget(...)` to inject its sidebar config UI, and
   `trigger.py` additionally hand-paints stimulus frames with raw `QPainter`/`QPixmap`. The
   "grab a layout and addWidget" plugin contract has no QML equivalent — needs to become "each
   module exposes a QML `Component`, host uses `Loader`/`Repeater`."

4. **Platform config plugin point** (`PlatformConfig.configureInterfaceModule`, used by
   `wulpus`/`wulpus_pro`) — today it's literally "a callback that pops a `QDialog`." Same
   redesign as (3): swap for a QML component/path contract.

5. **The whole `biogui/views/` tree** — forms (`SignalConfigWidget`/`Dialog`), a
   `QWizard`-based flow (`SignalConfigWizard` — QWizard has no QML analog, becomes a
   `StackView`), a tree-in-combobox picker (`DataSourceConfigDialog`, 614 lines), one genuinely
   hand-painted widget (`SidebarSplitter`'s collapse arrow), and the `post_run_plotters/`
   dashboards (dense, pyqtgraph+pandas driven).

6. **pyqtgraph — the hardest problem, deliberately last.** pyqtgraph has *no* QML binding, and
   it's the dominant graphics dependency: live line plots, a real-time scrolling image/waterfall
   for ultrasound M-mode (`mmode_plot_mode.py`, updates a `pg.ImageItem` every frame), and every
   post-run dashboard. A prior attempt to back pyqtgraph with `QOpenGLWidget` was abandoned for
   performance reasons — a signal that current plotting is tuned for CPU rendering, not GPU.
   Realistic options, roughly in the order to try them:
   - Keep pyqtgraph, embed it via `QQuickWidget` inside otherwise-QML panels — legitimate as a
     permanent end state, not just a stopgap, especially for M-mode.
   - Prototype **Qt Graphs** (QML module) for the simple line-plot screens only, with a
     throughput spike first — real-time append performance at streaming rates is unproven,
     don't assume it.
   - Fall back to `QQuickPaintedItem` (closest match to pyqtgraph's current CPU-painted
     approach) if Qt Graphs disappoints.
   - `QQuickFramebufferObject` only if that also disappoints — it reintroduces the same GPU
     uncertainty the old `QOpenGLWidget` attempt hit.

   It's fine — arguably correct — for M-mode and the dashboards to simply stay
   pyqtgraph-in-`QQuickWidget` indefinitely.

## Recommended approach: incremental, hybrid, bottom-up

Not a big-bang rewrite. Use `QQuickWidget` to embed QML panels **inside the existing
`QMainWindow`**, one screen at a time, so the app stays runnable at every step. Full replacement
of the root window with `QQmlApplicationEngine` is optional and should come last, if at all —
staying permanently hybrid is a legitimate architecture with no deadline attached.

Suggested phase order (each phase should ship before starting the next):

- **Phase 0 (do first, regardless of QML timing):** prerequisite refactors — split `utils.py`
  (pull `detectTheme()`/QWidget-parameterized type alias out, leave it pure dataclasses), split
  every `data_sources/*.py` into worker + config-widget files, same split for the
  wulpus/wulpus_pro config mechanism, and introduce a narrow interface between `MainController`
  and `MainWindow` (setters/properties instead of reaching into named children). These are pure
  refactors with no visible behavior change — verifiable against the current running app, and
  valuable even if QML stalls.
- **Phase 1 — learn QML on low-stakes, low-coupling screens:** `HelpDialog` (self-contained),
  `SidebarSplitter`'s collapse arrow (small, and genuinely *easier* in QML — a good early win).
- **Phase 2 — simple forms with real controller coupling:** `SignalConfigWidget`/`Dialog`, the
  data-source config widgets (now split out per Phase 0), the tree-in-combobox picker, then
  `SignalConfigWizard` (as a `StackView`) — this is where the "QML view + Python view-model via
  properties/`QAbstractItemModel`" pattern gets established for reuse everywhere after.
- **Phase 3 — plugin architecture:** redefine the module contract (`Loader`-based instead of
  `layout().addWidget`) once, then port `teleprompter.py` → `forwarding.py` → `trigger.py`
  through it; redefine and port the platform config-dialog contract the same way.
- **Phase 4 — `MainController`/`MainWindow`:** only once Phases 1–3 have working QML
  replacements for everything it currently instantiates. Highest line count, most consequential,
  most worth doing last.
- **Phase 5 — pyqtgraph/real-time plotting:** highest risk, deliberately last, so QML fluency is
  already built and effort goes entirely into the graphics problem. See options above.
- **Phase 6 (optional, "graduation"):** swap `BioGUI(QApplication)`/`MainWindow` for
  `QGuiApplication`+`QQmlApplicationEngine`. Not required — the hybrid state from Phase 0 onward
  is a fine permanent architecture.

## Critical files (representative, not exhaustive)

- `biogui/biogui.py` — app bootstrap, changes last (Phase 6)
- `biogui/utils.py` — split pure dataclasses from QtWidgets helpers (Phase 0)
- `biogui/data_sources/base.py`, `data_sources/__init__.py`, `data_sources/serial.py`
  (representative of all transport files) — worker/config-widget split (Phase 0)
- `biogui/controllers/main_controller.py` — the big view-model rewrite (Phase 4)
- `biogui/controllers/module_controller.py` — smaller version of the same problem
- `biogui/modules/trigger.py`, `forwarding.py`, `teleprompter.py` — plugin contract redesign
  (Phase 3)
- `biogui/platforms/wulpus/runtime.py`, `wulpus_pro/runtime.py` — platform config contract
  redesign (Phase 3)
- `biogui/views/` (whole directory) — form/dialog/wizard ports (Phase 2), `sidebar_splitter.py`
  (Phase 1), `help_dialog.py` (Phase 1)
- `biogui/views/plot_modes/mmode_plot_mode.py`, `time_series_plot_mode.py`,
  `amode_plot_mode.py`, `views/post_run_plotters/` — pyqtgraph problem (Phase 5)
