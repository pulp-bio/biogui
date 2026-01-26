# Trigger Module
The Trigger module allows you to display visual stimuli and send trigger signals to your data acquisition interfaces during experiments. When you add the Trigger module, a configuration widget appears in the scrollable area where you can load a JSON configuration file that defines the trigger sequence. An example can be found under [`acquisitions/acquisition_config.json`](https://github.com/pulp-bio/biogui/blob/main/acquisitions/acquisition_config.json) in the BioGUI repository.

## Configuration
The trigger configuration is defined via a JSON file with the following structure:

```json
{
    "triggers": {
        "Open Hand": "open_hand.png",
        "Close Hand": "close_hand.png"
    },
    "nReps": 5,
    "durationTrigger": 2000,
    "durationStart": 1000,
    "durationRest": 3000,
    "imageFolder": "/path/to/images"
}
```

### Parameters
- `triggers`: Dictionary mapping trigger labels to image filenames
- `nReps`: Number of repetitions for each trigger
- `durationTrigger`: Duration (in milliseconds) for which each stimulus is displayed
- `durationStart`: Initial delay (in milliseconds) before the first trigger
- `durationRest`: Duration (in milliseconds) of rest periods between triggers with countdown
- `imageFolder`: Path to the folder containing the stimulus images

## How It Works
1. When streaming starts, a viewer window opens displaying "START"
2. After `durationStart` milliseconds, the trigger sequence begins
3. For each trigger (repeated `nReps` times):
    - The stimulus is displayed as an image
    - A trigger signal is sent to all streaming controllers
    - After `durationTrigger` milliseconds, the rest period begins
    - During rest, a countdown is displayed showing the upcoming stimulus label
    - Triggers are set to 0 during rest periods
4. When all triggers are complete, the sequence stops

## Usage Tips
- Images should be in PNG or JPG format
- If an image file is missing, the trigger label is displayed instead
- The countdown helps subjects prepare for the upcoming stimulus
- The viewer window can be closed to stop the trigger sequence early
