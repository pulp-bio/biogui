using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Rotation task with simple timing: one time per repetition.
/// Timer starts on first fist, stops when back at neutral.
/// </summary>
public class RotationTask : MonoBehaviour
{
    [Header("Task Settings")]
    public float targetSupinationAngle = 70f;
    public float angleTolerance = 5f;
    public float neutralTolerance = 10f;
    public int targetRepetitions = 5;

    [Header("Gesture Detection")]
    public float grabThreshold = 0.6f;
    public float releaseThreshold = 0.3f;

    [Header("References")]
    public HandController handController;

    [Header("Debug")]
    public bool showDebug = false;

    // Task state machine
    public enum TaskState
    {
        WaitingForGrabAtNeutral,
        WaitingForReleaseAtNeutral,
        RotatingToSupination,
        WaitingForGrabAtSupination,
        WaitingForReleaseAtSupination,
        RotatingToNeutral,
        Complete,
    }

    private TaskState state = TaskState.WaitingForGrabAtNeutral;
    private int currentRepetition = 0;
    private bool wasGripping = false;

    // Simple timing: start on first fist, stop when back at neutral
    private float repetitionStartTime = -1f;
    private float taskStartTime = -1f;
    private float taskCompleteTime = -1f;

    // Initial rotation reference
    private float initialSupinationAngle = 0f;

    // Public properties
    public bool IsComplete => state == TaskState.Complete;
    public float CurrentSupinationAngle { get; private set; }
    public float CurrentRelativeAngle { get; private set; }
    public int CurrentRepetition => currentRepetition;
    public int TotalRepetitions => targetRepetitions;

    // Expose current state for UI
    public TaskState GetCurrentState() => state;

    /// <summary>
    /// Simple timing: just duration of one complete repetition.
    /// </summary>
    [System.Serializable]
    public class RepetitionTiming
    {
        public int repetitionNumber;
        public float duration; // Total time for this repetition
    }

    private List<RepetitionTiming> repetitionTimings = new List<RepetitionTiming>();

    void Awake()
    {
        if (!handController)
            handController = FindFirstObjectByType<HandController>();
    }

    void Start()
    {
        taskStartTime = Time.time;

        // Record initial rotation
        if (handController)
        {
            Vector3 handRotation = handController.CurrentRotationEuler;
            initialSupinationAngle = NormalizeAngle(handRotation.z);
        }
    }

    void Update()
    {
        if (state == TaskState.Complete || !handController)
            return;

        // Get current hand state
        float currentGrip = handController.GripValue;
        bool isGripping = currentGrip >= grabThreshold;
        bool justGrabbed = isGripping && !wasGripping;
        bool justReleased = !isGripping && wasGripping;
        wasGripping = isGripping;

        // Get current rotation
        Vector3 handRotation = handController.CurrentRotationEuler;
        CurrentSupinationAngle = NormalizeAngle(handRotation.z);

        // Calculate relative angle, direction depends on handedness
        float relativeAngle = CurrentSupinationAngle - initialSupinationAngle;
        relativeAngle = NormalizeAngle(relativeAngle);
        relativeAngle = -handController.HandednessMultiplier * relativeAngle;
        CurrentRelativeAngle = relativeAngle;

        // State machine
        switch (state)
        {
            case TaskState.WaitingForGrabAtNeutral:
                if (justGrabbed && IsAtNeutral())
                {
                    // START TIMER for this repetition
                    repetitionStartTime = Time.time;

                    state = TaskState.WaitingForReleaseAtNeutral;
                    if (showDebug)
                        Debug.Log($"[Rep {currentRepetition + 1}] Started (fist at neutral)");
                }
                break;

            case TaskState.WaitingForReleaseAtNeutral:
                if (justReleased)
                {
                    state = TaskState.RotatingToSupination;
                    if (showDebug)
                        Debug.Log($"[Rep {currentRepetition + 1}] Open at neutral");
                }
                break;

            case TaskState.RotatingToSupination:
                if (IsAtSupination())
                {
                    state = TaskState.WaitingForGrabAtSupination;
                    if (showDebug)
                        Debug.Log(
                            $"[Rep {currentRepetition + 1}] Reached supination ({relativeAngle:F1}°)"
                        );
                }
                break;

            case TaskState.WaitingForGrabAtSupination:
                if (justGrabbed && IsAtSupination())
                {
                    state = TaskState.WaitingForReleaseAtSupination;
                    if (showDebug)
                        Debug.Log($"[Rep {currentRepetition + 1}] Fist at supination");
                }
                break;

            case TaskState.WaitingForReleaseAtSupination:
                if (justReleased)
                {
                    state = TaskState.RotatingToNeutral;
                    if (showDebug)
                        Debug.Log($"[Rep {currentRepetition + 1}] Open at supination");
                }
                break;

            case TaskState.RotatingToNeutral:
                if (IsAtNeutral())
                {
                    // STOP TIMER for this repetition
                    float duration = Time.time - repetitionStartTime;

                    // Store completed repetition
                    repetitionTimings.Add(
                        new RepetitionTiming
                        {
                            repetitionNumber = currentRepetition + 1,
                            duration = duration,
                        }
                    );

                    if (showDebug)
                        Debug.Log(
                            $"[Rep {currentRepetition + 1}] Complete! Duration: {duration:F2}s"
                        );

                    currentRepetition++;

                    if (currentRepetition >= targetRepetitions)
                    {
                        CompleteTask();
                    }
                    else
                    {
                        // Start new repetition immediately
                        state = TaskState.WaitingForGrabAtNeutral;
                        repetitionStartTime = -1f;
                    }
                }
                break;
        }
    }

