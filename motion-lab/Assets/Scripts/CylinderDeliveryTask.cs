// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Task 2: Cylinder delivery task.
/// User must grab cylinder sideways (hand rotates), move it right, and drop it in delivery zone.
/// </summary>
public class CylinderDeliveryTask : ContinuousTask
{
    [Header("Task Objects")]
    public GameObject cylinderObject;
    public GameObject cylinderPrefab; // Prefab to spawn if cylinderObject is null
    public DeliveryZone deliveryZone;

    [Header("Spawn Settings (Normalized Grid Coordinates)")]
    [Tooltip("Normalized X position (-1 to 1) for cylinder spawn")]
    public float cylinderSpawnNormalizedX = -0.1f;

    [Tooltip("Normalized Y position (-1 to 1) for cylinder spawn (maps to Unity Z)")]
    public float cylinderSpawnNormalizedY = 0f;

    [Tooltip("Normalized X position (-1 to 1) for delivery zone")]
    public float deliveryZoneNormalizedX = 0.8f;

    [Tooltip("Normalized Y position (-1 to 1) for delivery zone (maps to Unity Z)")]
    public float deliveryZoneNormalizedY = 0f;

    [Header("Grab Requirements")]
    [Tooltip("Requires hand to be at ~90° supination to grab the cylinder")]
    public bool requireSupinationToGrab = true;

    [Tooltip("Target supination angle (degrees) to grab cylinder")]
    public float targetSupinationAngle = 90f;

    [Tooltip("Allowed deviation from target angle (degrees) - creates range of ±tolerance")]
    public float supinationTolerance = 5f;

    private Grabbable cylinderGrabbable;
    private Rigidbody cylinderRigidbody;
    private bool cylinderWasGrabbed = false;
    private bool cylinderWasDelivered = false;

    void Awake()
    {
        taskName = "Cylinder Delivery";
        taskType = ContinuousTaskType.CylinderDelivery;
    }

    void Start()
    {
        // Try to get delivery zone from ContinuousTaskManager if not assigned
        if (deliveryZone == null && ContinuousTaskManager.Instance != null)
        {
            deliveryZone = ContinuousTaskManager.Instance.deliveryZone;
            if (deliveryZone != null)
            {
                Debug.Log("[CylinderDeliveryTask] Got delivery zone from ContinuousTaskManager");
            }
        }
    }

