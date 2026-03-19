// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public enum Handedness
{
    Left,
    Right,
}

/// <summary>
/// Defines how the HandController should interpret position data from messages.
/// </summary>
public enum PositionMode
{
    /// <summary>
    /// Use positionDelta - incremental movement (adds delta to current position).
    /// For tasks like BoxTask.
    /// </summary>
    Delta,

    /// <summary>
    /// Use positionState - discrete positions ("start", "forward", "right").
    /// For tasks like BoxDeliveryTask, CylinderDeliveryTask, BottlePouringTask, MarbleDeliveryTask.
    /// </summary>
    State,
}

public class HandController : MonoBehaviour
{
    [Header("Hand Settings")]
    [Tooltip("Select which hand to use. This mirrors the model and adjusts rotation directions.")]
    public Handedness handedness = Handedness.Right;

    [Header("Network")]
    public int listenPort = 5055;

    [Header("Position Mode")]
    [Tooltip("Current position mode - set by active task to control position interpretation")]
    public PositionMode currentPositionMode = PositionMode.State;

    [Header("Workspace Grid")]
    [Tooltip("Reference to WorkspaceGrid for position state mapping (auto-found if null)")]
    public WorkspaceGrid workspaceGrid;

    [Header("Motion")]
    [Tooltip("Approximate time in seconds to reach target position (higher = slower/smoother)")]
    public float positionSmoothTime = 0.2f;

    [Tooltip("Approximate time in seconds to reach target rotation")]
    public float rotationSmoothTime = 0.3f;
    public float curlSpeed = 10f;

    [Header("Grasp")]
    public float grabThreshold = 0.6f;

    [Header("Pinch")]
    [Tooltip("Threshold for thumb+index curl to detect pinch")]
    public float pinchThreshold = 0.6f;

    [Tooltip("Maximum curl for other fingers (middle, ring, pinky) to allow pinch")]
    public float pinchOtherFingersMaxCurl = 0.3f;

    /// <summary>
    /// Returns +1 for left hand, -1 for right hand.
    /// Use this to flip rotation directions based on handedness.
    /// </summary>
    public float HandednessMultiplier => handedness == Handedness.Right ? 1f : -1f;

    [Serializable]
    public class Finger
    {
        public Transform[] joints = new Transform[3];
        public Vector3 axis = new Vector3(-1, 0, 0);
        public float[] maxDegrees = new float[3] { 60, 90, 70 };

        [NonSerialized]
        public Quaternion[] startRot = new Quaternion[3];
    }

    [Header("Rig")]
    public Finger thumb = new Finger();
    public Finger index = new Finger();
    public Finger middle = new Finger();
    public Finger ring = new Finger();
    public Finger pinky = new Finger();

    private Thread networkThread;
    private UdpClient udpClient;
    private volatile HandMsg latestMessage;

    private Vector3 targetPos;
    private Quaternion targetRot;
    private float[] targetCurls = new float[5];
    private float[] currentCurls = new float[5];
    private float[] lastCurls = new float[5];

    // SmoothDamp velocity tracking
    private Vector3 positionVelocity;
    private Vector3 rotationVelocity;

    private float demoBlend = 0f; // 0..1 how much to visually blend to demo pose
    private float[] demoCurls = new float[5]; // Target curls for visual demo only

    public float GripValue { get; private set; }
    public bool IsGripping { get; private set; }
    public bool GripJustBecameTrue { get; private set; }
    public bool GripJustBecameFalse { get; private set; }

    // Pinch state (thumb + index curled, other fingers extended)
    public float PinchValue { get; private set; }
    public bool IsPinching { get; private set; }
    public bool PinchJustBecameTrue { get; private set; }
    public bool PinchJustBecameFalse { get; private set; }
    private bool wasPinching = false;

    public Vector3 CurrentPosition => transform.position;
    public Vector3 CurrentRotationEuler => transform.rotation.eulerAngles;

    private Vector3 externalPositionOffset = Vector3.zero;

    // Input freeze state - when frozen, messages are ignored but Update() still runs
    private bool isInputFrozen = false;

