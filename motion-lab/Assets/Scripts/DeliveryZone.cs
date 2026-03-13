using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(Collider))]
public class DeliveryZone : MonoBehaviour
{
    public LayerMask grabbableLayers = ~0;
    public bool debugLogs = false;

    private readonly HashSet<Rigidbody> _counted = new HashSet<Rigidbody>();
    private Collider _col;

    void Awake()
    {
        _col = GetComponent<Collider>();
        if (_col && !_col.isTrigger)
        {
            // MeshColliders can only be triggers if they are convex
            MeshCollider meshCol = _col as MeshCollider;
            if (meshCol != null && !meshCol.convex)
            {
                Debug.LogWarning(
                    $"[DeliveryZone] {gameObject.name} has a concave MeshCollider. Converting to BoxCollider for trigger support."
                );
                // Replace with BoxCollider
                BoxCollider boxCol = gameObject.AddComponent<BoxCollider>();
                boxCol.size = _col.bounds.size;
                boxCol.center = _col.bounds.center - transform.position;
                Destroy(_col);
                _col = boxCol;
            }
            _col.isTrigger = true;
        }
    }

    void OnValidate()
    {
        var c = GetComponent<Collider>();
        if (c)
        {
            // MeshColliders can only be triggers if they are convex
            MeshCollider meshCol = c as MeshCollider;
            if (meshCol != null && !meshCol.convex)
            {
                // Don't set trigger on concave mesh colliders - will be handled in Awake
                return;
            }
            c.isTrigger = true;
        }
    }

    void OnTriggerEnter(Collider other) => TryCount(other);

    void OnTriggerStay(Collider other) => TryCount(other);

    void TryCount(Collider other)
    {
        var rb = other.attachedRigidbody;
        if (!rb)
            return;

        if (((1 << rb.gameObject.layer) & grabbableLayers) == 0)
            return;

        if (_counted.Contains(rb))
            return;

        var g = rb.GetComponent<Grabbable>();
        bool isHeld = g != null && g.IsHeld;

        if (g == null)
        {
            bool hasJoint = rb.GetComponent<FixedJoint>() != null;
            bool gravityOff = rb.useGravity == false;
            isHeld = hasJoint || gravityOff;
        }

        if (isHeld)
        {
            if (debugLogs)
                Debug.Log($"DeliveryZone: {rb.name} inside but still held");
            return;
        }

        // Check for continuous tasks - tasks are managed by ContinuousTaskManager, not on the box itself
        // So we check if this is a box/cylinder from a continuous task by checking the name pattern
        // The actual completion is handled by the task's CheckTaskCompletion() method
        // This OnTriggerStay is just a backup - the main logic is in BoxDeliveryTask.CheckTaskCompletion()

        // For continuous tasks, the completion is handled by the task itself in CheckTaskCompletion()
        // which checks if box is released AND in zone. This trigger is just for legacy BoxTask system.

        // Legacy: Check for old BoxTask system
        BoxTask boxTask = rb.GetComponent<BoxTask>();
        if (boxTask && boxTask.taskType == TaskType.DeliverToBasket)
        {
            // Only if task is running (start was allowed)
            if (boxTask.startTime < 0f)
            {
                BoxTaskManager.Instance?.ShowWrongBoxHint();
                return;
            }

            _counted.Add(rb);
            boxTask.CompleteTask();
            if (debugLogs)
                Debug.Log($"DeliveryZone: delivered {rb.name}. Total: {_counted.Count}");
        }
    }

    public void ClearCount()
    {
        _counted.Clear();
    }
}
