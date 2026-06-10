// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;
using UnityEngine.Serialization;

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

    [Header("Spawn Settings")]
    [Tooltip("Normalized X position (-1 to 1) for bottle spawn")]
    public float bottleSpawnNormalizedX = 0f;

    [FormerlySerializedAs("bottleSpawnNormalizedY")]
    [Tooltip("Normalized Z position (-1 to 1) for bottle spawn")]
    public float bottleSpawnNormalizedZ = 0f;

    [Tooltip("If enabled, use WorkspaceGrid objectHeight for bottle spawn Y")]
    public bool useWorkspaceGridBottleHeight = true;

    [Tooltip("Unity Y position for bottle spawn")]
    public float bottleSpawnY = 0.5f;

    [Tooltip("Additional upward spawn offset for the bottle to avoid starting slightly inside the table")]
    public float bottleSpawnLift = 0.5f;

    [Tooltip("Normalized X position (-1 to 1) for bowl position")]
    public float bowlNormalizedX = 0.5f;

    [FormerlySerializedAs("bowlNormalizedY")]
    [Tooltip("Normalized Z position (-1 to 1) for bowl position")]
    public float bowlNormalizedZ = 0f;

    [Tooltip("If enabled, derive bowl Y from WorkspaceGrid objectHeight with the legacy -0.2 offset")]
    public bool useWorkspaceGridBowlHeight = true;

    [Tooltip("Unity Y position for bowl position")]
    public float bowlY = 0.3f;

    [Header("Grab Requirements")]
    [Tooltip("Requires hand to be at ~90° supination to grab the bottle")]
    public bool requireSupinationToGrab = true;

    [Tooltip("Target supination angle (degrees) to grab bottle")]
    public float targetSupinationAngle = 90f;

    [Tooltip("Allowed deviation from target angle (degrees) - creates range of ±tolerance")]
    public float supinationTolerance = 5f;

    [Tooltip("Degrees of rotation back from grab angle before liquid starts pouring")]
    public float minRotationToPour = 90f;

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
    private bool grabbedAtValidSupination = false;
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
    private float ResolveBottleSpawnY()
    {
        float baseY;
        if (useWorkspaceGridBottleHeight && WorkspaceGrid.Instance != null)
        {
            baseY = WorkspaceGrid.Instance.objectHeight;
        }
        else
        {
            baseY = bottleSpawnY;
        }

        return baseY + bottleSpawnLift;
    }

    private Vector3 GetBottleSpawnPosition()
    {
        return WorkspaceGrid.ToWorld(
            bottleSpawnNormalizedX,
            bottleSpawnNormalizedZ,
            ResolveBottleSpawnY()
        );
    }

    /// <summary>
    /// Get the actual bowl position (converts from normalized grid coordinates).
    /// </summary>
    private float ResolveBowlY()
    {
        if (useWorkspaceGridBowlHeight && WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.Instance.objectHeight - 0.2f;
        }

        return bowlY;
    }

    private Vector3 GetBowlPosition()
    {
        return WorkspaceGrid.ToWorld(bowlNormalizedX, bowlNormalizedZ, ResolveBowlY());
    }

    /// <summary>
    /// Prepare task: Show bottle and bowl, but don't start timing.
    /// </summary>
    protected override void OnTaskPrepare()
    {
        // Reset state
        bottleWasGrabbed = false;
        grabbedAtValidSupination = false;
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
                $"[BottlePouringTask] Spawned bottle at {bottlePos} (normalized X/Z: {bottleSpawnNormalizedX}, {bottleSpawnNormalizedZ}; Y: {bottleSpawnY})"
            );
        }

        // Spawn bowl if needed
        if (bowlObject == null && bowlPrefab != null)
        {
            bowlObject = Instantiate(bowlPrefab, bowlPos, Quaternion.identity);
            bowlObject.name = "Bowl_" + System.DateTime.Now.Ticks;
            Debug.Log(
                $"[BottlePouringTask] Spawned bowl at {bowlPos} (normalized X/Z: {bowlNormalizedX}, {bowlNormalizedZ}; Y: {bowlY})"
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
                ConfigureLiquidPouring(liquidWobble);
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
                $"[BottlePouringTask] Bowl prepared at {bowlPos} (normalized X/Z: {bowlNormalizedX}, {bowlNormalizedZ}; Y: {bowlY})"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown (they're already visible).
    /// </summary>
    protected override void OnTaskActivate()
    {
        if (bottleObject != null)
        {
            GrabbableLayerHelper.ApplyToObject(bottleObject);
            Debug.Log(
                $"[BottlePouringTask] Bottle is now grabbable (layer {bottleObject.layer})"
            );
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
        grabbedAtValidSupination = false;
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

        // Check if bottle was grabbed at valid supination (~90°)
        if (!bottleWasGrabbed && bottleGrabbable.IsHeld)
        {
            float grabSupination = HandSupination.GetDegrees(handController);
            if (IsSupinationValidForGrab(grabSupination))
            {
                bottleWasGrabbed = true;
                grabbedAtValidSupination = true;
                initialSupinationOnGrab = grabSupination;
                Debug.Log(
                    $"[BottlePouringTask] Bottle grabbed at supination: {initialSupinationOnGrab:F1}°"
                );
            }
            else if (debugLogs)
            {
                Debug.Log(
                    $"[BottlePouringTask] Ignoring grab at {grabSupination:F1}° — need {targetSupinationAngle:F0}°±{supinationTolerance:F0}°"
                );
            }
        }

        // Pour only after valid grab at ~90° and rotating back toward neutral
        if (bottleWasGrabbed && bottleGrabbable.IsHeld && bottleObject != null)
        {
            if (handController != null)
            {
                float currentSupination = HandSupination.GetDegrees(handController);
                float rotationFromGrab = HandSupination.RotationFromGrab(
                    initialSupinationOnGrab,
                    currentSupination
                );
                bool canPour = CanPourAtSupination(rotationFromGrab);

                float pourRate = minPouringSpeed;
                if (canPour)
                {
                    float t = Mathf.Clamp01(rotationFromGrab / minRotationToPour);
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
        else if (
            bottleWasGrabbed
            && TaskZoneChecker.IsReleased(bottleGrabbable, bottleRigidbody)
        )
        {
            isPouring = false;
            isHandLifted = false;
            handTargetOffset = Vector3.zero;
            if (handController != null)
                handController.SetPositionOffset(Vector3.zero);

            if (liquidWobble != null)
            {
                liquidWobble.SetPouringEnabled(false);
                liquidWobble.SetPourRate(0f);
            }

            Debug.Log("[BottlePouringTask] Bottle released — task failed");
            FailTask("Bottle dropped");
        }
    }

    /// <summary>
    /// True when supination is within the configured grab window (default ~90° ± 5°).
    /// </summary>
    public bool IsSupinationValidForGrab(float supination)
    {
        if (!requireSupinationToGrab)
            return true;

        return HandSupination.IsWithinTarget(
            supination,
            targetSupinationAngle,
            supinationTolerance
        );
    }

    /// <summary>
    /// True when the hand has rotated back at least minRotationToPour from the grab pose.
    /// </summary>
    public bool CanPourAtSupination(float rotationFromGrabDegrees)
    {
        if (!grabbedAtValidSupination)
            return false;

        return rotationFromGrabDegrees >= minRotationToPour;
    }

    void OnValidate()
    {
        supinationTolerance = Mathf.Clamp(supinationTolerance, 0f, 15f);
        minRotationToPour = Mathf.Max(1f, minRotationToPour);
    }

    static void ConfigureLiquidPouring(LiquidWobble wobble)
    {
        wobble.requireExternalPouring = true;
        wobble.SetPouringEnabled(false);
        wobble.SetPourRate(0f);
    }

    [Header("Debug")]
    public bool debugLogs = false;

    /// <summary>
    /// Get current task status for UI display
    /// </summary>
    public string GetStatusText()
    {
        if (isFailed)
            return failureMessage;

        if (isComplete)
            return "Complete!";

        if (bottleWasGrabbed && bottleGrabbable != null && bottleGrabbable.IsHeld)
        {
            float currentSup = HandSupination.GetDegrees(handController);
            float rotationFromGrab = HandSupination.RotationFromGrab(
                initialSupinationOnGrab,
                currentSup
            );
            float progressDeg = Mathf.Clamp(rotationFromGrab, 0f, minRotationToPour);
            int pourProgressPercent = Mathf.RoundToInt(
                100f * progressDeg / minRotationToPour
            );

            if (liquidWobble != null)
            {
                int liquidPercent = Mathf.RoundToInt(liquidWobble.GetFillAmount() * 100f);
                if (isPouring)
                    return $"Pouring into bowl\nBottle: {liquidPercent}% full";

                if (pourProgressPercent >= 100)
                    return $"Tip further to pour faster\nBottle: {liquidPercent}% full";

                return $"Rotate hand down to pour\nPour ready: {pourProgressPercent}%";
            }

            if (isPouring)
                return "Pouring into bowl";

            return $"Rotate hand down to pour\nPour ready: {pourProgressPercent}%";
        }

        if (startTime >= 0)
        {
            if (requireSupinationToGrab && handController != null)
            {
                float currentSup = HandSupination.GetDegrees(handController);

                if (IsSupinationValidForGrab(currentSup))
                    return "Grab the bottle";

                return $"Rotate to {targetSupinationAngle:F0}° (sideways)\n"
                    + $"Your rotation: {currentSup:F0}°";
            }

            return "Grab the bottle";
        }

        return "Get ready...";
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
            if (wobble.containerTransform == null)
                wobble.containerTransform = bottle.transform;

            ConfigureLiquidPouring(wobble);
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
