using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(SphereCollider))]
public class HandGrabber : MonoBehaviour
{
    [Header("References")]
    public HandController hand;
    public Transform holdPoint;
    public Rigidbody holdPointRb;

    [Header("Settings")]
    public LayerMask grabbableLayers = ~0;
    public float breakForce = Mathf.Infinity;
    public float breakTorque = Mathf.Infinity;
    public bool requireEdgeToGrab = true;
    public bool debugLogs = true;

    [Header("Rotation Requirements (Optional)")]
    [Tooltip(
        "If enabled, requires minimum supination angle to grab cylinder. Disable to allow grabbing without rotation."
    )]
    public bool requireSupinationForCylinder = true;

    [Tooltip("Minimum supination angle (degrees) required to grab cylinder")]
    public float minSupinationAngle = 70f;

    [Tooltip("Tolerance for supination check (degrees) - allows grabbing if within this range")]
    public float supinationTolerance = 30f;

    [Header("Pinch Settings")]
    [Tooltip("Transform for pinch hold point (between thumb and index finger tips)")]
    public Transform pinchHoldPoint;

    [Tooltip("Rigidbody for pinch hold point")]
    public Rigidbody pinchHoldPointRb;

    private HashSet<Rigidbody> objectsInRange = new HashSet<Rigidbody>();
    private Rigidbody heldObject;
    private FixedJoint joint;
    private bool isPinchHeld = false; // Track if current held object was grabbed via pinch

    void Awake()
    {
        if (!holdPointRb && holdPoint)
            holdPointRb = holdPoint.GetComponent<Rigidbody>();

        // Setup pinch hold point (fallback to regular hold point if not set)
        if (!pinchHoldPoint)
            pinchHoldPoint = holdPoint;
        if (!pinchHoldPointRb && pinchHoldPoint)
            pinchHoldPointRb = pinchHoldPoint.GetComponent<Rigidbody>();
        if (!pinchHoldPointRb)
            pinchHoldPointRb = holdPointRb;
    }

    void Update()
    {
        if (!hand)
            return;

        // Check for pinch first (for marbles and small objects)
        bool shouldPinch =
            (requireEdgeToGrab && hand.PinchJustBecameTrue)
            || (!requireEdgeToGrab && hand.IsPinching);

        if (shouldPinch && heldObject == null)
        {
            if (debugLogs)
                Debug.Log(
                    $"[HandGrabber] Pinch triggered! PinchJustBecameTrue: {hand.PinchJustBecameTrue}, IsPinching: {hand.IsPinching}"
                );
            TryPinch();
        }

        // Check for regular grab (for boxes, cylinders, bottles)
        bool shouldGrab =
            (requireEdgeToGrab && hand.GripJustBecameTrue)
            || (!requireEdgeToGrab && hand.IsGripping);

        if (shouldGrab && heldObject == null)
        {
            if (debugLogs)
                Debug.Log(
                    $"[HandGrabber] Grab triggered! GripJustBecameTrue: {hand.GripJustBecameTrue}, IsGripping: {hand.IsGripping}, requireEdgeToGrab: {requireEdgeToGrab}"
                );
            TryGrab();
        }

        // Release based on how object was grabbed
        if (isPinchHeld && !hand.IsPinching && heldObject != null)
        {
            Release();
        }
        else if (!isPinchHeld && !hand.IsGripping && heldObject != null)
        {
            Release();
        }
    }

    void OnTriggerEnter(Collider col)
    {
        Rigidbody rb = GetGrabbable(col);
        if (rb != null)
        {
            objectsInRange.Add(rb);
            bool isCyl = IsCylinder(rb);
            Debug.Log(
                $"[HandGrabber] Object entered range: {rb.name} (IsCylinder: {isCyl}, Layer: {col.gameObject.layer})"
            );

            if (isCyl)
            {
                CylinderDeliveryTask task = GetCylinderDeliveryTask(rb);
                Debug.Log(
                    $"[HandGrabber] Cylinder detected! Task found: {task != null}, requireSupination: {(task != null ? task.requireSupinationToGrab.ToString() : "N/A")}"
                );
            }
        }
        else
        {
            // Log why object was rejected
            if (col.attachedRigidbody != null)
            {
                bool layerOk = ((1 << col.gameObject.layer) & grabbableLayers) != 0;
                bool isTrigger = col.isTrigger;
                Debug.Log(
                    $"[HandGrabber] Object rejected: {col.name} (Layer OK: {layerOk}, IsTrigger: {isTrigger}, HasRigidbody: {col.attachedRigidbody != null})"
                );
            }
        }
    }

