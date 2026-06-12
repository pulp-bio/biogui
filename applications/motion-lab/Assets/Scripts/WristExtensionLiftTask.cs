// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;
using UnityEngine.Serialization;

/// <summary>
/// Functional task: approach an object, grab it from above, lift by wrist extension,
/// return the wrist to neutral, and place it back on the table.
/// </summary>
public class WristExtensionLiftTask : ContinuousTask
{
    [Header("Task Objects")]
    public GameObject liftObject;
    public GameObject liftObjectPrefab;

    [Header("Spawn Settings")]
    [Tooltip("Normalized X position (-1 to 1) for object spawn")]
    public float objectSpawnNormalizedX = 0f;

    [FormerlySerializedAs("objectSpawnNormalizedY")]
    [Tooltip("Normalized Z position (-1 to 1) for object spawn")]
    public float objectSpawnNormalizedZ = 0f;

    [Tooltip("If enabled, use WorkspaceGrid objectHeight for object spawn Y")]
    public bool useWorkspaceGridObjectHeight = true;

    [Tooltip("Unity Y position for object spawn")]
    public float objectSpawnY = 0.5f;

    [Tooltip("Optional upward offset for the object spawn if it intersects the table")]
    public float objectSpawnLift = 0.0f;

    [Header("Task Logic")]
    [Tooltip("Radius around the spawn point treated as the valid table release zone")]
    public float releaseZoneRadius = 0.45f;

    [Tooltip("Required wrist extension angle in degrees while holding the object")]
    public float requiredExtensionAngle = 30f;

    [Tooltip("Tolerance for a flat hand when grabbing from above")]
    public float flatHandTolerance = 8f;

    [Tooltip("Tolerance in degrees for returning the wrist to neutral before release")]
    public float neutralTolerance = 10f;

    [Tooltip("Required hand position state before grabbing the object")]
    public string requiredGrabPositionState = "forward";

    [Header("Hand Lift Settings")]
    [Tooltip("How much to lift the hand (Unity Y) while the dumbbell is held")]
    public float handLiftOnGrab = 0.08f;

    [Tooltip("How fast to lift/lower the hand (units per second)")]
    public float handLiftSpeed = 2.0f;

    [Header("References")]
    public HandController handController;

    [Header("Debug")]
    public bool debugLogs = false;

    private Grabbable liftGrabbable;
    private Rigidbody liftRigidbody;
    private bool objectWasGrabbed = false;
    private bool extensionReached = false;
    private bool returnedToNeutralAfterExtension = false;
    private bool isHandLifted = false;
    private Vector3 handTargetOffset = Vector3.zero;

    void Awake()
    {
        taskName = "Wrist Extension Lift";
        taskType = ContinuousTaskType.WristExtensionLift;
    }

    void Start()
    {
        if (handController == null)
            handController = FindFirstObjectByType<HandController>();
    }

    private float ResolveObjectSpawnY()
    {
        float baseY;
        if (useWorkspaceGridObjectHeight && WorkspaceGrid.Instance != null)
            baseY = WorkspaceGrid.Instance.objectHeight;
        else
            baseY = objectSpawnY;

        return baseY + objectSpawnLift;
    }

    private Vector3 GetObjectSpawnPosition()
    {
        return WorkspaceGrid.ToWorld(
            objectSpawnNormalizedX,
            objectSpawnNormalizedZ,
            ResolveObjectSpawnY()
        );
    }

    private Quaternion GetObjectSpawnRotation()
    {
        if (liftObject != null)
            return liftObject.transform.rotation;

        if (liftObjectPrefab != null)
            return liftObjectPrefab.transform.rotation;

        return Quaternion.identity;
    }

