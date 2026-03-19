// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Task: Marble delivery task.
/// User must pinch (thumb+index grip) the marble, move it, and drop it in delivery zone.
/// Unlike box/cylinder, marble requires a precision pinch grip instead of a full hand grab.
/// </summary>
public class MarbleDeliveryTask : ContinuousTask
{
    [Header("Task Objects")]
    public GameObject marbleObject;
    public GameObject marblePrefab; // Prefab to spawn if marbleObject is null
    public DeliveryZone deliveryZone;

    [Header("Spawn Settings (Normalized Grid Coordinates)")]
    [Tooltip("Normalized X position (-1 to 1) for marble spawn")]
    public float marbleSpawnNormalizedX = 0f;

    [Tooltip("Normalized Y position (-1 to 1) for marble spawn (maps to Unity Z)")]
    public float marbleSpawnNormalizedY = 0f;

    [Tooltip("Normalized X position (-1 to 1) for delivery zone")]
    public float deliveryZoneNormalizedX = 0.8f;

    [Tooltip("Normalized Y position (-1 to 1) for delivery zone (maps to Unity Z)")]
    public float deliveryZoneNormalizedY = 0f;

    private Grabbable marbleGrabbable;
    private Rigidbody marbleRigidbody;
    private bool marbleWasGrabbed = false;
    private bool marbleWasDelivered = false;

    void Awake()
    {
        taskName = "Marble Delivery";
        taskType = ContinuousTaskType.MarbleDelivery;
    }

    void Start()
    {
        // Try to get delivery zone from ContinuousTaskManager if not assigned
        if (deliveryZone == null && ContinuousTaskManager.Instance != null)
        {
            deliveryZone = ContinuousTaskManager.Instance.deliveryZone;
            if (deliveryZone != null)
            {
                Debug.Log("[MarbleDeliveryTask] Got delivery zone from ContinuousTaskManager");
            }
        }
    }