    void OnTriggerExit(Collider col)
    {
        Rigidbody rb = col.attachedRigidbody;
        if (rb != null)
            objectsInRange.Remove(rb);
    }

    Rigidbody GetGrabbable(Collider col)
    {
        if (((1 << col.gameObject.layer) & grabbableLayers) == 0)
            return null;

        Rigidbody rb = col.attachedRigidbody;
        if (!rb || col.isTrigger)
            return null;
        if (holdPointRb && rb == holdPointRb)
            return null;

        return rb;
    }

    void TryGrab()
    {
        if (!holdPointRb)
        {
            Debug.LogError("HandGrabber: holdPointRb not set!");
            return;
        }

        if (objectsInRange.Count == 0)
        {
            Debug.Log("[HandGrabber] No objects in range to grab");
            return;
        }

        Debug.Log($"[HandGrabber] Trying to grab from {objectsInRange.Count} objects in range");

        Rigidbody closest = null;
        float closestDist = float.MaxValue;

        foreach (var rb in objectsInRange)
        {
            if (!rb)
                continue;

            // Skip marbles - they require pinch grip, not regular grab
            if (IsMarble(rb))
            {
                if (debugLogs)
                    Debug.Log($"[HandGrabber] Skipping marble {rb.name} - requires pinch grip");
                continue;
            }

            // Check if this is a box and if flat hand is required
            if (IsBox(rb))
            {
                Debug.Log($"[HandGrabber] Found box: {rb.name}");

                BoxDeliveryTask boxTask = GetBoxDeliveryTask(rb);
                if (boxTask != null && boxTask.requireFlatHandToGrab)
                {
                    float currentSup = GetCurrentSupination();
                    float tolerance = boxTask.flatHandTolerance;
                    if (Mathf.Abs(currentSup) > tolerance)
                    {
                        Debug.Log(
                            $"[HandGrabber] ❌ Cannot grab box - need flat hand (0°±{tolerance}°), current: {currentSup:F1}°"
                        );
                        continue; // Skip this object if flat hand requirement not met
                    }
                    else
                    {
                        Debug.Log($"[HandGrabber] ✅ Hand is flat enough for box: {currentSup:F1}°");
                    }
                }
            }

            // Check if this is a cylinder and if supination is required
            if (IsCylinder(rb))
            {
                Debug.Log($"[HandGrabber] Found cylinder: {rb.name}");

                // First check if this cylinder belongs to a CylinderDeliveryTask (has specific requirements)
                CylinderDeliveryTask cylinderTask = GetCylinderDeliveryTask(rb);
                if (cylinderTask != null)
                {
                    Debug.Log(
                        $"[HandGrabber] Cylinder belongs to CylinderDeliveryTask, requireSupinationToGrab: {cylinderTask.requireSupinationToGrab}"
                    );

                    if (cylinderTask.requireSupinationToGrab)
                    {
                        float currentSup = GetCurrentSupination();
                        float minAngle = cylinderTask.targetSupinationAngle - cylinderTask.supinationTolerance;
                        float maxAngle = cylinderTask.targetSupinationAngle + cylinderTask.supinationTolerance;
                        if (currentSup < minAngle || currentSup > maxAngle)
                        {
                            Debug.Log(
                                $"[HandGrabber] ❌ Cannot grab cylinder - need {cylinderTask.targetSupinationAngle}°±{cylinderTask.supinationTolerance}° supination, current: {currentSup:F1}°"
                            );
                            continue; // Skip this object if supination requirement not met
                        }
                        else
                        {
                            Debug.Log(
                                $"[HandGrabber] ✅ Supination OK for cylinder: {currentSup:F1}°"
                            );
                        }
                    }
                    else
                    {
                        Debug.Log($"[HandGrabber] ✅ Supination not required for this cylinder");
                    }
                }
                // Fallback to global setting for other cylinders
                else if (requireSupinationForCylinder)
                {
                    Debug.Log($"[HandGrabber] Using global supination requirement");
                    if (!IsSupinatedEnough())
                    {
                        float currentSup = GetCurrentSupination();
                        Debug.Log(
                            $"[HandGrabber] ❌ Cannot grab cylinder - need {minSupinationAngle}° supination, current: {currentSup:F1}°"
                        );
                        continue; // Skip this object if supination requirement not met
                    }
                }
                else
                {
                    Debug.Log($"[HandGrabber] ✅ No supination requirement for cylinder");
                }
            }
            // Check if this is a bottle and if supination is required
            else if (IsBottle(rb))
            {
                Debug.Log($"[HandGrabber] Found bottle: {rb.name}");

                // Check if this bottle belongs to a BottlePouringTask (has specific requirements)
                BottlePouringTask bottleTask = GetBottlePouringTask(rb);
                if (bottleTask != null)
                {
                    Debug.Log(
                        $"[HandGrabber] Bottle belongs to BottlePouringTask, requireSupinationToGrab: {bottleTask.requireSupinationToGrab}"
                    );

                    if (bottleTask.requireSupinationToGrab)
                    {
                        float currentSup = GetCurrentSupination();
                        float minAngle = bottleTask.targetSupinationAngle - bottleTask.supinationTolerance;
                        float maxAngle = bottleTask.targetSupinationAngle + bottleTask.supinationTolerance;
                        if (currentSup < minAngle || currentSup > maxAngle)
                        {
                            Debug.Log(
                                $"[HandGrabber] ❌ Cannot grab bottle - need {bottleTask.targetSupinationAngle}°±{bottleTask.supinationTolerance}° supination, current: {currentSup:F1}°"
                            );
                            continue; // Skip this object if supination requirement not met
                        }
                        else
                        {
                            Debug.Log(
                                $"[HandGrabber] ✅ Supination OK for bottle: {currentSup:F1}°"
                            );
                        }
                    }
                    else
                    {
                        Debug.Log($"[HandGrabber] ✅ Supination not required for this bottle");
                    }
                }
            }

            float dist = Vector3.Distance(rb.worldCenterOfMass, holdPoint.position);
            if (dist < closestDist)
            {
                closestDist = dist;
                closest = rb;
            }
        }

        if (closest != null)
            Grab(closest);
    }