    /// <summary>
    /// Returns true if input processing is currently frozen.
    /// When frozen, UDP messages are ignored but the hand stays at its current position.
    /// </summary>
    public bool IsInputFrozen => isInputFrozen;

    public void SetPositionOffset(Vector3 offset)
    {
        externalPositionOffset = offset;
    }

    /// <summary>
    /// Freeze input processing. UDP messages will be ignored, but Update() still runs
    /// to keep the hand rendered at its current position. Use this during countdowns
    /// to prevent the hand from moving due to incoming messages.
    /// </summary>
    public void FreezeInput()
    {
        isInputFrozen = true;
        // Clear any pending message so it doesn't get processed when unfrozen
        latestMessage = null;
        Debug.Log("[HandController] Input FROZEN - ignoring incoming messages");
    }

    /// <summary>
    /// Unfreeze input processing. UDP messages will be processed again normally.
    /// </summary>
    public void UnfreezeInput()
    {
        isInputFrozen = false;
        // Clear any messages that accumulated while frozen
        latestMessage = null;
        Debug.Log("[HandController] Input UNFROZEN - processing messages again");
    }

    // Current state from bio-bridge (text labels)
    public string CurrentPositionState { get; private set; } = "start";
    public string CurrentGesture { get; private set; } = "rest";

    // Returns a defensive copy of the current curls (length=5, 0..1)
    public float[] GetCurrentCurlsCopy()
    {
        var copy = new float[5];
        for (int i = 0; i < 5; i++)
            copy[i] = currentCurls[i];
        return copy;
    }

    /// <summary>
    /// Message format from bio-bridge.
    ///
    /// Protocol:
    /// {
    ///     "positionDelta": [dx, dy, dz],           // Delta position
    ///     "positionState": "forward",               // "start", "forward", "right"
    ///     "gesture": "close",                       // "rest", "open", "close", "pinch"
    ///     "rotation": [flex, unused, supin],        // IMU-based rotation
    ///     "curls": [t, i, m, r, p]                  // Absolute finger curls
    /// }
    ///
    /// Unity decides which to use:
    /// - Position: positionState (discrete) OR positionDelta (continuous)
    /// - Rotation: Always IMU-based
    ///
    /// Note: Grabbing/pinching is controlled by "curls", NOT by "gesture".
    /// The gesture field is only used for UI display and GestureMovementController.
    /// </summary>
    [Serializable]
    private class HandMsg
    {
        // Position delta (for continuous movement)
        public float[] positionDelta; // [dx, dy, dz]

        // Position state label (for discrete movement)
        public string positionState; // "start", "forward", "right"

        // Gesture label (not used for grabbing/pinching)
        public string gesture; // "rest", "open", "close", "pinch"

        // Rotation (IMU-based)
        public float[] rotation; // [flexion, unused, supination]

        // Finger curls (absolute) - this controls grabbing/pinching
        public float[] curls; // [thumb, index, middle, ring, pinky]
    }

    void Start()
    {
        // Apply handedness (mirror the model for right hand)
        ApplyHandedness();

        // Save initial finger rotations
        SaveStartRotations(thumb);
        SaveStartRotations(index);
        SaveStartRotations(middle);
        SaveStartRotations(ring);
        SaveStartRotations(pinky);

        // Find WorkspaceGrid if not assigned
        if (workspaceGrid == null)
        {
            workspaceGrid = FindFirstObjectByType<WorkspaceGrid>();
        }

        // Set initial position from grid (position state 0 = Start)
        if (workspaceGrid != null)
        {
            transform.position = workspaceGrid.GetWorldPositionForState(PositionState.Start);
            Debug.Log($"[HandController] Initial position: {transform.position} (State: Start)");
        }
        else
        {
            transform.position = new Vector3(0.0f, 0.5f, 0.0f);
            Debug.LogWarning("[HandController] No WorkspaceGrid found! Using origin.");
        }

        targetPos = transform.position;
        targetRot = transform.rotation;

        try
        {
            udpClient = new UdpClient(listenPort);
            networkThread = new Thread(NetworkLoop);
            networkThread.IsBackground = true;
            networkThread.Start();
            Debug.Log($"HandController ({handedness} hand) listening on port {listenPort}");
        }
        catch (Exception e)
        {
            Debug.LogError("Failed to start UDP: " + e);
            enabled = false;
        }
    }