    protected override void OnTaskPrepare()
    {
        objectWasGrabbed = false;
        extensionReached = false;
        returnedToNeutralAfterExtension = false;

        Vector3 spawnPos = GetObjectSpawnPosition();

        if (liftObject == null && liftObjectPrefab == null)
        {
            Debug.LogError(
                "[WristExtensionLiftTask] ERROR: Both liftObject and liftObjectPrefab are null! Please assign either a scene object or prefab."
            );
            return;
        }

        if (liftObject == null && liftObjectPrefab != null)
        {
            liftObject = Instantiate(liftObjectPrefab, spawnPos, GetObjectSpawnRotation());
            liftObject.name = "WristLiftObject_" + System.DateTime.Now.Ticks;
            Debug.Log(
                $"[WristExtensionLiftTask] Spawned object at {spawnPos} (normalized X/Z: {objectSpawnNormalizedX}, {objectSpawnNormalizedZ}; Y: {objectSpawnY})"
            );
        }

        if (liftObject == null)
        {
            Debug.LogError("[WristExtensionLiftTask] ERROR: liftObject is null after spawn attempt!");
            return;
        }

        liftObject.transform.SetPositionAndRotation(spawnPos, GetObjectSpawnRotation());
        liftObject.SetActive(true);

        int defaultLayer = 0;
        liftObject.layer = defaultLayer;
        SetLayerRecursively(liftObject.transform, defaultLayer);

        liftRigidbody = liftObject.GetComponent<Rigidbody>();
        if (liftRigidbody == null)
        {
            liftRigidbody = liftObject.AddComponent<Rigidbody>();
            Debug.Log("[WristExtensionLiftTask] Added Rigidbody to lift object");
        }

        Collider objectCollider = liftObject.GetComponent<Collider>();
        if (objectCollider == null)
        {
            liftObject.AddComponent<BoxCollider>();
            Debug.Log("[WristExtensionLiftTask] Added BoxCollider to lift object");
        }

        liftGrabbable = liftObject.GetComponent<Grabbable>();
        if (liftGrabbable == null)
        {
            liftGrabbable = liftObject.AddComponent<Grabbable>();
            Debug.Log("[WristExtensionLiftTask] Added Grabbable to lift object");
        }

        liftRigidbody.linearVelocity = Vector3.zero;
        liftRigidbody.angularVelocity = Vector3.zero;
        liftRigidbody.useGravity = true;
        liftRigidbody.isKinematic = false;
    }

    protected override void OnTaskActivate()
    {
        if (liftObject != null)
            GrabbableLayerHelper.ApplyToObject(liftObject);
    }

    protected override void OnTaskStart()
    {
        Debug.Log("[WristExtensionLiftTask] Timing started - approach, grab, extend wrist, release, return");
    }

    protected override void OnTaskReset()
    {
        base.OnTaskReset();
        objectWasGrabbed = false;
        extensionReached = false;
        returnedToNeutralAfterExtension = false;
        isHandLifted = false;
        handTargetOffset = Vector3.zero;

        if (handController != null)
            handController.SetPositionOffset(Vector3.zero);

        if (liftObject != null)
        {
            if (liftObjectPrefab != null && liftObject.name.StartsWith("WristLiftObject_"))
            {
                Destroy(liftObject);
                liftObject = null;
            }
            else
            {
                liftObject.SetActive(false);
            }
        }
    }

    protected override void CheckTaskCompletion()
    {
        if (liftGrabbable == null || liftRigidbody == null || liftObject == null)
            return;

        bool shouldLift = liftGrabbable.IsHeld;
        if (shouldLift && !isHandLifted)
            isHandLifted = true;
        else if (!shouldLift && isHandLifted)
            isHandLifted = false;

        Vector3 targetOffset = isHandLifted ? new Vector3(0f, handLiftOnGrab, 0f) : Vector3.zero;
        handTargetOffset = Vector3.MoveTowards(
            handTargetOffset,
            targetOffset,
            handLiftSpeed * Time.deltaTime
        );

        if (handController != null)
            handController.SetPositionOffset(handTargetOffset);

        bool isHeld = liftGrabbable.IsHeld;
        bool isReleased = TaskZoneChecker.IsReleased(liftGrabbable, liftRigidbody);

        if (!objectWasGrabbed && isHeld)
        {
            if (IsHandAtRequiredGrabPosition() && IsHandFlatForGrab())
            {
                objectWasGrabbed = true;
                if (debugLogs)
                    Debug.Log("[WristExtensionLiftTask] Object grabbed in valid start posture");
            }
            else if (debugLogs)
            {
                Debug.Log("[WristExtensionLiftTask] Grab detected before reaching valid approach posture");
            }
        }

        if (objectWasGrabbed && isHeld && !extensionReached)
        {
            if (IsAtRequiredExtension())
            {
                extensionReached = true;
                if (debugLogs)
                    Debug.Log("[WristExtensionLiftTask] Required wrist extension reached");
            }
        }

        if (objectWasGrabbed && extensionReached && isHeld && !returnedToNeutralAfterExtension)
        {
            if (IsBackAtNeutral())
            {
                returnedToNeutralAfterExtension = true;
                if (debugLogs)
                    Debug.Log("[WristExtensionLiftTask] Wrist returned to neutral after extension");
            }
        }

        if (objectWasGrabbed && isReleased)
        {
            isHandLifted = false;
            handTargetOffset = Vector3.zero;
            if (handController != null)
                handController.SetPositionOffset(Vector3.zero);

            bool inReleaseZone = TaskZoneChecker.IsInPickupZone(
                GetObjectSpawnPosition(),
                releaseZoneRadius,
                liftRigidbody,
                liftObject
            );

            if (!extensionReached || !returnedToNeutralAfterExtension)
            {
                if (inReleaseZone)
                {
                    objectWasGrabbed = false;
                    extensionReached = false;
                    returnedToNeutralAfterExtension = false;
                    if (debugLogs)
                        Debug.Log("[WristExtensionLiftTask] Released before completing the motion - retry allowed");
                }
                else
                {
                    FailTask("Object dropped");
                }
                return;
            }

            if (!inReleaseZone)
            {
                FailTask("Object dropped");
                return;
            }

            CompleteTask();
            if (debugLogs)
                Debug.Log("[WristExtensionLiftTask] Object released on table after extension-neutral sequence");
            return;
        }
    }