    /// <summary>
    /// Get the actual spawn position for the marble (converts from normalized grid coordinates).
    /// </summary>
    private Vector3 GetMarbleSpawnPosition()
    {
        if (WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.ToWorld(
                marbleSpawnNormalizedX,
                marbleSpawnNormalizedY,
                WorkspaceGrid.Instance.objectHeight
            );
        }
        // Fallback if no WorkspaceGrid instance
        return WorkspaceGrid.ToWorld(marbleSpawnNormalizedX, marbleSpawnNormalizedY, 0.5f);
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
    /// Prepare task: Setup marble and delivery zone, but keep them inactive (not grabbable).
    /// </summary>
    protected override void OnTaskPrepare()
    {
        // Reset state
        marbleWasGrabbed = false;
        marbleWasDelivered = false;

        // Get spawn positions (from grid or legacy)
        Vector3 spawnPos = GetMarbleSpawnPosition();
        Vector3 zonePos = GetDeliveryZonePosition();

        // Debug: Check if we have marble references
        if (marbleObject == null && marblePrefab == null)
        {
            Debug.LogError(
                "[MarbleDeliveryTask] ERROR: Both marbleObject and marblePrefab are null! Cannot spawn marble. Please assign either marbleObject or marblePrefab in the inspector."
            );
            return;
        }

        // Spawn marble if needed
        if (marbleObject == null && marblePrefab != null)
        {
            marbleObject = Instantiate(marblePrefab, spawnPos, Quaternion.identity);
            marbleObject.name = "Marble_" + System.DateTime.Now.Ticks;

            Debug.Log(
                $"[MarbleDeliveryTask] Spawned marble at {spawnPos} (normalized: {marbleSpawnNormalizedX}, {marbleSpawnNormalizedY})"
            );
        }

        // Setup marble (visible but not grabbable during countdown)
        if (marbleObject != null)
        {
            marbleObject.transform.position = spawnPos;
            marbleObject.SetActive(true); // Visible during countdown

            // Set to Default layer (NOT grabbable yet)
            int defaultLayer = 0; // Default layer
            marbleObject.layer = defaultLayer;
            SetLayerRecursively(marbleObject.transform, defaultLayer);

            marbleRigidbody = marbleObject.GetComponent<Rigidbody>();
            if (marbleRigidbody == null)
            {
                marbleRigidbody = marbleObject.AddComponent<Rigidbody>();
                marbleRigidbody.mass = 0.01f; // Light marble
                Debug.Log("[MarbleDeliveryTask] Added Rigidbody to marble");
            }

            // Ensure marble has a sphere collider
            SphereCollider sphereCollider = marbleObject.GetComponent<SphereCollider>();
            if (sphereCollider == null)
            {
                sphereCollider = marbleObject.AddComponent<SphereCollider>();
                Debug.Log("[MarbleDeliveryTask] Added SphereCollider to marble");
            }

            marbleGrabbable = marbleObject.GetComponent<Grabbable>();
            if (marbleGrabbable == null)
            {
                marbleGrabbable = marbleObject.AddComponent<Grabbable>();
                Debug.Log("[MarbleDeliveryTask] Added Grabbable to marble");
            }

            // Reset physics
            marbleRigidbody.linearVelocity = Vector3.zero;
            marbleRigidbody.angularVelocity = Vector3.zero;
            marbleRigidbody.useGravity = true;
            marbleRigidbody.isKinematic = false;

            Debug.Log(
                $"[MarbleDeliveryTask] Marble prepared at position {marbleObject.transform.position} (visible but not grabbable during countdown)"
            );
        }
        else
        {
            Debug.LogError(
                "[MarbleDeliveryTask] ERROR: marbleObject is still null after spawn attempt!"
            );
        }

        // Setup delivery zone (also keep inactive)
        if (deliveryZone == null)
        {
            Debug.LogError(
                "[MarbleDeliveryTask] ERROR: deliveryZone is null! Please assign deliveryZone in the inspector or ensure ContinuousTaskManager has a deliveryZone assigned."
            );
        }
        else
        {
            deliveryZone.transform.position = zonePos;
            deliveryZone.gameObject.SetActive(true); // Visible during countdown
            deliveryZone.ClearCount();
            Debug.Log(
                $"[MarbleDeliveryTask] Delivery zone prepared at {zonePos} (normalized: {deliveryZoneNormalizedX}, {deliveryZoneNormalizedY})"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown (they're already visible).
    /// </summary>
    protected override void OnTaskActivate()
    {
        // Make marble grabbable
        if (marbleObject != null)
        {
            // Set layer to "Grabbable" (Layer 8) so HandGrabber can detect it
            int grabbableLayer = LayerMask.NameToLayer("Grabbable");
            if (grabbableLayer != -1)
            {
                marbleObject.layer = grabbableLayer;
                // Also set layer for all children
                SetLayerRecursively(marbleObject.transform, grabbableLayer);
            }
            else
            {
                Debug.LogWarning(
                    "[MarbleDeliveryTask] 'Grabbable' layer not found! Using Default layer. Make sure 'Grabbable' layer exists in Project Settings > Tags and Layers."
                );
            }

            Debug.Log("[MarbleDeliveryTask] Marble is now grabbable");
        }
    }

    /// <summary>
    /// Start timing: Called when task actually starts (after countdown).
    /// </summary>
    protected override void OnTaskStart()
    {
        Debug.Log("[MarbleDeliveryTask] Timing started - waiting for marble pinch and delivery");
    }

    protected override void OnTaskReset()
    {
        base.OnTaskReset();
        marbleWasGrabbed = false;
        marbleWasDelivered = false;

        // Hide or destroy objects
        if (marbleObject != null)
        {
            // If spawned from prefab, destroy it; otherwise just hide
            if (marblePrefab != null && marbleObject.name.StartsWith("Marble_"))
            {
                Destroy(marbleObject);
                marbleObject = null;
            }
            else
            {
                marbleObject.SetActive(false);
            }
        }
        if (deliveryZone != null)
            deliveryZone.gameObject.SetActive(false);
    }

    protected override void CheckTaskCompletion()
    {
        if (marbleGrabbable == null || deliveryZone == null || marbleRigidbody == null)
            return;

        // Check if marble was grabbed (pinched)
        if (!marbleWasGrabbed && marbleGrabbable.IsHeld)
        {
            marbleWasGrabbed = true;
            Debug.Log("[MarbleDeliveryTask] Marble pinched!");
        }

        // Check if marble was delivered (not held and in delivery zone)
        if (marbleWasGrabbed && !marbleWasDelivered)
        {
            // Marble must be released (not held) AND in delivery zone
            bool isReleased = !marbleGrabbable.IsHeld;

            // Check if marble is in delivery zone using multiple methods for reliability
            Collider zoneCollider = deliveryZone.GetComponent<Collider>();
            bool isInZone = false;

            if (zoneCollider != null)
            {
                // Method 1: Check if marble center is within zone bounds
                Vector3 marblePos = marbleRigidbody.worldCenterOfMass;
                Bounds zoneBounds = zoneCollider.bounds;
                isInZone = zoneBounds.Contains(marblePos);

                // Method 2: Also check marble transform position (more reliable for trigger colliders)
                if (!isInZone)
                {
                    Vector3 marbleTransformPos = marbleObject.transform.position;
                    isInZone = zoneBounds.Contains(marbleTransformPos);
                }

                // Method 3: Check if any part of marble collider overlaps with zone
                if (!isInZone && marbleObject != null)
                {
                    Collider marbleCollider = marbleObject.GetComponent<Collider>();
                    if (marbleCollider != null)
                    {
                        isInZone = zoneBounds.Intersects(marbleCollider.bounds);
                    }
                }
            }

            if (isReleased && isInZone)
            {
                marbleWasDelivered = true;
                CompleteTask();
                Debug.Log("[MarbleDeliveryTask] Marble delivered! (released in delivery zone)");
            }
            else if (isReleased && !isInZone)
            {
                // Marble was released but not in zone - log for debugging
                if (debugLogs)
                    Debug.Log(
                        $"[MarbleDeliveryTask] Marble released but not in delivery zone. Marble pos: {marbleRigidbody.worldCenterOfMass}, Zone bounds: {zoneCollider.bounds}"
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

        if (marbleWasDelivered)
            return "Delivered!";

        if (marbleWasGrabbed && marbleGrabbable != null && marbleGrabbable.IsHeld)
            return "Move marble to delivery zone";

        if (marbleWasGrabbed)
            return "Drop marble in delivery zone";

        if (startTime >= 0)
            return "Pinch the marble\n(thumb + index finger)";

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
}