    void ApplyHandedness()
    {
        // Mirror the hand model by flipping X scale
        Vector3 scale = transform.localScale;
        scale.x = Mathf.Abs(scale.x) * HandednessMultiplier;
        transform.localScale = scale;
    }

    // Called by Unity Editor when values change in Inspector (works in Edit mode!)
    void OnValidate()
    {
        ApplyHandedness();
    }

    void SaveStartRotations(Finger f)
    {
        for (int i = 0; i < f.joints.Length; i++)
        {
            if (f.joints[i])
                f.startRot[i] = f.joints[i].localRotation;
        }
    }

    void NetworkLoop()
    {
        IPEndPoint endpoint = new IPEndPoint(IPAddress.Any, listenPort);

        while (true)
        {
            try
            {
                byte[] data = udpClient.Receive(ref endpoint);
                string json = Encoding.UTF8.GetString(data).Trim();

                try
                {
                    HandMsg msg = JsonUtility.FromJson<HandMsg>(json);
                    if (msg != null)
                        latestMessage = msg;
                }
                catch { }
            }
            catch (SocketException)
            {
                break;
            }
            catch (Exception ex)
            {
                Debug.LogWarning("Network error: " + ex.Message);
            }
        }
    }

    /// <summary>
    /// Reset hand to start position with neutral rotation and open fingers - INSTANTLY!
    /// Called at the beginning of each task (during countdown).
    /// Also clears any pending UDP messages to prevent them from overriding the reset.
    /// </summary>
    /// <param name="startPosition">The position to reset the hand to</param>
    public void ResetToStartPosition(Vector3 startPosition)
    {
        // Clear any pending message FIRST to prevent it from overriding our reset
        latestMessage = null;

        // INSTANT: Teleport position
        targetPos = startPosition;
        transform.position = startPosition;
        positionVelocity = Vector3.zero;

        // INSTANT: Reset supination/pronation to 0 (neutral rotation [0, 0, 0])
        targetRot = Quaternion.Euler(0f, 0f, 0f);
        transform.rotation = Quaternion.Euler(0f, 0f, 0f);
        rotationVelocity = Vector3.zero;

        // INSTANT: Set finger curls to [0, 0, 0, 0, 0] (open hand)
        // Only set the curl VALUES - do NOT call ApplyFingers() to avoid touching joints directly
        for (int i = 0; i < 5; i++)
        {
            targetCurls[i] = 0f;
            currentCurls[i] = 0f;
        }

        // Reset position offset (in case it was set by a task like bottle pouring)
        externalPositionOffset = Vector3.zero;

        // Reset gesture state
        CurrentGesture = "open";

        Debug.Log($"[HandController] INSTANT RESET to position: {startPosition}, rotation: [0,0,0], curls: [0,0,0,0,0], gesture: open");
    }

    void Update()
    {
        HandleMessage();
        SmoothTransform();
        SmoothCurls();
        ApplyFingers();
        UpdateGripState();
        UpdatePinchState();
    }

