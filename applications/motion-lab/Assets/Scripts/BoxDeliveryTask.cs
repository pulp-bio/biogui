// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;
using UnityEngine.Serialization;

/// <summary>
/// Task 1: Box delivery task.
/// User must grab box, move it right, and drop it in delivery zone.
/// </summary>
public class BoxDeliveryTask : ContinuousTask
{
    [Header("Task Objects")]
    public GameObject boxObject;
    public GameObject boxPrefab; // Prefab to spawn if boxObject is null
    public DeliveryZone deliveryZone;

    [Header("Spawn Settings")]
    [Tooltip("Normalized X position (-1 to 1) for box spawn")]
    public float boxSpawnNormalizedX = 0f;

    [FormerlySerializedAs("boxSpawnNormalizedY")]
    [Tooltip("Normalized Z position (-1 to 1) for box spawn")]
    public float boxSpawnNormalizedZ = 0f;

    [Tooltip("If enabled, use WorkspaceGrid objectHeight for box spawn Y")]
    public bool useWorkspaceGridObjectHeight = true;

    [Tooltip("Unity Y position for box spawn")]
    public float boxSpawnY = 0.5f;

    [Tooltip("Normalized X position (-1 to 1) for delivery zone")]
    public float deliveryZoneNormalizedX = 0.8f;

    [FormerlySerializedAs("deliveryZoneNormalizedY")]
    [Tooltip("Normalized Z position (-1 to 1) for delivery zone")]
    public float deliveryZoneNormalizedZ = 0f;

    [Tooltip("If enabled, use WorkspaceGrid deliveryZoneHeight for delivery zone Y")]
    public bool useWorkspaceGridDeliveryZoneHeight = true;

    [Tooltip("Unity Y position for delivery zone")]
    public float deliveryZoneY = 0.0f;

    [Header("Drop Zones")]
    [Tooltip("Radius around spawn treated as pickup/start — drop here does not fail the task")]
    public float pickupZoneRadius = 0.5f;

    [Header("Grab Requirements")]
    [Tooltip("If enabled, hand must be flat (near 0° supination) to grab the box")]
    public bool requireFlatHandToGrab = true;

    [Tooltip("Tolerance in degrees from neutral (0°) to allow grabbing")]
    public float flatHandTolerance = 5f;

    [Header("References")]
    [Tooltip("Reference to HandController (auto-found if null)")]
    public HandController handController;

    private Grabbable boxGrabbable;
    private Rigidbody boxRigidbody;
    private bool boxWasGrabbed = false;
    private bool boxWasDelivered = false;

    void Awake()
    {
        taskName = "Box Delivery";
        taskType = ContinuousTaskType.BoxDelivery;
    }

    void Start()
    {
        // Try to get delivery zone from ContinuousTaskManager if not assigned
        if (deliveryZone == null && ContinuousTaskManager.Instance != null)
        {
            deliveryZone = ContinuousTaskManager.Instance.deliveryZone;
            if (deliveryZone != null)
            {
                Debug.Log("[BoxDeliveryTask] Got delivery zone from ContinuousTaskManager");
            }
        }

        // Find HandController if not assigned
        if (handController == null)
        {
            handController = FindFirstObjectByType<HandController>();
        }
    }

    /// <summary>
    /// Get the actual spawn position for the box (converts from normalized grid coordinates).
    /// </summary>
    private float ResolveBoxSpawnY()
    {
        if (useWorkspaceGridObjectHeight && WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.Instance.objectHeight;
        }

        return boxSpawnY;
    }

    private Vector3 GetBoxSpawnPosition()
    {
        return WorkspaceGrid.ToWorld(
            boxSpawnNormalizedX,
            boxSpawnNormalizedZ,
            ResolveBoxSpawnY()
        );
    }

