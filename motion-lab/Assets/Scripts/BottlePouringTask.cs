// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Task 3: Bottle pouring task.
/// User must grab bottle, pour liquid into bowl using supination (IMU rotation).
/// </summary>
public class BottlePouringTask : ContinuousTask
{
    [Header("Task Objects")]
    public GameObject bottleObject;
    public GameObject bottlePrefab; // Prefab to spawn if bottleObject is null
    public GameObject bowlObject;
    public GameObject bowlPrefab; // Prefab to spawn if bowlObject is null

    [Header("Spawn Settings (Normalized Grid Coordinates)")]
    [Tooltip("Normalized X position (-1 to 1) for bottle spawn")]
    public float bottleSpawnNormalizedX = 0f;

    [Tooltip("Normalized Y position (-1 to 1) for bottle spawn (maps to Unity Z)")]
    public float bottleSpawnNormalizedY = 0f;

    [Tooltip("Normalized X position (-1 to 1) for bowl position")]
    public float bowlNormalizedX = 0.5f;

    [Tooltip("Normalized Y position (-1 to 1) for bowl position (maps to Unity Z)")]
    public float bowlNormalizedY = 0f;

    [Header("Grab Requirements")]
    [Tooltip("Requires hand to be at ~90° supination to grab the bottle")]
    public bool requireSupinationToGrab = true;

    [Tooltip("Target supination angle (degrees) to grab bottle")]
    public float targetSupinationAngle = 90f;

    [Tooltip("Allowed deviation from target angle (degrees) - creates range of ±tolerance")]
    public float supinationTolerance = 5f;

    public float minPouringSpeed = 0.05f;
    public float maxPouringSpeed = 0.5f;

    [Header("Hand Lift Settings")]
    [Tooltip("How much to lift hand (Unity Y) when grabbing bottle to prevent ground collision")]
    public float handLiftOnGrab = 0.15f;

    [Tooltip("How fast to lift/lower the hand (units per second)")]
    public float handLiftSpeed = 2.0f;

    [Header("References")]
    public HandController handController;

    private Grabbable bottleGrabbable;
    private Rigidbody bottleRigidbody;
    private bool bottleWasGrabbed = false;
    private bool isPouring = false;
    private float initialSupinationOnGrab = 0f; // Store supination angle when bottle was grabbed
    private LiquidWobble liquidWobble; // Shader-based liquid simulation

    // Hand lift variables
    private bool isHandLifted = false;
    private Vector3 handTargetOffset = Vector3.zero;

    void Awake()
    {
        taskName = "Bottle Pouring";
        taskType = ContinuousTaskType.BottlePouring;

        if (handController == null)
            handController = FindFirstObjectByType<HandController>();
    }

    /// <summary>
    /// Get the actual spawn position for the bottle (converts from normalized grid coordinates).
    /// </summary>
    private Vector3 GetBottleSpawnPosition()
    {
        if (WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.ToWorld(
                bottleSpawnNormalizedX,
                bottleSpawnNormalizedY,
                WorkspaceGrid.Instance.objectHeight
            );
        }
        // Fallback if no WorkspaceGrid instance
        return WorkspaceGrid.ToWorld(bottleSpawnNormalizedX, bottleSpawnNormalizedY, 0.5f);
    }

    /// <summary>
    /// Get the actual bowl position (converts from normalized grid coordinates).
    /// </summary>
    private Vector3 GetBowlPosition()
    {
        if (WorkspaceGrid.Instance != null)
        {
            // Bowl is slightly lower than object height
            float bowlHeight = WorkspaceGrid.Instance.objectHeight - 0.2f;
            return WorkspaceGrid.ToWorld(bowlNormalizedX, bowlNormalizedY, bowlHeight);
        }
        // Fallback if no WorkspaceGrid instance
        return WorkspaceGrid.ToWorld(bowlNormalizedX, bowlNormalizedY, 0.3f);
    }