    void HandleMessage()
    {
        if (latestMessage == null)
            return;

        // Skip message processing if input is frozen (during countdown)
        if (isInputFrozen)
        {
            latestMessage = null; // Discard the message
            return;
        }

        HandMsg msg = latestMessage;
        latestMessage = null;

        // ═════════════════════════════════════════════════════════════════
        // POSITION PROCESSING
        // Mode is controlled by currentPositionMode (set by active task)
        // ═════════════════════════════════════════════════════════════════

        if (currentPositionMode == PositionMode.Delta)
        {
            // ─────────────────────────────────────────────────────────────
            // Position Delta Mode (for incremental movement)
            // Used by: BoxTask, RotationTask
            // ─────────────────────────────────────────────────────────────
            if (msg.positionDelta != null && msg.positionDelta.Length == 3)
            {
                Vector3 position_delta = new Vector3(
                    msg.positionDelta[0],
                    msg.positionDelta[1],
                    msg.positionDelta[2]
                );

                // Add delta to current target position
                targetPos += position_delta;
            }

            // Still update CurrentPositionState for potential reading by tasks
            if (!string.IsNullOrEmpty(msg.positionState))
            {
                CurrentPositionState = msg.positionState.ToLower();
            }
        }
        else // PositionMode.State
        {
            // ─────────────────────────────────────────────────────────────
            // Position State Mode (for discrete positions)
            // Used by: BoxDeliveryTask, CylinderDeliveryTask, etc.
            // ─────────────────────────────────────────────────────────────
            if (!string.IsNullOrEmpty(msg.positionState))
            {
                CurrentPositionState = msg.positionState.ToLower();

                // Map state label to position
                int stateIndex = CurrentPositionState switch
                {
                    "start" => 0,
                    "forward" => 1,
                    "right" => 2,
                    _ => -1,
                };

                if (stateIndex >= 0)
                {
                    if (workspaceGrid != null)
                    {
                        targetPos = workspaceGrid.GetWorldPositionForState(stateIndex);
                    }
                    else
                    {
                        targetPos = WorkspaceGrid.GetPositionForState(stateIndex);
                    }
                }
            }
        }

        // ─────────────────────────────────────────────────────────────────
        // Gesture (label: "rest", "open", "close", "pinch")
        // ─────────────────────────────────────────────────────────────────
        if (!string.IsNullOrEmpty(msg.gesture))
        {
            CurrentGesture = msg.gesture.ToLower();
        }

        // ─────────────────────────────────────────────────────────────────
        // Rotation (IMU-based)
        // ─────────────────────────────────────────────────────────────────
        float[] rotationData = msg.rotation;

        if (rotationData != null && rotationData.Length == 3)
        {
            float x = Mathf.Clamp(
                rotationData[0],
                HandRotationLimits.FLEXION_MAX,
                HandRotationLimits.EXTENSION_MAX
            ); // Flexion/Extension
            float y = 0f; // Unused

            // Supination direction depends on handedness
            float z =
                -HandednessMultiplier
                * Mathf.Clamp(
                    rotationData[2],
                    HandRotationLimits.PRONATION_MAX,
                    HandRotationLimits.SUPINATION_MAX
                );

            targetRot = Quaternion.Euler(x, y, z);
        }

        // ─────────────────────────────────────────────────────────────────
        // Curls (absolute: [thumb, index, middle, ring, pinky])
        // ─────────────────────────────────────────────────────────────────
        if (msg.curls != null && msg.curls.Length == 5)
        {
            for (int i = 0; i < 5; i++)
            {
                targetCurls[i] = Mathf.Clamp01(msg.curls[i]);
            }
        }
    }

    void SmoothTransform()
    {
        // SmoothDamp provides smooth ease-in-out motion with configurable time
        transform.position = Vector3.SmoothDamp(
            transform.position,
            targetPos + externalPositionOffset,
            ref positionVelocity,
            positionSmoothTime
        );

        // For rotation, use SmoothDampAngle on each axis for smooth interpolation
        Vector3 currentEuler = transform.rotation.eulerAngles;
        Vector3 targetEuler = targetRot.eulerAngles;

        float smoothX = Mathf.SmoothDampAngle(
            currentEuler.x,
            targetEuler.x,
            ref rotationVelocity.x,
            rotationSmoothTime
        );
        float smoothY = Mathf.SmoothDampAngle(
            currentEuler.y,
            targetEuler.y,
            ref rotationVelocity.y,
            rotationSmoothTime
        );
        float smoothZ = Mathf.SmoothDampAngle(
            currentEuler.z,
            targetEuler.z,
            ref rotationVelocity.z,
            rotationSmoothTime
        );

        transform.rotation = Quaternion.Euler(smoothX, smoothY, smoothZ);
    }