    /// <summary>
    /// Get the actual delivery zone position (converts from normalized grid coordinates).
    /// </summary>
    private float ResolveDeliveryZoneY()
    {
        if (useWorkspaceGridDeliveryZoneHeight && WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.Instance.deliveryZoneHeight;
        }

        return deliveryZoneY;
    }

    private Vector3 GetDeliveryZonePosition()
    {
        return WorkspaceGrid.ToWorld(
            deliveryZoneNormalizedX,
            deliveryZoneNormalizedZ,
            ResolveDeliveryZoneY()
        );
    }

    /// <summary>
    /// Prepare task: Setup box and delivery zone, but keep them inactive (not grabbable).
    /// </summary>
    protected override void OnTaskPrepare()
    {
        // Reset state
        boxWasGrabbed = false;
        boxWasDelivered = false;

        // Get spawn positions (from grid or legacy)
        Vector3 spawnPos = GetBoxSpawnPosition();
        Vector3 zonePos = GetDeliveryZonePosition();

        // Debug: Check if we have box references
        if (boxObject == null && boxPrefab == null)
        {
            Debug.LogError(
                "[BoxDeliveryTask] ERROR: Both boxObject and boxPrefab are null! Cannot spawn box. Please assign either boxObject or boxPrefab in the inspector."
            );
            return;
        }

        // Spawn box if needed
        if (boxObject == null && boxPrefab != null)
        {
            boxObject = Instantiate(boxPrefab, spawnPos, Quaternion.identity);
            boxObject.name = "Box_" + System.DateTime.Now.Ticks;

            Debug.Log(
                $"[BoxDeliveryTask] Spawned box at {spawnPos} (normalized X/Z: {boxSpawnNormalizedX}, {boxSpawnNormalizedZ}; Y: {boxSpawnY})"
            );
        }

        // Setup box (visible but not grabbable during countdown)
        if (boxObject != null)
        {
            boxObject.transform.position = spawnPos;
            boxObject.SetActive(true); // Visible during countdown

            // Set to Default layer (NOT grabbable yet)
            int defaultLayer = 0; // Default layer
            boxObject.layer = defaultLayer;
            SetLayerRecursively(boxObject.transform, defaultLayer);

            boxRigidbody = boxObject.GetComponent<Rigidbody>();
            if (boxRigidbody == null)
            {
                boxRigidbody = boxObject.AddComponent<Rigidbody>();
                Debug.Log("[BoxDeliveryTask] Added Rigidbody to box");
            }

            boxGrabbable = boxObject.GetComponent<Grabbable>();
            if (boxGrabbable == null)
            {
                boxGrabbable = boxObject.AddComponent<Grabbable>();
                Debug.Log("[BoxDeliveryTask] Added Grabbable to box");
            }

            // Reset physics
            boxRigidbody.linearVelocity = Vector3.zero;
            boxRigidbody.angularVelocity = Vector3.zero;
            boxRigidbody.useGravity = true;
            boxRigidbody.isKinematic = false;

            Debug.Log(
                $"[BoxDeliveryTask] Box prepared at position {boxObject.transform.position} (visible but not grabbable during countdown)"
            );
        }
        else
        {
            Debug.LogError("[BoxDeliveryTask] ERROR: boxObject is still null after spawn attempt!");
        }

        // Setup delivery zone (also keep inactive)
        if (deliveryZone == null)
        {
            Debug.LogError(
                "[BoxDeliveryTask] ERROR: deliveryZone is null! Please assign deliveryZone in the inspector or ensure ContinuousTaskManager has a deliveryZone assigned."
            );
        }
        else
        {
            deliveryZone.transform.position = zonePos;
            deliveryZone.gameObject.SetActive(true); // Visible during countdown
            deliveryZone.ClearCount();
            Debug.Log(
                $"[BoxDeliveryTask] Delivery zone prepared at {zonePos} (normalized X/Z: {deliveryZoneNormalizedX}, {deliveryZoneNormalizedZ}; Y: {deliveryZoneY})"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown (they're already visible).
    /// </summary>
    protected override void OnTaskActivate()
    {
        if (boxObject != null)
        {
            GrabbableLayerHelper.ApplyToObject(boxObject);
            Debug.Log(
                $"[BoxDeliveryTask] Box is now grabbable (layer {boxObject.layer})"
            );
        }
    }

    /// <summary>
    /// Start timing: Called when task actually starts (after countdown).
    /// </summary>
    protected override void OnTaskStart()
    {
        Debug.Log("[BoxDeliveryTask] Timing started - waiting for box grab and delivery");
    }

    protected override void OnTaskReset()
    {
        base.OnTaskReset();
        boxWasGrabbed = false;
        boxWasDelivered = false;

        // Hide or destroy objects
        if (boxObject != null)
        {
            // If spawned from prefab, destroy it; otherwise just hide
            if (boxPrefab != null && boxObject.name.StartsWith("Box_"))
            {
                Destroy(boxObject);
                boxObject = null;
            }
            else
            {
                boxObject.SetActive(false);
            }
        }
        if (deliveryZone != null)
            deliveryZone.gameObject.SetActive(false);
    }

    protected override void CheckTaskCompletion()
    {
        if (boxGrabbable == null || deliveryZone == null || boxRigidbody == null)
            return;

        // Check if box was grabbed
        if (!boxWasGrabbed && boxGrabbable.IsHeld)
        {
            boxWasGrabbed = true;
            Debug.Log("[BoxDeliveryTask] Box grabbed");
        }

        if (boxWasGrabbed && !boxWasDelivered)
        {
            bool isReleased = TaskZoneChecker.IsReleased(boxGrabbable, boxRigidbody);
            bool isInDeliveryZone = TaskZoneChecker.IsInDeliveryZone(
                deliveryZone,
                boxRigidbody,
                boxObject
            );

            if (isReleased && isInDeliveryZone)
            {
                boxWasDelivered = true;
                CompleteTask();
                Debug.Log("[BoxDeliveryTask] Box delivered! (released in delivery zone)");
            }
            else if (isReleased)
            {
                if (
                    TaskZoneChecker.IsInPickupZone(
                        GetBoxSpawnPosition(),
                        pickupZoneRadius,
                        boxRigidbody,
                        boxObject
                    )
                )
                {
                    boxWasGrabbed = false;
                    if (debugLogs)
                        Debug.Log("[BoxDeliveryTask] Released at start — retry allowed");
                }
                else
                {
                    Debug.Log("[BoxDeliveryTask] Box released outside zones — task failed");
                    FailTask("Object dropped");
                }
            }
        }
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

        if (boxWasDelivered)
            return "Delivered!";

        if (boxWasGrabbed && boxGrabbable != null && boxGrabbable.IsHeld)
            return "Move box to delivery zone";

        if (boxWasGrabbed)
            return "Drop box in delivery zone";

        if (startTime >= 0)
        {
            // Check if hand needs to be flattened before grabbing
            if (requireFlatHandToGrab && !IsHandFlat())
            {
                float currentSupination = GetCurrentSupination();
                return $"Flatten hand! ({currentSupination:F0}° → 0°)";
            }
            return "Grab the box";
        }

        return "Get ready...";
    }

    /// <summary>
    /// Check if the hand is flat enough to grab the box.
    /// </summary>
    private bool IsHandFlat()
    {
        if (handController == null)
            return true; // Allow grab if no hand controller

        float currentSupination = GetCurrentSupination();
        return Mathf.Abs(currentSupination) <= flatHandTolerance;
    }

    /// <summary>
    /// Get the current supination angle from the hand controller.
    /// </summary>
    private float GetCurrentSupination()
    {
        return HandSupination.GetDegrees(handController);
    }

    void SetLayerRecursively(Transform obj, int layer)
    {
        obj.gameObject.layer = layer;
        foreach (Transform child in obj)
        {
            SetLayerRecursively(child, layer);
        }
    }
}