    protected override void OnTaskComplete()
    {
        base.OnTaskComplete();
        isHandLifted = false;
        handTargetOffset = Vector3.zero;
        if (handController != null)
            handController.SetPositionOffset(Vector3.zero);
    }

    public string GetStatusText()
    {
        if (isFailed)
            return failureMessage;

        if (isComplete)
            return "Complete!";

        if (objectWasGrabbed && liftGrabbable != null && liftGrabbable.IsHeld)
        {
            if (!extensionReached)
                return $"Extend wrist to {requiredExtensionAngle:F0}°";
            if (!returnedToNeutralAfterExtension)
                return "Return wrist to neutral";
            return "Release object on table";
        }

        if (objectWasGrabbed)
            return "Release object on table";

        if (startTime >= 0)
        {
            if (!IsHandAtRequiredGrabPosition())
                return $"Move hand to {requiredGrabPositionState}";

            if (!IsHandFlatForGrab())
                return $"Flatten hand! ({GetCurrentSupination():F0}° → 0°)";

            return "Grab the object";
        }

        return "Get ready...";
    }

    private bool IsHandAtRequiredGrabPosition()
    {
        if (handController == null)
            return true;
        return handController.CurrentPositionState == requiredGrabPositionState.ToLowerInvariant();
    }

    private bool IsBackAtNeutral()
    {
        if (handController == null)
            return true;
        if (handController.currentRotationMode == RotationMode.State)
            return handController.CurrentRotationState == "neutral";
        return GetCurrentExtensionAngle() <= neutralTolerance;
    }

    private bool IsAtRequiredExtension()
    {
        if (handController == null)
            return true;
        if (handController.currentRotationMode == RotationMode.State)
            return handController.CurrentRotationState == "extended";
        return GetCurrentExtensionAngle() >= requiredExtensionAngle;
    }

    private bool IsHandFlatForGrab()
    {
        return Mathf.Abs(GetCurrentSupination()) <= flatHandTolerance;
    }

    private float GetCurrentSupination()
    {
        if (handController == null)
            return 0f;
        return HandSupination.GetDegrees(handController);
    }

    private float GetCurrentExtensionAngle()
    {
        if (handController == null)
            return 0f;

        float x = NormalizeAngle(handController.CurrentRotationEuler.x);
        // In the current hand mapping, wrist extension corresponds to negative X angles.
        return Mathf.Max(0f, -x);
    }

    private float NormalizeAngle(float angle)
    {
        while (angle > 180f)
            angle -= 360f;
        while (angle < -180f)
            angle += 360f;
        return angle;
    }

    private void SetLayerRecursively(Transform root, int layer)
    {
        if (root == null)
            return;

        root.gameObject.layer = layer;
        foreach (Transform child in root)
            SetLayerRecursively(child, layer);
    }

    void OnValidate()
    {
        releaseZoneRadius = Mathf.Max(0.1f, releaseZoneRadius);
        requiredExtensionAngle = Mathf.Clamp(requiredExtensionAngle, 5f, HandRotationLimits.EXTENSION_MAX);
        flatHandTolerance = Mathf.Clamp(flatHandTolerance, 0f, 20f);
        neutralTolerance = Mathf.Clamp(neutralTolerance, 0f, 20f);
        requiredGrabPositionState = string.IsNullOrWhiteSpace(requiredGrabPositionState)
            ? "forward"
            : requiredGrabPositionState.ToLowerInvariant();
    }
}
