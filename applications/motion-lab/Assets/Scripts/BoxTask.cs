// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

public enum TaskType
{
    DeliverToBasket,
    SupinationRotation,
    FlexionExtensionRotation,
}

public class BoxTask : MonoBehaviour
{
    [Header("Task Config")]
    public int orderIndex = 1;
    public TaskType taskType = TaskType.DeliverToBasket;
    public Material taskMaterial;

    [Header("Rotation Task Settings")]
    public float requiredAngle = 70f;

    [HideInInspector]
    public float startTime = -1f;

    [HideInInspector]
    public float endTime = -1f;

    [HideInInspector]
    public bool isComplete = false;

    [HideInInspector]
    public bool hasReachedTarget = false; // Flex or Supination reached

    [HideInInspector]
    public bool hasReachedExtension = false; // Extension reached (FlexExt only)

    [HideInInspector]
    public bool hasReturnedToStart = false; // Back to neutral

    private Renderer _renderer;

    void Awake()
    {
        _renderer = GetComponent<Renderer>();
        if (_renderer && taskMaterial)
            _renderer.material = taskMaterial;
    }

    public void StartTask()
    {
        if (startTime < 0)
        {
            startTime = Time.time;
            Debug.Log($"BoxTask: {gameObject.name} started at {startTime:F2}s");
        }
    }

    public void CompleteTask()
    {
        if (!isComplete)
        {
            endTime = Time.time;
            isComplete = true;
            Debug.Log($"BoxTask: {gameObject.name} completed! Duration: {GetDuration():F2}s");
        }
    }

    public float GetDuration()
    {
        if (startTime < 0)
            return 0f;
        if (endTime < 0)
            return Time.time - startTime;
        return endTime - startTime;
    }

    public string GetTaskDescription()
    {
        switch (taskType)
        {
            case TaskType.DeliverToBasket:
                return "Deliver to basket";
            case TaskType.SupinationRotation:
                return $"Supination {requiredAngle}°";
            case TaskType.FlexionExtensionRotation:
                return $"Flexion/Extension {requiredAngle}°";
            default:
                return "Unknown task";
        }
    }

    public string GetProgressText(bool isHeld)
    {
        if (isComplete)
            return "Complete";

        // Before grabbing: show grab instruction
        if (!isHeld && startTime < 0)
            return $"Grab Box {orderIndex}";

        switch (taskType)
        {
            case TaskType.DeliverToBasket:
                return "Put in basket";

            case TaskType.SupinationRotation:
                if (!hasReachedTarget)
                    return $"Supinate to {requiredAngle}°";
                else if (!hasReturnedToStart)
                    return "Return to 0°";
                return $"Release Box {orderIndex}";

            case TaskType.FlexionExtensionRotation:
                if (!hasReachedTarget)
                    return $"Flex to {requiredAngle}°";
                else if (!hasReachedExtension)
                    return $"Extend to -{requiredAngle}°";
                else if (!hasReturnedToStart)
                    return "Return to 0°";
                return $"Release Box {orderIndex}";

            default:
                return "";
        }
    }
}
