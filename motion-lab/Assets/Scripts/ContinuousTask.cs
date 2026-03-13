using UnityEngine;

/// <summary>
/// Base class for all continuous tasks.
/// Provides common interface for task lifecycle management.
/// </summary>
public abstract class ContinuousTask : MonoBehaviour
{
    [HideInInspector]
    public string taskName = "Unnamed Task";

    [HideInInspector]
    public ContinuousTaskType taskType;

    [HideInInspector]
    public float startTime = -1f;

    [HideInInspector]
    public float endTime = -1f;

    [HideInInspector]
    public bool isComplete = false;

    [HideInInspector]
    public bool isPrepared = false; // Whether task objects are visible and ready

    [HideInInspector]
    public bool isActivated = false; // Whether task objects are activated (grabbable)

    /// <summary>
    /// Prepare task: Setup task but keep objects inactive (not grabbable).
    /// Called when task is selected but countdown hasn't finished.
    /// </summary>
    public virtual void PrepareTask()
    {
        if (!isPrepared)
        {
            isPrepared = true;
            OnTaskPrepare();
            Debug.Log(
                $"[ContinuousTask] {taskName} prepared (objects ready but not grabbable yet)"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown.
    /// Called when countdown finishes and task is ready to start.
    /// </summary>
    public virtual void ActivateTask()
    {
        if (!isActivated)
        {
            isActivated = true;
            OnTaskActivate();
            Debug.Log(
                $"[ContinuousTask] {taskName} activated (objects now grabbable)"
            );
        }
    }

    /// <summary>
    /// Start timing: Begin time tracking. Objects should already be visible.
    /// Called when first movement/gesture is detected.
    /// </summary>
    public virtual void StartTiming()
    {
        if (startTime < 0)
        {
            startTime = Time.time;
            isComplete = false;
            endTime = -1f;
            OnTaskStart();
            Debug.Log($"[ContinuousTask] {taskName} timing started at {startTime:F2}s");
        }
    }

    /// <summary>
    /// Called when task should start. Reset state and begin task.
    /// This does both PrepareTask() and StartTiming() for backwards compatibility.
    /// </summary>
    public virtual void StartTask()
    {
        PrepareTask();
        StartTiming();
    }

    /// <summary>
    /// Called when task is completed. Mark as complete and record time.
    /// </summary>
    public virtual void CompleteTask()
    {
        if (!isComplete)
        {
            endTime = Time.time;
            isComplete = true;
            OnTaskComplete();
            Debug.Log($"[ContinuousTask] {taskName} completed! Duration: {GetDuration():F2}s");
        }
    }

    /// <summary>
    /// Reset task to initial state. Called when switching tasks.
    /// </summary>
    public virtual void ResetTask()
    {
        startTime = -1f;
        endTime = -1f;
        isComplete = false;
        isPrepared = false;
        isActivated = false;
        OnTaskReset();
    }

    /// <summary>
    /// Get duration of task in seconds.
    /// </summary>
    public float GetDuration()
    {
        if (startTime < 0)
            return 0f;
        if (endTime < 0)
            return Time.time - startTime;
        return endTime - startTime;
    }

    /// <summary>
    /// Check if task is currently active (started but not complete).
    /// </summary>
    public bool IsActive()
    {
        return startTime >= 0 && !isComplete;
    }

    /// <summary>
    /// Override to implement task-specific preparation logic (setup objects but keep them non-grabbable).
    /// Called when task is selected but countdown hasn't finished yet.
    /// </summary>
    protected virtual void OnTaskPrepare() { }

    /// <summary>
    /// Override to implement task-specific activation logic (make objects grabbable).
    /// Called when countdown finishes and objects should become interactive.
    /// </summary>
    protected virtual void OnTaskActivate() { }

    /// <summary>
    /// Override to implement task-specific start logic (start timing).
    /// Called when timing should begin (after countdown and activation).
    /// </summary>
    protected virtual void OnTaskStart() { }

    /// <summary>
    /// Override to implement task-specific completion logic.
    /// </summary>
    protected virtual void OnTaskComplete() { }

    /// <summary>
    /// Override to implement task-specific reset logic.
    /// </summary>
    protected virtual void OnTaskReset() { }

    /// <summary>
    /// Called every frame. Override to implement task-specific update logic.
    /// </summary>
    protected virtual void Update()
    {
        if (IsActive())
        {
            CheckTaskCompletion();
        }
    }

    /// <summary>
    /// Override to implement task-specific completion checking.
    /// </summary>
    protected virtual void CheckTaskCompletion() { }
}

/// <summary>
/// Task type enumeration for different continuous task types.
/// </summary>
public enum ContinuousTaskType
{
    BoxDelivery,
    CylinderDelivery,
    BottlePouring,
    MarbleDelivery,
}