    void TryPinch()
    {
        if (!pinchHoldPointRb)
        {
            Debug.LogError("HandGrabber: pinchHoldPointRb not set!");
            return;
        }

        if (objectsInRange.Count == 0)
        {
            if (debugLogs)
                Debug.Log("[HandGrabber] No objects in range to pinch");
            return;
        }

        if (debugLogs)
            Debug.Log(
                $"[HandGrabber] Trying to pinch from {objectsInRange.Count} objects in range"
            );

        Rigidbody closest = null;
        float closestDist = float.MaxValue;

        foreach (var rb in objectsInRange)
        {
            if (!rb)
                continue;

            // Only pinch marbles (small spherical objects)
            if (!IsMarble(rb))
            {
                if (debugLogs)
                    Debug.Log(
                        $"[HandGrabber] Object {rb.name} is not a marble, skipping for pinch"
                    );
                continue;
            }

            if (debugLogs)
                Debug.Log($"[HandGrabber] Found marble for pinch: {rb.name}");

            float dist = Vector3.Distance(rb.worldCenterOfMass, pinchHoldPoint.position);
            if (dist < closestDist)
            {
                closestDist = dist;
                closest = rb;
            }
        }

        if (closest != null)
        {
            PinchGrab(closest);
        }
    }

    void PinchGrab(Rigidbody rb)
    {
        heldObject = rb;
        isPinchHeld = true;

        // Set grabbable state
        Grabbable g = heldObject.GetComponent<Grabbable>();
        if (!g)
            g = heldObject.gameObject.AddComponent<Grabbable>();
        g.SetHeld(true);

        // Physics setup for small object
        heldObject.useGravity = false;
        heldObject.isKinematic = false;
        heldObject.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        heldObject.interpolation = RigidbodyInterpolation.Interpolate;

        // Create joint attached to pinch hold point
        FixedJoint oldJoint = heldObject.GetComponent<FixedJoint>();
        if (oldJoint)
            Destroy(oldJoint);

        joint = heldObject.gameObject.AddComponent<FixedJoint>();
        joint.connectedBody = pinchHoldPointRb;
        joint.breakForce = breakForce;
        joint.breakTorque = breakTorque;

        heldObject.MovePosition(pinchHoldPoint.position);
        heldObject.MoveRotation(pinchHoldPoint.rotation);

        if (debugLogs)
            Debug.Log($"[HandGrabber] Pinch-grabbed: {heldObject.name}");
    }

