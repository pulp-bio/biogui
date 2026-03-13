# MotionLab

Unity 6.3 LTS environment for hand visualization and gesture-controlled task evaluation. Receives hand pose commands from BioBridge over UDP.

## Requirements

- Unity Hub
- Unity Editor **6000.3.11f1** (installed via Unity Hub)

## Setup

1. Launch Unity Hub.

1. Navigate to the Projects tab on the left sidebar.

1. Click the Add dropdown in the top-right corner and select Add project from disk.

1. Select the `motion-lab/` folder.

1. Unity will prompt you to install editor version **6000.3.11f1** if not present.
   - Note: The installation may take several minutes depending on your internet connection.

1. Once installed, open the project.
   - Note: The initial import will take some time, as Unity needs to download and configure the necessary packages and assets. Subsequent launches will be quicker.

1. Open a Unity scene from the:

| Scene                                               | Description                                    |
| --------------------------------------------------- | ---------------------------------------------- |
| `Assets/_Project/Scenes/MainScene.unity`            | Main hand control scene                        |
| `Assets/_Project/Scenes/ContinuousTasksScene.unity` | Continuous task evaluation (used in the paper) |

Open a scene from the Project panel at the bottom and press **Play** at the top to run it.

## Configuring ContinuousTasksScene

All settings are exposed in the Unity Inspector. Select the `ContinuousTaskManager` GameObject in the scene hierarchy to configure:

**Active tasks** — enable or disable individual tasks:

| Task              | Description                                   |
| ----------------- | --------------------------------------------- |
| Box Delivery      | Pick up and deliver a box (used in the paper) |
| Cylinder Delivery | Pick up and deliver a cylinder                |
| Bottle Pouring    | Pour a bottle into a container                |
| Marble Delivery   | Deliver a marble                              |

**Task Selection** — sequential or random order.

**Timing** — `Pre-task Countdown`, `Task Timeout`, `Completion Delay`.

**Position Mode** — `State` (discrete positions: neutral / forward / right; this was used in the paper) or `Delta` (incremental movement).

Task results are automatically saved as CSV files to `motion-lab/Results/` at the end of each session.
