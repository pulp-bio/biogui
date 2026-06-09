# Trigger Post-Run Plotting Integration Plan

## Goal

Add an optional post-run plotting flow to the trigger module so that, once a recording finishes, the GUI can automatically open a visualization for the last collected dataset saved in `DataRunTime/`.

The first implementation should focus only on ultrasound data. The design must stay modular so other signal families can plug in later without changing the trigger controller again.

## Current Situation

- The trigger module currently controls the stimulus/rest sequence and uses the streaming controllers to push trigger values during acquisition.
- The live visualization system is organized around `biogui/views/plot_modes/` with a shared `BasePlotMode` abstraction and ultrasound-specific runtime modes such as `AModePlotMode` and `MModePlotMode`.
- Post-run plotting is not yet separated from live GUI logic, so the new feature should be added as a new layer rather than extending the trigger code with signal-specific plotting logic.

## Confirmed Data-Directory Rules

The current plan should follow these runtime-save rules:

- If the user does not choose a save directory in the configured module, runtime output must be stored under `biogui/dataruntime/`.
- If the user does choose a directory, the runtime output must be saved there instead.
- The current workflow stays intact: the collected file is always a `.bio` file.
- The post-run plotting layer should always look for the last `.bio` file in the active runtime output directory, not for intermediate artifacts.

This means the plotting feature should be attached to the same save-location decision already used by the acquisition workflow, instead of introducing a second output-path policy.

## Recommended Architecture

Create a dedicated offline plotting layer for collected files and keep live plot modes unchanged.

Suggested structure:

- Keep `biogui/views/plot_modes/` for live, in-GUI visualization.
- Add a new folder for post-run plotting, for example `biogui/views/post_run_plotters/` or `biogui/views/offline_plot_modes/`.
- Reuse the same concept of a base interface so the ultrasound plotter can be extended later without rewriting the trigger flow.

Why this split:

- `plot_modes/` already means “rendering inside the GUI while acquisition is running”.
- Post-run plotting will need file discovery, dataframe building, trigger alignment, export naming, and possibly saving figures to disk.
- A separate layer keeps the trigger module small and makes it easier to add other modalities later.

## Proposed Workflow

1. Trigger session runs normally.
2. Data is automatically saved into `DataRunTime/` during or immediately after acquisition.
3. When the session ends, the trigger controller asks a post-run plotting service to locate the newest/last collected file.
4. The plotting service loads that file, reconstructs the dataframe, aligns the trigger information, and generates the ultrasound plot.
5. The plot is shown to the user and, if desired, also exported as a figure file.

## Implementation Phases

### Phase 1: Define the offline plotting contract

Create a small abstraction for post-run plotting so the ultrasound implementation can remain clean and future signals can be added later.

Minimum responsibilities:

- Resolve the input file path.
- Load raw collected ultrasound data.
- Convert data into a structured dataframe or equivalent analysis object.
- Generate the ultrasound visualization.
- Optionally save the output figure.

For ultrasound, the first implementation should accept the saved runtime file format used by the current acquisition pipeline.

### Phase 2: Add a file discovery helper

Implement a utility that locates the last collected file in `DataRunTime/`.

Recommended behavior:

- Resolve the active runtime folder first: `biogui/dataruntime/` when no custom save directory is configured, otherwise the user-selected directory.
- Prefer the newest `.bio` file by modification time.
- If a run folder contains multiple `.bio` files, pick the primary file according to a deterministic rule.
- Fail gracefully if no `.bio` file exists and notify the user with a clear message.

This helper should live outside the trigger controller so other modules can reuse it.

### Phase 3: Add ultrasound-specific plotting logic

Start with an ultrasound post-run plotter that can:

- Read the saved file format.
- Build a pandas dataframe from the collected samples.
- Extract or reconstruct the trigger timeline.
- Render the resulting visualization.

At this stage, the ultrasound plotter can be a direct consumer of the existing runtime data format and later be refactored into smaller pieces if needed.

The attached reference scripts already show the intended analysis shape:

- `utils/data_preparation.py` reads `.bio` files, reconstructs signal arrays, builds a pandas dataframe, carries trigger and trigger-string data, and produces ultrasound visualizations.
- `utils/general_utils.py` contains reusable preprocessing, transient detection, dataset loading, and helper utilities for session handling.
- `utils/plotting_utils.py` contains the current plotting logic for M-mode style views, including trigger and IMU overlays.
- `utils/processing.py` contains ultrasound preprocessing helpers such as band-pass filtering and Hilbert-envelope extraction.

These scripts should be treated as reference implementations for the offline plotting layer, not as the final GUI integration point.

### Phase 4: Hook the trigger lifecycle to post-run plotting

Extend `biogui/modules/trigger.py` so that the end of a trigger session can optionally launch the offline plotting flow.

Suggested behavior:

- Add a configuration option such as `plotAfterRun` or equivalent.
- When enabled, call the plotting service from the cleanup path after acquisition stops.
- Keep this call asynchronous or deferred if plotting can block the GUI.
- Do not let plotting failures break trigger cleanup.

Important: the trigger module should only decide when to start post-run plotting, not how plotting is done.

### Phase 5: Align triggers with the collected data

Because the default behavior should plot all collected data together with the corresponding trigger, the offline plotter should normalize both pieces of information into the same analysis frame.

For ultrasound, this likely means:

- Preserve the trigger value per sample or per file segment.
- Add trigger annotations to the dataframe.
- Ensure the plot uses the same trigger chronology that was recorded during the session.

### Phase 6: Add optional export behavior

If the user enables plotting, the system can also save the generated plot image or report into the same run folder.

Recommended outputs:

- Figure image for quick inspection.
- Optional metadata file describing the source data and trigger sequence.

### Phase 7: Generalize for future signals

Once ultrasound works end-to-end, add more plotters through the same interface when needed.

Future signal families should be able to supply:

- A file reader.
- A dataframe builder.
- A visualization implementation.
- Signal-specific metadata handling.

## Minimal File Impact Strategy

To keep the first change set reviewable, the initial implementation should likely touch only a small number of locations:

- `biogui/modules/trigger.py` for the opt-in launch point.
- A new offline plotting package for file-backed plotting.
- A shared loader/helper for finding the last collected runtime file.
- Optional configuration UI additions if the plotting option must be user-selectable from the GUI.

Likely follow-up path for the implementation:

- Reuse the current save-directory selection logic already present in the configured module.
- Build the offline ultrasound plotter around the `.bio` parsing and dataframe logic already proven in the reference scripts.
- Keep any new file-backed code separate from live `plot_modes/` unless a shared interface is needed.
- Keep the first implementation ultrasound-only; do not add modality-specific branching yet.

## Validation Checklist

Before merging, verify the following:

- Trigger sessions still start and stop normally when plotting is disabled.
- The newest file in `DataRunTime/` is selected deterministically.
- Ultrasound data loads correctly into a dataframe.
- The plotted output contains the collected signal and the corresponding trigger timeline.
- Missing-file and parse-error cases fail gracefully.
- The trigger module does not depend on ultrasound-specific plotting internals.

## Open Questions For The Main Developer

- Where exactly should the runtime save path be defined, and is `DataRunTime/` always the canonical output folder?
- What is the exact file format for the collected ultrasound run data?
- Should the post-run plot open in the GUI, save to disk, or do both by default?
- Should plotting happen at the end of every run or only when a dedicated option is enabled?
- Do we want the offline plotting layer to live under `views/plot_modes/` or as a separate sibling package?

## Suggested First Step Order

1. Confirm the runtime file format and the naming rule for the latest run.
2. Define the offline plotting interface for ultrasound only.
3. Implement file discovery for the last collected run.
4. Add the post-run plotting hook in the trigger cleanup path.
5. Add trigger-aligned visualization and export.
6. Expand the interface to other signal families after ultrasound is stable.

These are my answers to your queston:

1. RunTime save path should be saved within biogui/dataruntime folder if user didn't specify a saing directory in the configured moduler. Otherwise, fetch from the directory choosen by the user. the file is always a .bio file (the current biogui workflow should stay intact)