    bool IsMarble(Rigidbody rb)
    {
        if (rb == null)
            return false;

        // Check if object name contains "marble" or "Marble"
        string objName = rb.name.ToLower();
        if (objName.Contains("marble"))
            return true;

        // Check if spawned by MarbleDeliveryTask (name pattern: "Marble_...")
        if (objName.StartsWith("marble_"))
            return true;

        // Check if it's part of a MarbleDeliveryTask
        if (GetMarbleDeliveryTask(rb) != null)
            return true;

        return false;
    }

    MarbleDeliveryTask GetMarbleDeliveryTask(Rigidbody rb)
    {
        if (rb == null)
            return null;

        // Check if it's part of a MarbleDeliveryTask
        MarbleDeliveryTask task = rb.GetComponent<MarbleDeliveryTask>();
        if (task != null)
            return task;

        // Check parent for MarbleDeliveryTask
        if (rb.transform.parent != null)
        {
            task = rb.transform.parent.GetComponent<MarbleDeliveryTask>();
            if (task != null)
                return task;
        }

        // Check if any parent has MarbleDeliveryTask
        Transform current = rb.transform.parent;
        while (current != null)
        {
            task = current.GetComponent<MarbleDeliveryTask>();
            if (task != null)
                return task;
            current = current.parent;
        }

        // Check if this marble object belongs to a MarbleDeliveryTask by checking ContinuousTaskManager
        if (ContinuousTaskManager.Instance != null)
        {
            MarbleDeliveryTask managerTask = ContinuousTaskManager.Instance.marbleDeliveryTask;
            if (managerTask != null)
            {
                // Check if this is the marble object from the task
                if (managerTask.marbleObject == rb.gameObject)
                {
                    return managerTask;
                }

                // Also check if the name matches the pattern used when spawning from prefab
                if (rb.name.StartsWith("Marble_"))
                {
                    return managerTask;
                }
            }
        }

        return null;
    }

    bool IsBox(Rigidbody rb)
    {
        if (rb == null)
            return false;

        // Check if object name contains "box" or "Box"
        string objName = rb.name.ToLower();
        if (objName.Contains("box"))
            return true;

        // Check if spawned by BoxDeliveryTask (name pattern: "Box_...")
        if (objName.StartsWith("box_"))
            return true;

        // Check if it's part of a BoxDeliveryTask
        if (GetBoxDeliveryTask(rb) != null)
            return true;

        return false;
    }

    BoxDeliveryTask GetBoxDeliveryTask(Rigidbody rb)
    {
        if (rb == null)
            return null;

        // Check if it's part of a BoxDeliveryTask
        BoxDeliveryTask task = rb.GetComponent<BoxDeliveryTask>();
        if (task != null)
            return task;

        // Check parent for BoxDeliveryTask
        if (rb.transform.parent != null)
        {
            task = rb.transform.parent.GetComponent<BoxDeliveryTask>();
            if (task != null)
                return task;
        }

        // Check if any parent has BoxDeliveryTask
        Transform current = rb.transform.parent;
        while (current != null)
        {
            task = current.GetComponent<BoxDeliveryTask>();
            if (task != null)
                return task;
            current = current.parent;
        }

        // Check if this box object belongs to a BoxDeliveryTask by checking ContinuousTaskManager
        if (ContinuousTaskManager.Instance != null)
        {
            BoxDeliveryTask managerTask = ContinuousTaskManager.Instance.boxDeliveryTask;
            if (managerTask != null)
            {
                // Check if this is the box object from the task
                if (managerTask.boxObject == rb.gameObject)
                {
                    return managerTask;
                }

                // Also check if the name matches the pattern used when spawning from prefab
                if (rb.name.StartsWith("Box_"))
                {
                    return managerTask;
                }
            }
        }

        return null;
    }