    void SmoothCurls()
    {
        for (int i = 0; i < 5; i++)
        {
            currentCurls[i] = Mathf.Lerp(
                currentCurls[i],
                targetCurls[i],
                Time.deltaTime * curlSpeed
            );
        }
    }

    void ApplyFingers()
    {
        ApplyFinger(thumb, GetVisualCurl(0));
        ApplyFinger(index, GetVisualCurl(1));
        ApplyFinger(middle, GetVisualCurl(2));
        ApplyFinger(ring, GetVisualCurl(3));
        ApplyFinger(pinky, GetVisualCurl(4));
    }

    void ApplyFinger(Finger f, float curl)
    {
        for (int i = 0; i < f.joints.Length; i++)
        {
            if (!f.joints[i])
                continue;

            float angle = f.maxDegrees[i] * curl;
            Quaternion bend = Quaternion.AngleAxis(angle, f.axis);
            f.joints[i].localRotation = f.startRot[i] * bend;
        }
    }

    // Returns the value used for rendering (currentCurls blended with demoCurls)
    float GetVisualCurl(int i)
    {
        float baseVal = currentCurls[i];
        if (demoBlend <= 0f)
            return baseVal;
        return Mathf.Lerp(baseVal, demoCurls[i], demoBlend);
    }

    void UpdateGripState()
    {
        float avgCurrent = 0;
        float avgLast = 0;

        for (int i = 0; i < 5; i++)
        {
            avgCurrent += currentCurls[i];
            avgLast += lastCurls[i];
        }

        avgCurrent /= 5f;
        avgLast /= 5f;

        bool wasGripping = avgLast >= grabThreshold;
        bool isGripping = avgCurrent >= grabThreshold;

        GripJustBecameTrue = !wasGripping && isGripping;
        GripJustBecameFalse = wasGripping && !isGripping;
        GripValue = avgCurrent;
        IsGripping = isGripping;

        for (int i = 0; i < 5; i++)
            lastCurls[i] = currentCurls[i];
    }

    void UpdatePinchState()
    {
        // Pinch = thumb + index curled, other fingers (middle, ring, pinky) extended
        // currentCurls: [0]=thumb, [1]=index, [2]=middle, [3]=ring, [4]=pinky
        float thumbCurl = currentCurls[0];
        float indexCurl = currentCurls[1];
        float otherFingersCurl = (currentCurls[2] + currentCurls[3] + currentCurls[4]) / 3f;

        // Pinch value = average of thumb and index curl
        PinchValue = (thumbCurl + indexCurl) / 2f;

        // Is pinching if thumb+index are curled AND other fingers are extended
        bool isPinching =
            (thumbCurl >= pinchThreshold)
            && (indexCurl >= pinchThreshold)
            && (otherFingersCurl <= pinchOtherFingersMaxCurl);

        PinchJustBecameTrue = !wasPinching && isPinching;
        PinchJustBecameFalse = wasPinching && !isPinching;
        IsPinching = isPinching;
        wasPinching = isPinching;
    }

    void OnApplicationQuit()
    {
        if (udpClient != null)
        {
            try
            {
                udpClient.Close();
            }
            catch { }
        }

        if (networkThread != null)
        {
            try
            {
                networkThread.Abort();
            }
            catch { }
        }
    }

    // Set a visual demo pose by curls (values 0..1). Only affects rendering, not GripValue.
    public void SetDemoPose(float[] curls, float blend = 1f)
    {
        if (curls == null || curls.Length != 5)
            return;
        for (int i = 0; i < 5; i++)
            demoCurls[i] = Mathf.Clamp01(curls[i]);
        demoBlend = Mathf.Clamp01(blend);
    }

    // Convenience: fully open/fist poses for demo
    public void SetDemoOpen(float blend = 1f)
    {
        SetDemoPose(new float[] { 0f, 0f, 0f, 0f, 0f }, blend);
    }

    public void SetDemoFist(float blend = 1f)
    {
        SetDemoPose(new float[] { 1f, 1f, 1f, 1f, 1f }, blend);
    }

    // Remove visual demo (instantly)
    public void ClearDemoPose()
    {
        demoBlend = 0f;
    }
}