    /// <summary>
    /// Get the actual spawn position for the cylinder (converts from normalized grid coordinates).
    /// </summary>
    private Vector3 GetCylinderSpawnPosition()
    {
        if (WorkspaceGrid.Instance != null)
        {
            return WorkspaceGrid.ToWorld(
                cylinderSpawnNormalizedX,
                cylinderSpawnNormalizedY,
                WorkspaceGrid.Instance.objectHeight
            );
        }
        // Fallback if no WorkspaceGrid instance
        return WorkspaceGrid.ToWorld(cylinderSpawnNormalizedX, cylinderSpawnNormalizedY, 0.5f);
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
    /// Prepare task: Setup cylinder and delivery zone, but keep them inactive (not grabbable).
    /// </summary>
    protected override void OnTaskPrepare()
    {
        // Reset state
        cylinderWasGrabbed = false;
        cylinderWasDelivered = false;

        // Get spawn positions (from grid or legacy)
        Vector3 spawnPos = GetCylinderSpawnPosition();
        Vector3 zonePos = GetDeliveryZonePosition();

        // Debug: Check if we have cylinder references
        if (cylinderObject == null && cylinderPrefab == null)
        {
            Debug.LogError(
                "[CylinderDeliveryTask] ERROR: Both cylinderObject and cylinderPrefab are null! Cannot spawn cylinder. Please assign either cylinderObject or cylinderPrefab in the inspector."
            );
            return;
        }

        // Spawn cylinder if needed
        if (cylinderObject == null && cylinderPrefab != null)
        {
            cylinderObject = Instantiate(cylinderPrefab, spawnPos, Quaternion.identity);
            cylinderObject.name = "Cylinder_" + System.DateTime.Now.Ticks;

            Debug.Log(
                $"[CylinderDeliveryTask] Spawned cylinder at {spawnPos} (normalized: {cylinderSpawnNormalizedX}, {cylinderSpawnNormalizedY})"
            );
        }

        // Setup cylinder (no rotation - hand will rotate to grab it sideways, visible but not grabbable during countdown)
        if (cylinderObject != null)
        {
            cylinderObject.transform.position = spawnPos;
            cylinderObject.transform.rotation = Quaternion.identity; // No rotation - hand rotates to grab sideways
            cylinderObject.SetActive(true); // Visible during countdown

            // Set to Default layer (NOT grabbable yet)
            int defaultLayer = 0; // Default layer
            cylinderObject.layer = defaultLayer;
            SetLayerRecursively(cylinderObject.transform, defaultLayer);

            cylinderRigidbody = cylinderObject.GetComponent<Rigidbody>();
            if (cylinderRigidbody == null)
            {
                cylinderRigidbody = cylinderObject.AddComponent<Rigidbody>();
                Debug.Log("[CylinderDeliveryTask] Added Rigidbody to cylinder");
            }

            cylinderGrabbable = cylinderObject.GetComponent<Grabbable>();
            if (cylinderGrabbable == null)
            {
                cylinderGrabbable = cylinderObject.AddComponent<Grabbable>();
                Debug.Log("[CylinderDeliveryTask] Added Grabbable to cylinder");
            }

            // Reset physics
            cylinderRigidbody.linearVelocity = Vector3.zero;
            cylinderRigidbody.angularVelocity = Vector3.zero;
            cylinderRigidbody.useGravity = true;
            cylinderRigidbody.isKinematic = false;

            Debug.Log(
                $"[CylinderDeliveryTask] Cylinder prepared at position {cylinderObject.transform.position} (visible but not grabbable during countdown)"
            );
        }
        else
        {
            Debug.LogError(
                "[CylinderDeliveryTask] ERROR: cylinderObject is still null after spawn attempt!"
            );
        }

        // Setup delivery zone (also keep inactive)
        if (deliveryZone == null)
        {
            Debug.LogError(
                "[CylinderDeliveryTask] ERROR: deliveryZone is null! Please assign deliveryZone in the inspector or ensure ContinuousTaskManager has a deliveryZone assigned."
            );
        }
        else
        {
            deliveryZone.transform.position = zonePos;
            deliveryZone.gameObject.SetActive(true); // Visible during countdown
            deliveryZone.ClearCount();
            Debug.Log(
                $"[CylinderDeliveryTask] Delivery zone prepared at {zonePos} (normalized: {deliveryZoneNormalizedX}, {deliveryZoneNormalizedY})"
            );
        }
    }

    /// <summary>
    /// Activate task: Make objects grabbable after countdown (they're already visible).
    /// </summary>
    protected override void OnTaskActivate()
    {
        // Make cylinder grabbable
        if (cylinderObject != null)
        {
            // Set layer to "Grabbable" (Layer 8) so HandGrabber can detect it
            int grabbableLayer = LayerMask.NameToLayer("Grabbable");
            if (grabbableLayer != -1)
            {
                cylinderObject.layer = grabbableLayer;
                // Also set layer for all children
                SetLayerRecursively(cylinderObject.transform, grabbableLayer);
            }
            else
            {
                Debug.LogWarning(
                    "[CylinderDeliveryTask] 'Grabbable' layer not found! Using Default layer. Make sure 'Grabbable' layer exists in Project Settings > Tags and Layers."
                );
            }

            Debug.Log("[CylinderDeliveryTask] Cylinder is now grabbable");
        }
    }

    /// <summary>
    /// Start timing: Called when task actually starts (after countdown).
    /// </summary>
    protected override void OnTaskStart()
    {
        Debug.Log("[CylinderDeliveryTask] Timing started - waiting for cylinder grab and delivery");
    }

    protected override void OnTaskReset()
    {
        base.OnTaskReset();
        cylinderWasGrabbed = false;
        cylinderWasDelivered = false;

        // Hide or destroy objects
        if (cylinderObject != null)
        {
            // If spawned from prefab, destroy it; otherwise just hide
            if (cylinderPrefab != null && cylinderObject.name.StartsWith("Cylinder_"))
            {
                Destroy(cylinderObject);
                cylinderObject = null;
            }
            else
            {
                cylinderObject.SetActive(false);
            }
        }
        if (deliveryZone != null)
            deliveryZone.gameObject.SetActive(false);
    }

    protected override void CheckTaskCompletion()
    {
        if (cylinderGrabbable == null || deliveryZone == null || cylinderRigidbody == null)
            return;

        // Check if cylinder was grabbed
        if (!cylinderWasGrabbed && cylinderGrabbable.IsHeld)
        {
            cylinderWasGrabbed = true;
            Debug.Log("[CylinderDeliveryTask] Cylinder grabbed");
        }

        // Check if cylinder was delivered (not held and in delivery zone)
        if (cylinderWasGrabbed && !cylinderWasDelivered)
        {
            // Cylinder must be released (not held) AND in delivery zone
            bool isReleased = !cylinderGrabbable.IsHeld;

            // Check if cylinder is in delivery zone using multiple methods for reliability
            Collider zoneCollider = deliveryZone.GetComponent<Collider>();
            bool isInZone = false;

            if (zoneCollider != null)
            {
                // Method 1: Check if cylinder center is within zone bounds
                Vector3 cylinderPos = cylinderRigidbody.worldCenterOfMass;
                Bounds zoneBounds = zoneCollider.bounds;
                isInZone = zoneBounds.Contains(cylinderPos);

                // Method 2: Also check cylinder transform position (more reliable for trigger colliders)
                if (!isInZone)
                {
                    Vector3 cylinderTransformPos = cylinderObject.transform.position;
                    isInZone = zoneBounds.Contains(cylinderTransformPos);
                }

                // Method 3: Check if any part of cylinder collider overlaps with zone
                if (!isInZone && cylinderObject != null)
                {
                    Collider cylinderCollider = cylinderObject.GetComponent<Collider>();
                    if (cylinderCollider != null)
                    {
                        isInZone = zoneBounds.Intersects(cylinderCollider.bounds);
                    }
                }
            }

            if (isReleased && isInZone)
            {
                cylinderWasDelivered = true;
                CompleteTask();
                Debug.Log("[CylinderDeliveryTask] Cylinder delivered! (released in delivery zone)");
            }
            else if (isReleased && !isInZone)
            {
                // Cylinder was released but not in zone - reset grab state so user can try again
                if (debugLogs)
                    Debug.Log(
                        $"[CylinderDeliveryTask] Cylinder released but not in delivery zone. Cylinder pos: {cylinderRigidbody.worldCenterOfMass}, Zone bounds: {zoneCollider.bounds}"
                    );
            }
        }
    }

    /// <summary>
    /// Get current task status for UI display
    /// </summary>
    public string GetStatusText()
    {
        if (isComplete)
            return "Complete!";

        if (cylinderWasDelivered)
            return "Delivered!";

        if (cylinderWasGrabbed && cylinderGrabbable != null && cylinderGrabbable.IsHeld)
            return "Move cylinder to delivery zone";

        if (cylinderWasGrabbed)
            return "Drop cylinder in delivery zone";

        if (startTime >= 0)
        {
            // Show supination info if required
            if (requireSupinationToGrab)
            {
                float currentSup = GetCurrentSupination();
                float minAngle = targetSupinationAngle - supinationTolerance;
                float maxAngle = targetSupinationAngle + supinationTolerance;

                if (currentSup >= minAngle && currentSup <= maxAngle)
                {
                    return "Grab the cylinder!";
                }
                else
                {
                    return $"Rotate hand to {targetSupinationAngle:F0}°\nCurrent: {currentSup:F0}°";
                }
            }
            else
            {
                return "Grab the cylinder";
            }
        }

        return "Get ready...";
    }


    float GetCurrentSupination()
    {
        if (
            ContinuousTaskManager.Instance == null
            || ContinuousTaskManager.Instance.handController == null
        )
            return 0f;

        HandController handController = ContinuousTaskManager.Instance.handController;
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

    [Header("Debug")]
    public bool debugLogs = false;

    void SetLayerRecursively(Transform obj, int layer)
    {
        obj.gameObject.layer = layer;
        foreach (Transform child in obj)
        {
            SetLayerRecursively(child, layer);
        }
    }
}