    bool IsCylinder(Rigidbody rb)
    {
        if (rb == null)
            return false;

        // Check if object name contains "cylinder" or "Cylinder"
        string objName = rb.name.ToLower();
        if (objName.Contains("cylinder"))
            return true;

        // Check if spawned by CylinderDeliveryTask (name pattern: "Cylinder_...")
        if (objName.StartsWith("cylinder_"))
            return true;

        // Check if it's part of a CylinderDeliveryTask
        if (GetCylinderDeliveryTask(rb) != null)
            return true;

        return false;
    }

    bool IsBottle(Rigidbody rb)
    {
        if (rb == null)
            return false;

        // Check if object name contains "bottle" or "Bottle"
        string objName = rb.name.ToLower();
        if (objName.Contains("bottle"))
            return true;

        // Check if spawned by BottlePouringTask (name pattern: "Bottle_...")
        if (objName.StartsWith("bottle_"))
            return true;

        // Check if it's part of a BottlePouringTask
        if (GetBottlePouringTask(rb) != null)
            return true;

        return false;
    }

    CylinderDeliveryTask GetCylinderDeliveryTask(Rigidbody rb)
    {
        if (rb == null)
            return null;

        // Check if it's part of a CylinderDeliveryTask (check on GameObject, not Rigidbody)
        CylinderDeliveryTask task = rb.GetComponent<CylinderDeliveryTask>();
        if (task != null)
            return task;

        // Check parent for CylinderDeliveryTask
        if (rb.transform.parent != null)
        {
            task = rb.transform.parent.GetComponent<CylinderDeliveryTask>();
            if (task != null)
                return task;
        }

        // Check if any parent has CylinderDeliveryTask
        Transform current = rb.transform.parent;
        while (current != null)
        {
            task = current.GetComponent<CylinderDeliveryTask>();
            if (task != null)
                return task;
            current = current.parent;
        }

        // Check if this cylinder object belongs to a CylinderDeliveryTask by checking ContinuousTaskManager
        if (ContinuousTaskManager.Instance != null)
        {
            CylinderDeliveryTask managerTask = ContinuousTaskManager.Instance.cylinderDeliveryTask;
            if (managerTask != null)
            {
                // Check if this is the cylinder object from the task
                if (managerTask.cylinderObject == rb.gameObject)
                {
                    return managerTask;
                }

                // Also check if the name matches the pattern used when spawning from prefab
                if (rb.name.StartsWith("Cylinder_"))
                {
                    return managerTask;
                }
            }
        }

        return null;
    }

    BottlePouringTask GetBottlePouringTask(Rigidbody rb)
    {
        if (rb == null)
            return null;

        // Check if it's part of a BottlePouringTask (check on GameObject, not Rigidbody)
        BottlePouringTask task = rb.GetComponent<BottlePouringTask>();
        if (task != null)
            return task;

        // Check parent for BottlePouringTask
        if (rb.transform.parent != null)
        {
            task = rb.transform.parent.GetComponent<BottlePouringTask>();
            if (task != null)
                return task;
        }

        // Check if any parent has BottlePouringTask
        Transform current = rb.transform.parent;
        while (current != null)
        {
            task = current.GetComponent<BottlePouringTask>();
            if (task != null)
                return task;
            current = current.parent;
        }

        // Check if this bottle object belongs to a BottlePouringTask by checking ContinuousTaskManager
        if (ContinuousTaskManager.Instance != null)
        {
            BottlePouringTask managerTask = ContinuousTaskManager.Instance.bottlePouringTask;
            if (managerTask != null)
            {
                // Check if this is the bottle object from the task
                if (managerTask.bottleObject == rb.gameObject)
                {
                    return managerTask;
                }

                // Also check if the name matches the pattern used when spawning from prefab
                if (rb.name.StartsWith("Bottle_"))
                {
                    return managerTask;
                }
            }
        }

        return null;
    }

    bool IsSupinatedEnough()
    {
        if (!hand)
            return true; // If no hand controller, allow grab

        Vector3 handRotation = hand.CurrentRotationEuler;
        float currentSupinationZ = NormalizeAngle(handRotation.z);

        // Calculate relative supination
        // HandController uses: z = -HandednessMultiplier * clampedRotation[2]
        // So for left hand (multiplier = +1): negative z = supination
        // For right hand (multiplier = -1): positive z = supination
        // We need to reverse this to get the actual supination angle
        float relativeSupination = -hand.HandednessMultiplier * currentSupinationZ;

        // Check if supination is within tolerance
        float minRequired = minSupinationAngle - supinationTolerance;
        bool isEnough = relativeSupination >= minRequired;

        if (debugLogs && !isEnough)
        {
            Debug.Log(
                $"[HandGrabber] Supination check: current={relativeSupination:F1}°, required={minRequired:F1}° (min={minSupinationAngle}°, tolerance={supinationTolerance}°)"
            );
        }

        return isEnough;
    }