    bool IsAtNeutral()
    {
        return Mathf.Abs(CurrentRelativeAngle) <= neutralTolerance;
    }

    bool IsAtSupination()
    {
        return CurrentRelativeAngle >= targetSupinationAngle - angleTolerance;
    }

    void CompleteTask()
    {
        state = TaskState.Complete;
        taskCompleteTime = Time.time;

        float totalDuration = taskCompleteTime - taskStartTime;
        if (showDebug)
            Debug.Log(
                $"[RotationTask] All complete! Total time: {totalDuration:F2}s, Reps: {currentRepetition}"
            );
    }

    public float GetCurrentRepetitionDuration()
    {
        if (repetitionStartTime < 0)
            return 0f;

        return Time.time - repetitionStartTime;
    }

    public float GetTotalTaskDuration()
    {
        if (taskStartTime < 0)
            return 0f;

        if (state == TaskState.Complete)
            return taskCompleteTime - taskStartTime;

        return Time.time - taskStartTime;
    }

    public List<RepetitionTiming> GetRepetitionTimings()
    {
        return new List<RepetitionTiming>(repetitionTimings);
    }

    public string GetStatusText()
    {
        switch (state)
        {
            case TaskState.WaitingForGrabAtNeutral:
                return "At NEUTRAL: Close hand (fist)";

            case TaskState.WaitingForReleaseAtNeutral:
                return "At NEUTRAL: Open hand";

            case TaskState.RotatingToSupination:
                float progressToSup = (CurrentRelativeAngle / targetSupinationAngle) * 100f;
                return $"Supinate to {targetSupinationAngle:F0}° ({progressToSup:F0}%)";

            case TaskState.WaitingForGrabAtSupination:
                return $"At SUPINATION ({CurrentRelativeAngle:F0}°): Close hand";

            case TaskState.WaitingForReleaseAtSupination:
                return $"At SUPINATION ({CurrentRelativeAngle:F0}°): Open hand";

            case TaskState.RotatingToNeutral:
                float progressToNeutral =
                    (1 - Mathf.Abs(CurrentRelativeAngle) / targetSupinationAngle) * 100f;
                return $"Return to neutral ({progressToNeutral:F0}%)";

            case TaskState.Complete:
                return "Task Complete!";

            default:
                return "";
        }
    }

    public string GetInstructionText()
    {
        string repInfo = $"Repetition {currentRepetition + 1}/{targetRepetitions}";

        switch (state)
        {
            case TaskState.WaitingForGrabAtNeutral:
            case TaskState.WaitingForReleaseAtNeutral:
                return $"{repInfo}\n1. Neutral: Fist → Open";

            case TaskState.RotatingToSupination:
                return $"{repInfo}\n2. Rotate to supination";

            case TaskState.WaitingForGrabAtSupination:
            case TaskState.WaitingForReleaseAtSupination:
                return $"{repInfo}\n3. Supination: Fist → Open";

            case TaskState.RotatingToNeutral:
                return $"{repInfo}\n4. Rotate back to neutral";

            case TaskState.Complete:
                return "✓ Well done!";

            default:
                return "";
        }
    }

    public string GetPhaseText()
    {
        switch (state)
        {
            case TaskState.WaitingForGrabAtNeutral:
            case TaskState.WaitingForReleaseAtNeutral:
                return "NEUTRAL";

            case TaskState.RotatingToSupination:
                return "→ SUPINATING";

            case TaskState.WaitingForGrabAtSupination:
            case TaskState.WaitingForReleaseAtSupination:
                return "SUPINATION";

            case TaskState.RotatingToNeutral:
                return "→ RETURNING";

            case TaskState.Complete:
                return "COMPLETE";

            default:
                return "";
        }
    }

    float NormalizeAngle(float angle)
    {
        while (angle > 180f)
            angle -= 360f;
        while (angle < -180f)
            angle += 360f;
        return angle;
    }

    public void ResetTask()
    {
        state = TaskState.WaitingForGrabAtNeutral;
        currentRepetition = 0;
        wasGripping = false;
        taskStartTime = Time.time;
        repetitionStartTime = -1f;
        taskCompleteTime = -1f;
        CurrentSupinationAngle = 0f;
        CurrentRelativeAngle = 0f;

        repetitionTimings.Clear();

        // Re-establish neutral reference
        if (handController)
        {
            Vector3 handRotation = handController.CurrentRotationEuler;
            initialSupinationAngle = NormalizeAngle(handRotation.z);
        }
    }
}
