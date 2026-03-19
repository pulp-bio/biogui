// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

public class RotationTracker : MonoBehaviour
{
    private BoxTask boxTask;
    private Rigidbody rb;
    private bool isHeld = false;
    private Transform handTransform;
    private HandController handController;

    private Vector3 initialHandEuler; // Hand Euler angles when grabbed

    // Live display (smoothed)
    public float CurrentAngleDeg { get; private set; }
    public bool IsHeld => isHeld;

    [Header("Stability")]
    public float angleSmooth = 12f; // Smoothing (Lerp factor)
    public float hitToleranceDeg = 3f; // Tolerance when reaching ±target

    [Header("Debug")]
    public bool showDebugInfo = false;

    void Awake()
    {
        boxTask = GetComponent<BoxTask>();
        rb = GetComponent<Rigidbody>();
        handController = FindFirstObjectByType<HandController>();
    }

    public void OnGrabbed(Transform handTrans)
    {
        if (isHeld)
            return;

        isHeld = true;
        handTransform = handTrans;

        // Save the HAND's Euler angles when grabbed
        Vector3 handEuler = handTrans.rotation.eulerAngles;
        initialHandEuler = new Vector3(
            NormalizeAngle(handEuler.x),
            NormalizeAngle(handEuler.y),
            NormalizeAngle(handEuler.z)
        );

        boxTask?.StartTask();
        CurrentAngleDeg = 0f;

        if (showDebugInfo)
        {
            Debug.Log($"[RotationTracker] Grabbed. Initial hand euler: {initialHandEuler}");
        }
    }

    public void OnReleased()
    {
        if (!isHeld)
            return;

        isHeld = false;
        handTransform = null;

        // Only complete rotation tasks here
        if (boxTask && !boxTask.isComplete && boxTask.taskType != TaskType.DeliverToBasket)
        {
            if (boxTask.hasReachedTarget && boxTask.hasReturnedToStart)
                boxTask.CompleteTask();
        }

        CurrentAngleDeg = 0f;
    }

    void Update()
    {
        if (!isHeld || !boxTask || boxTask.isComplete || handTransform == null)
            return;

        // Get current hand rotation - works with both IMU and manual control!
        Vector3 currentHandEuler = handTransform.rotation.eulerAngles;
        currentHandEuler = new Vector3(
            NormalizeAngle(currentHandEuler.x),
            NormalizeAngle(currentHandEuler.y),
            NormalizeAngle(currentHandEuler.z)
        );

        float rawAngle = 0f;

        // Get handedness multiplier (flips angle direction for right hand)
        float handMult = handController != null ? handController.HandednessMultiplier : 1f;

        if (boxTask.taskType == TaskType.SupinationRotation)
        {
            // Supination = Z-Rotation, direction depends on handedness
            rawAngle = -handMult * GetAngleDelta(initialHandEuler.z, currentHandEuler.z);
        }
        else if (boxTask.taskType == TaskType.FlexionExtensionRotation)
        {
            // Flexion/Extension = X-Rotation of the hand
            // Positive = Flexion (bend down), Negative = Extension (bend up)
            rawAngle = GetAngleDelta(initialHandEuler.x, currentHandEuler.x);
        }

        if (showDebugInfo)
        {
            Debug.Log(
                $"[RotationTracker] Hand Euler: {currentHandEuler}, Raw Angle: {rawAngle:F1}°"
            );
        }

        CheckThresholds(rawAngle);

        // Smooth display for UI
        CurrentAngleDeg = Mathf.Lerp(CurrentAngleDeg, rawAngle, Time.deltaTime * angleSmooth);
    }

    void CheckThresholds(float rawAngle)
    {
        if (boxTask.taskType == TaskType.SupinationRotation)
        {
            // Supination: first to requiredAngle (positive), then back to ~0
            if (!boxTask.hasReachedTarget && rawAngle >= (boxTask.requiredAngle - hitToleranceDeg))
            {
                boxTask.hasReachedTarget = true;
                if (showDebugInfo)
                    Debug.Log($"[RotationTracker] ✓ Reached target {boxTask.requiredAngle}°");
            }

            if (
                boxTask.hasReachedTarget
                && !boxTask.hasReturnedToStart
                && Mathf.Abs(rawAngle) <= hitToleranceDeg
            )
            {
                boxTask.hasReturnedToStart = true;
                if (showDebugInfo)
                    Debug.Log($"[RotationTracker] ✓ Returned to 0°");
            }
        }
        else if (boxTask.taskType == TaskType.FlexionExtensionRotation)
        {
            // Flexion/Extension: +requiredAngle (Flex) -> -requiredAngle (Extend) -> 0 (Neutral)
            if (!boxTask.hasReachedTarget && rawAngle >= (boxTask.requiredAngle - hitToleranceDeg))
            {
                boxTask.hasReachedTarget = true;
                if (showDebugInfo)
                    Debug.Log($"[RotationTracker] Reached FLEXION +{boxTask.requiredAngle}");
            }

            if (
                boxTask.hasReachedTarget
                && !boxTask.hasReachedExtension
                && rawAngle <= -(boxTask.requiredAngle - hitToleranceDeg)
            )
            {
                boxTask.hasReachedExtension = true;
                if (showDebugInfo)
                    Debug.Log($"[RotationTracker] Reached EXTENSION -{boxTask.requiredAngle}");
            }

            if (
                boxTask.hasReachedTarget
                && boxTask.hasReachedExtension
                && !boxTask.hasReturnedToStart
                && Mathf.Abs(rawAngle) <= hitToleranceDeg
            )
            {
                boxTask.hasReturnedToStart = true;
                if (showDebugInfo)
                    Debug.Log($"[RotationTracker] Returned to NEUTRAL 0");
            }
        }
    }

    float GetAngleDelta(float startAngle, float currentAngle)
    {
        float delta = currentAngle - startAngle;

        // Normalize to [-180, 180] (shortest path)
        while (delta > 180f)
            delta -= 360f;
        while (delta < -180f)
            delta += 360f;

        return delta;
    }

    float NormalizeAngle(float angle)
    {
        while (angle > 180f)
            angle -= 360f;
        while (angle < -180f)
            angle += 360f;
        return angle;
    }
}