    float GetCurrentSupination()
    {
        if (!hand)
            return 0f;

        Vector3 handRotation = hand.CurrentRotationEuler;
        float currentSupinationZ = NormalizeAngle(handRotation.z);
        return -hand.HandednessMultiplier * currentSupinationZ;
    }

    float NormalizeAngle(float angle)
    {
        while (angle > 180f)
            angle -= 360f;
        while (angle < -180f)
            angle += 360f;
        return angle;
    }

    void Grab(Rigidbody rb)
    {
        heldObject = rb;
        isPinchHeld = false; // Regular grab, not pinch

        // Handle BoxTask
        BoxTask boxTask = heldObject.GetComponent<BoxTask>();
        if (boxTask)
        {
            if (BoxTaskManager.Instance == null || BoxTaskManager.Instance.AllowStart(boxTask))
                boxTask.StartTask();
            else
                BoxTaskManager.Instance.ShowWrongBoxHint();
        }

        // Handle RotationTracker (for BoxTask rotation tasks)
        RotationTracker rotTracker = heldObject.GetComponent<RotationTracker>();
        if (rotTracker)
            rotTracker.OnGrabbed(holdPoint);

        // Set grabbable state
        Grabbable g = heldObject.GetComponent<Grabbable>();
        if (!g)
            g = heldObject.gameObject.AddComponent<Grabbable>();
        g.SetHeld(true);

        // Check if this is a cylinder - cylinders should keep their rotation
        bool isCyl = IsCylinder(heldObject);

        // Physics setup
        heldObject.useGravity = false;
        heldObject.isKinematic = false;
        heldObject.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        heldObject.interpolation = RigidbodyInterpolation.Interpolate;

        // For cylinders, freeze rotation to keep sideways orientation
        if (isCyl)
        {
            heldObject.freezeRotation = true;
            if (debugLogs)
                Debug.Log(
                    $"[HandGrabber] Cylinder grabbed - rotation frozen to keep sideways orientation"
                );
        }

        // Create joint
        FixedJoint oldJoint = heldObject.GetComponent<FixedJoint>();
        if (oldJoint)
            Destroy(oldJoint);

        joint = heldObject.gameObject.AddComponent<FixedJoint>();
        joint.connectedBody = holdPointRb;
        joint.breakForce = breakForce;
        joint.breakTorque = breakTorque;

        heldObject.MovePosition(holdPoint.position);

        // For non-cylinders, rotate to match hand rotation
        // For cylinders, keep original rotation (already frozen above)
        if (!isCyl)
        {
            heldObject.MoveRotation(holdPoint.rotation);
        }

        if (debugLogs)
            Debug.Log($"Grabbed: {heldObject.name}");
    }

    public void Release()
    {
        if (heldObject == null)
            return;

        // Notify RotationTracker (for BoxTask)
        RotationTracker rotTracker = heldObject.GetComponent<RotationTracker>();
        if (rotTracker)
        {
            rotTracker.OnReleased();
        }

        // Check if this was a cylinder - unfreeze rotation when released
        bool wasCyl = IsCylinder(heldObject);
        if (wasCyl)
        {
            heldObject.freezeRotation = false;
        }

        // Destroy joint
        if (joint)
            Destroy(joint);

        // Physics cleanup
        heldObject.useGravity = true;
        heldObject.linearVelocity = holdPointRb.linearVelocity;
        heldObject.angularVelocity = holdPointRb.angularVelocity;

        // Update grabbable state
        Grabbable g = heldObject.GetComponent<Grabbable>();
        if (g)
            g.SetHeld(false);

        if (debugLogs)
            Debug.Log($"Released: {heldObject.name} (was pinch: {isPinchHeld})");

        joint = null;
        heldObject = null;
        isPinchHeld = false;
    }

    void OnJointBreak(float force)
    {
        if (heldObject)
        {
            heldObject.useGravity = true;
            heldObject = null;
        }
        joint = null;
    }
}