    /// <summary>
    /// Prepare task: Show bottle and bowl, but don't start timing.
    /// </summary>
    protected override void OnTaskPrepare()
    {
        // Reset state
        bottleWasGrabbed = false;
        isPouring = false;

        // Get spawn positions (from grid or legacy)
        Vector3 bottlePos = GetBottleSpawnPosition();
        Vector3 bowlPos = GetBowlPosition();

        // Debug: Check if we have bottle references
        if (bottleObject == null && bottlePrefab == null)
        {
            Debug.LogError(
                "[BottlePouringTask] ERROR: Both bottleObject and bottlePrefab are null! Cannot spawn bottle. Please assign either bottleObject or bottlePrefab in the inspector."
            );
            return;
        }

        // Spawn bottle if needed
        if (bottleObject == null && bottlePrefab != null)
        {
            bottleObject = Instantiate(bottlePrefab, bottlePos, Quaternion.identity);
            bottleObject.name = "Bottle_" + System.DateTime.Now.Ticks;

            Debug.Log(
                $"[BottlePouringTask] Spawned bottle at {bottlePos} (normalized: {bottleSpawnNormalizedX}, {bottleSpawnNormalizedY})"
            );
        }

        // Spawn bowl if needed
        if (bowlObject == null && bowlPrefab != null)
        {
            bowlObject = Instantiate(bowlPrefab, bowlPos, Quaternion.identity);
            bowlObject.name = "Bowl_" + System.DateTime.Now.Ticks;
            Debug.Log(
                $"[BottlePouringTask] Spawned bowl at {bowlPos} (normalized: {bowlNormalizedX}, {bowlNormalizedY})"
            );
        }

        // Setup bottle (visible but not grabbable during countdown)
        if (bottleObject != null)
        {
            bottleObject.transform.position = bottlePos;
            bottleObject.transform.rotation = Quaternion.identity;
            bottleObject.SetActive(true); // Visible during countdown

            // Set to Default layer (NOT grabbable yet)
            int defaultLayer = 0; // Default layer
            bottleObject.layer = defaultLayer;
            SetLayerRecursively(bottleObject.transform, defaultLayer);

            bottleRigidbody = bottleObject.GetComponent<Rigidbody>();
            if (bottleRigidbody == null)
            {
                bottleRigidbody = bottleObject.AddComponent<Rigidbody>();
                Debug.Log("[BottlePouringTask] Added Rigidbody to bottle");
            }

            bottleGrabbable = bottleObject.GetComponent<Grabbable>();
            if (bottleGrabbable == null)
            {
                bottleGrabbable = bottleObject.AddComponent<Grabbable>();
                Debug.Log("[BottlePouringTask] Added Grabbable to bottle");
            }

            // Reset physics
            bottleRigidbody.linearVelocity = Vector3.zero;
            bottleRigidbody.angularVelocity = Vector3.zero;
            bottleRigidbody.useGravity = true;
            bottleRigidbody.isKinematic = false;

            // Setup liquid simulation on Fill object
            liquidWobble = SetupLiquidSimulation(bottleObject);
            if (liquidWobble != null)
            {
                // Enable external pouring control (based on hand rotation, not just tilt)
                liquidWobble.requireExternalPouring = true;
                liquidWobble.SetPouringEnabled(false);
            }

            Debug.Log(
                $"[BottlePouringTask] Bottle prepared at position {bottleObject.transform.position} (visible but not grabbable during countdown)"
            );
        }
        else
        {
            Debug.LogError(
                "[BottlePouringTask] ERROR: bottleObject is still null after spawn attempt!"
            );
        }

        // Setup bowl (visible during countdown)
        if (bowlObject == null)
        {
            Debug.LogWarning(
                "[BottlePouringTask] WARNING: bowlObject is null! Please assign bowlObject or bowlPrefab in the inspector."
            );
        }
        else
        {
            bowlObject.transform.position = bowlPos;
            bowlObject.SetActive(true); // Visible during countdown
            Debug.Log(
                $"[BottlePouringTask] Bowl prepared at {bowlPos} (normalized: {bowlNormalizedX}, {bowlNormalizedY})"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown (they're already visible).
    /// </summary>
    protected override void OnTaskActivate()
    {
        // Make bottle grabbable
        if (bottleObject != null)
        {
            // Set layer to "Grabbable" (Layer 8) so HandGrabber can detect it
            int grabbableLayer = LayerMask.NameToLayer("Grabbable");
            if (grabbableLayer != -1)
            {
                bottleObject.layer = grabbableLayer;
                // Also set layer for all children
                SetLayerRecursively(bottleObject.transform, grabbableLayer);
            }
            else
            {
                Debug.LogWarning(
                    "[BottlePouringTask] 'Grabbable' layer not found! Using Default layer. Make sure 'Grabbable' layer exists in Project Settings > Tags and Layers."
                );
            }

            Debug.Log("[BottlePouringTask] Bottle is now grabbable");
        }
    }

    /// <summary>
    /// Start timing: Called when first movement is detected.
    /// Objects are already visible from OnTaskPrepare().
    /// </summary>
    protected override void OnTaskStart()
    {
        Debug.Log("[BottlePouringTask] Timing started - grab bottle and tilt to pour");
    }

    /// <summary>
    /// Called when task completes. Reset hand lifting.
    /// </summary>
    protected override void OnTaskComplete()
    {
        base.OnTaskComplete();

        // Reset hand lifting when task completes
        isHandLifted = false;
        handTargetOffset = Vector3.zero;
        if (handController != null)
        {
            handController.SetPositionOffset(Vector3.zero);
            Debug.Log("[BottlePouringTask] Hand lifting reset on task completion");
        }
    }

    protected override void OnTaskReset()
    {
        base.OnTaskReset();
        bottleWasGrabbed = false;
        isPouring = false;

        // Reset hand lifting
        isHandLifted = false;
        handTargetOffset = Vector3.zero;
        if (handController != null)
        {
            handController.SetPositionOffset(Vector3.zero);
        }

        // Hide or destroy objects
        if (bottleObject != null)
        {
            if (bottlePrefab != null && bottleObject.name.StartsWith("Bottle_"))
            {
                Destroy(bottleObject);
                bottleObject = null;
            }
            else
            {
                bottleObject.SetActive(false);
            }
        }
        if (bowlObject != null)
        {
            if (bowlPrefab != null && bowlObject.name.StartsWith("Bowl_"))
            {
                Destroy(bowlObject);
                bowlObject = null;
            }
            else
            {
                bowlObject.SetActive(false);
            }
        }
    }

    protected override void CheckTaskCompletion()
    {
        if (bottleGrabbable == null)
            return;

        // ─────────────────────────────────────────────────────────────────
        // Auto-lift hand when grabbing bottle
        // ─────────────────────────────────────────────────────────────────
        bool shouldLift = bottleGrabbable.IsHeld;

        if (shouldLift && !isHandLifted)
        {
            // Start lifting
            isHandLifted = true;
        }
        else if (!shouldLift && isHandLifted)
        {
            // Start lowering
            isHandLifted = false;
        }

        // Smoothly interpolate hand offset
        Vector3 targetOffset = isHandLifted ? new Vector3(0, handLiftOnGrab, 0) : Vector3.zero;
        handTargetOffset = Vector3.MoveTowards(
            handTargetOffset,
            targetOffset,
            handLiftSpeed * Time.deltaTime
        );

        // Apply offset to hand controller
        if (handController != null)
        {
            handController.SetPositionOffset(handTargetOffset);
        }

        // Check if bottle was grabbed
        if (!bottleWasGrabbed && bottleGrabbable.IsHeld)
        {
            bottleWasGrabbed = true;
            // Store initial supination when grabbed
            if (handController != null)
            {
                initialSupinationOnGrab = GetCurrentSupination();
                Debug.Log(
                    $"[BottlePouringTask] Bottle grabbed at supination: {initialSupinationOnGrab:F1}°"
                );
            }
        }

        // Check pouring state - based on hand rotation from grab angle
        if (bottleWasGrabbed && bottleGrabbable.IsHeld && bottleObject != null)
        {
            if (handController != null)
            {
                float currentSupination = GetCurrentSupination();

                // Pouring happens when supination is 0° or less (hand rotated back from grab position)
                bool canPour = currentSupination <= 0f;

                // Calculate pour rate based on how far below 0° we are
                // 0° = minPouringSpeed, -45° = maxPouringSpeed
                float pourRate = minPouringSpeed;
                if (canPour)
                {
                    float pronationAmount = Mathf.Abs(currentSupination); // How far below 0° (0 to 45)
                    float t = Mathf.Clamp01(pronationAmount / HandRotationLimits.POUR_ANGLE_RANGE); // 0 at 0°, 1 at -45°
                    pourRate = Mathf.Lerp(minPouringSpeed, maxPouringSpeed, t);
                }

                if (canPour && !isPouring)
                {
                    isPouring = true;
                    if (liquidWobble != null)
                    {
                        liquidWobble.SetPouringEnabled(true);
                        liquidWobble.SetPourRate(pourRate);
                    }
                    Debug.Log(
                        $"[BottlePouringTask] Pouring started - supination: {currentSupination:F1}°, speed: {pourRate:F2}"
                    );
                }
                else if (canPour && isPouring && liquidWobble != null)
                {
                    // Update pour rate based on current angle
                    liquidWobble.SetPourRate(pourRate);
                }

                if (!canPour && isPouring)
                {
                    isPouring = false;
                    if (liquidWobble != null)
                    {
                        liquidWobble.SetPouringEnabled(false);
                        liquidWobble.SetPourRate(0f);
                    }
                    Debug.Log(
                        $"[BottlePouringTask] Pouring stopped - supination: {currentSupination:F1}°"
                    );
                }

                // Check if liquid is empty (task completion)
                if (liquidWobble != null)
                {
                    float liquidLevel = liquidWobble.GetFillAmount();

                    if (liquidLevel <= 0)
                    {
                        CompleteTask();
                        Debug.Log(
                            $"[BottlePouringTask] Pouring complete! Liquid level: {liquidLevel * 100f:F1}%"
                        );
                    }
                }
            }
        }
        else if (bottleWasGrabbed && !bottleGrabbable.IsHeld)
        {
            // Released before completing
            isPouring = false;
            if (liquidWobble != null)
            {
                liquidWobble.SetPouringEnabled(false);
            }
            initialSupinationOnGrab = 0f;
        }
    }

    /// <summary>
    /// Get current task status for UI display
    /// </summary>
    public string GetStatusText()
    {
        if (isComplete)
            return "Complete!";

        if (bottleWasGrabbed && bottleGrabbable != null && bottleGrabbable.IsHeld)
        {
            if (handController != null)
            {
                // Show liquid level
                if (liquidWobble != null)
                {
                    float liquidLevel = liquidWobble.GetFillAmount();
                    if (isPouring)
                    {
                        return $"Pouring...\n{liquidLevel * 100f:F0}% remaining";
                    }
                    else
                    {
                        return $"Rotate hand back to pour\n{liquidLevel * 100f:F0}% remaining";
                    }
                }
                else
                {
                    if (isPouring)
                    {
                        return "Pouring...";
                    }
                    else
                    {
                        return "Rotate hand back to pour";
                    }
                }
            }
            return "Rotate hand back to pour";
        }

        if (bottleWasGrabbed)
            return "Grab bottle again";

        if (startTime >= 0)
        {
            if (requireSupinationToGrab && handController != null)
            {
                float currentSup = GetCurrentSupination();
                float minAngle = targetSupinationAngle - supinationTolerance;
                float maxAngle = targetSupinationAngle + supinationTolerance;

                if (currentSup >= minAngle && currentSup <= maxAngle)
                {
                    return "Grab the bottle!";
                }
                else
                {
                    return $"Rotate hand to {targetSupinationAngle:F0}°\nCurrent: {currentSup:F0}°";
                }
            }
            return "Grab the bottle";
        }

        return "Get ready...";
    }


    float GetCurrentSupination()
    {
        if (handController == null)
            return 0f;

        Vector3 handRotation = handController.CurrentRotationEuler;
        float currentSupinationZ = NormalizeAngle(handRotation.z);
        return -handController.HandednessMultiplier * currentSupinationZ;
    }

    float NormalizeAngle(float angle)
    {
        while (angle > 180f)
            angle -= 360f;
        while (angle < -180f)
            angle += 360f;
        return angle;
    }

    void SetLayerRecursively(Transform obj, int layer)
    {
        obj.gameObject.layer = layer;
        foreach (Transform child in obj)
        {
            SetLayerRecursively(child, layer);
        }
    }

    LiquidWobble SetupLiquidSimulation(GameObject bottle)
    {
        // Find the Fill object (liquid) in the bottle hierarchy
        Transform fillTransform = null;

        // Search for Fill in children
        foreach (Transform child in bottle.transform)
        {
            if (child.name.Contains("Fill") || child.name.Contains("fill"))
            {
                fillTransform = child;
                break;
            }
        }

        if (fillTransform != null)
        {
            // Add LiquidWobble component if not already present
            LiquidWobble wobble = fillTransform.GetComponent<LiquidWobble>();
            if (wobble == null)
            {
                wobble = fillTransform.gameObject.AddComponent<LiquidWobble>();
                wobble.containerTransform = bottle.transform;
                wobble.fillAmount = 1f; // Start full
                Debug.Log($"[BottlePouringTask] Added LiquidWobble to {fillTransform.name}");
            }
            else
            {
                // Make sure container reference is set
                if (wobble.containerTransform == null)
                {
                    wobble.containerTransform = bottle.transform;
                }
            }
            return wobble;
        }
        else
        {
            Debug.LogWarning(
                $"[BottlePouringTask] Could not find Fill object in bottle {bottle.name}. Liquid simulation will not work."
            );
            return null;
        }
    }
}
