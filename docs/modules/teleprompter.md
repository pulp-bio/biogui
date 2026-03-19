# Teleprompter Module
The Teleprompter module displays text prompts for reading or speaking tasks, with configurable voiced and silent modes. When you add the Teleprompter module, a configuration widget appears in the scrollable area where you can load a JSON file containing sentences and timing parameters. A teleprompter window displays the sentences with word-by-word highlighting. An example can be found under [`acquisitions/teleprompter_dates.json`](https://github.com/pulp-bio/biogui/blob/main/acquisitions/teleprompter_dates.json).

## Configuration
The teleprompter configuration is defined via a JSON file with the following structure:

```json
{
    "sentences": [
        "The quick brown fox jumps over the lazy dog.",
        "Hello, this is a test sentence.",
        "Another example for demonstration."
    ],
    "durationStart": 1000,
    "durationPerSentence": 3000,
    "durationRest": 2000,
    "numberofRepeatsVoiced": 2,
    "numberofRepeatsSilent": 1
}
```

### Parameters
- `sentences`: Array of strings, each containing a sentence to display
- `durationStart`: Initial delay (in milliseconds) before the first sentence
- `durationPerSentence`: Duration (in milliseconds) for each sentence display
- `durationRest`: Duration (in milliseconds) of rest periods between repetitions
- `numberofRepeatsVoiced`: Number of times to repeat each sentence in voiced mode
- `numberofRepeatsSilent`: Number of times to repeat each sentence in silent mode

## How It Works
1. When streaming starts, a teleprompter window opens displaying "START"
2. After `durationStart` milliseconds, the sentence sequence begins
3. For each sentence:
    - The sentence is repeated `numberofRepeatsVoiced` times in VOICED mode
    - Each repetition is followed by a REST period of duration `durationRest`
    - Then the sentence is repeated `numberofRepeatsSilent` times in SILENT mode
    - Each repetition is followed by a REST period
4. When all sentences are complete, the sequence stops
