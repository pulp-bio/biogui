// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

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

    [Header("Spawn Settings (Normalized Grid Coordinates)")]
    [Tooltip("Normalized X position (-1 to 1) for box spawn")]
    public float boxSpawnNormalizedX = 0f;

    [Tooltip("Normalized Y position (-1 to 1) for box spawn (maps to Unity Z)")]
    public float boxSpawnNormalizedY = 0f;

    [Tooltip("Normalized X position (-1 to 1) for delivery zone")]
    public float deliveryZoneNormalizedX = 0.8f;

    [Tooltip("Normalized Y position (-1 to 1) for delivery zone (maps to Unity Z)")]
    public float deliveryZoneNormalizedY = 0f;

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
    private Vector3 GetBoxSpawnPosition()
    {
        if (WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.ToWorld(
                boxSpawnNormalizedX,
                boxSpawnNormalizedY,
                WorkspaceGrid.Instance.objectHeight
            );
        }
        // Fallback if no WorkspaceGrid instance
        return WorkspaceGrid.ToWorld(boxSpawnNormalizedX, boxSpawnNormalizedY, 0.5f);
    }

    /// <summary>
    /// Get the actual delivery zone position (converts from normalized grid coordinates).
    /// </summary>
    private Vector3 GetDeliveryZonePosition()
    {
        if (WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.ToWorld(
                deliveryZoneNormalizedX,
                deliveryZoneNormalizedY,
                WorkspaceGrid.Instance.deliveryZoneHeight
            );
        }
        // Fallback if no WorkspaceGrid instance
        return WorkspaceGrid.ToWorld(deliveryZoneNormalizedX, deliveryZoneNormalizedY, 0.0f);
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
                $"[BoxDeliveryTask] Spawned box at {spawnPos} (normalized: {boxSpawnNormalizedX}, {boxSpawnNormalizedY})"
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
                $"[BoxDeliveryTask] Delivery zone prepared at {zonePos} (normalized: {deliveryZoneNormalizedX}, {deliveryZoneNormalizedY})"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown (they're already visible).
    /// </summary>
    protected override void OnTaskActivate()
    {
        // Make box grabbable
        if (boxObject != null)
        {
            // Set layer to "Grabbable" (Layer 8) so HandGrabber can detect it
            int grabbableLayer = LayerMask.NameToLayer("Grabbable");
            if (grabbableLayer != -1)
            {
                boxObject.layer = grabbableLayer;
                // Also set layer for all children
                SetLayerRecursively(boxObject.transform, grabbableLayer);
            }
            else
            {
                Debug.LogWarning(
                    "[BoxDeliveryTask] 'Grabbable' layer not found! Using Default layer. Make sure 'Grabbable' layer exists in Project Settings > Tags and Layers."
                );
            }

            Debug.Log("[BoxDeliveryTask] Box is now grabbable");
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

        // Check if box was delivered (not held and in delivery zone)
        if (boxWasGrabbed && !boxWasDelivered)
        {
            // Box must be released (not held) AND in delivery zone
            bool isReleased = !boxGrabbable.IsHeld;

            // Check if box is in delivery zone using multiple methods for reliability
            Collider zoneCollider = deliveryZone.GetComponent<Collider>();
            bool isInZone = false;

            if (zoneCollider != null)
            {
                // Method 1: Check if box center is within zone bounds
                Vector3 boxPos = boxRigidbody.worldCenterOfMass;
                Bounds zoneBounds = zoneCollider.bounds;
                isInZone = zoneBounds.Contains(boxPos);

                // Method 2: Also check box transform position (more reliable for trigger colliders)
                if (!isInZone)
                {
                    Vector3 boxTransformPos = boxObject.transform.position;
                    isInZone = zoneBounds.Contains(boxTransformPos);
                }

                // Method 3: Check if any part of box collider overlaps with zone
                if (!isInZone && boxObject != null)
                {
                    Collider boxCollider = boxObject.GetComponent<Collider>();
                    if (boxCollider != null)
                    {
                        isInZone = zoneBounds.Intersects(boxCollider.bounds);
                    }
                }
            }

            if (isReleased && isInZone)
            {
                boxWasDelivered = true;
                CompleteTask();
                Debug.Log("[BoxDeliveryTask] Box delivered! (released in delivery zone)");
            }
            else if (isReleased && !isInZone)
            {
                // Box was released but not in zone - reset grab state so user can try again
                if (debugLogs)
                    Debug.Log(
                        $"[BoxDeliveryTask] Box released but not in delivery zone. Box pos: {boxRigidbody.worldCenterOfMass}, Zone bounds: {zoneCollider.bounds}"
                    );
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
        if (handController == null)
            return 0f;

        Vector3 handRotation = handController.CurrentRotationEuler;
        float supinationZ = NormalizeAngle(handRotation.z);

        // Reverse the handedness multiplier to get actual supination
        return -handController.HandednessMultiplier * supinationZ;
    }

    /// <summary>
    /// Normalize angle to -180 to 180 range.
    /// </summary>
    private float NormalizeAngle(float angle)
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
}
