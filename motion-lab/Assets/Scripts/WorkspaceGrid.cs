// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Position states for hand movement (from bio-bridge protocol).
/// </summary>
public enum PositionState
{
    Start = 0, // Initial position (grid: 0, -1) - user/camera side
    Forward = 1, // Center position (grid: 0, 0) - at object
    Right = 2, // Right position (grid: 1, 0) - at delivery zone
}

/// <summary>
/// Gesture labels for NN predictions (from bio-bridge protocol).
/// </summary>
public enum GestureLabel
{
    Rest = 0, // Initial state / Rest
    Open = 1, // Hand open
    Fist = 2, // Grabbing (hand close)
    Pinch = 3, // Pinching (thumb + index)
}

/// <summary>
/// Central workspace grid configuration.
/// Maps normalized grid coordinates [-1, 1] to Unity world coordinates.
/// Also maps discrete position states (0, 1, 2) from bio-bridge to grid coordinates.
///
/// Grid Layout (from PDF):
///   - Grid X → Unity X
///   - Grid Y → Unity Z (forward/back in Unity)
///   - Unity Y is fixed (height)
///
/// Position States (discrete, from bio-bridge):
///   - 0: Start   → (0, -1) → user/camera side
///   - 1: Forward → (0, 0)  → center, at object
///   - 2: Right   → (1, 0)  → right side, at delivery zone
///
/// Key positions (normalized):
///   - Hand Start: (0, -1) → user/camera side
///   - Objects: (0, 0) → center of workspace
///   - Delivery Zone: (1, 0) → right side
/// </summary>
public class WorkspaceGrid : MonoBehaviour
{
    [Header("Grid Scale")]
    [Tooltip("Scale factor: normalized [-1,1] maps to [-scale, scale] in Unity units")]
    public float gridScale = 4.0f;

    [Header("Fixed Height (Unity Y)")]
    [Tooltip("Fixed Y coordinate for objects (table height)")]
    public float objectHeight = 0.5f;

    [Tooltip("Fixed Y coordinate for hand")]
    public float handHeight = 0.5f;

    [Tooltip("Fixed Y coordinate for delivery zone")]
    public float deliveryZoneHeight = 0.0f;

    [Header("Position State Mapping (Normalized Grid Coords)")]
    [Tooltip("Position 0: Start - user/camera side")]
    public Vector2 positionStateStart = new Vector2(0f, -1f);

    [Tooltip("Position 1: Forward - center, at object")]
    public Vector2 positionStateForward = new Vector2(0f, 0f);

    [Tooltip("Position 2: Right - center of delivery zone")]
    public Vector2 positionStateRight = new Vector2(0.8f, 0f);

    [Header("Default Normalized Positions")]
    [Tooltip("Hand start position in normalized grid coords (x, y where y→Unity Z)")]
    public Vector2 handStartNormalized = new Vector2(0f, -1f);

    [Tooltip("Object spawn position in normalized grid coords")]
    public Vector2 objectSpawnNormalized = new Vector2(0f, 0f);

    [Tooltip("Delivery zone position in normalized grid coords")]
    public Vector2 deliveryZoneNormalized = new Vector2(0.8f, 0f);

    [Header("Debug")]
    public bool showGizmos = true;
    public Color gridColor = new Color(0.5f, 0.5f, 1f, 0.3f);
    public Color handStartColor = Color.green;
    public Color objectSpawnColor = Color.yellow;
    public Color deliveryZoneColor = Color.red;

    /// <summary>
    /// Singleton instance for easy access.
    /// </summary>
    public static WorkspaceGrid Instance { get; private set; }

    void Awake()
    {
        if (Instance == null)
            Instance = this;
        else if (Instance != this)
            Debug.LogWarning("[WorkspaceGrid] Multiple instances found! Using first one.");
    }

    /// <summary>
    /// Convert normalized grid position (x, y) to Unity world position.
    /// Grid Y maps to Unity Z.
    /// </summary>
    /// <param name="normalizedX">X in range [-1, 1]</param>
    /// <param name="normalizedY">Y in range [-1, 1] (maps to Unity Z)</param>
    /// <param name="unityY">Fixed Unity Y coordinate (height)</param>
    /// <returns>Unity world position</returns>
    public Vector3 NormalizedToWorld(float normalizedX, float normalizedY, float unityY)
    {
        return new Vector3(normalizedX * gridScale, unityY, normalizedY * gridScale);
    }

    /// <summary>
    /// Convert normalized Vector2 (grid x, grid y) to Unity world position.
    /// </summary>
    public Vector3 NormalizedToWorld(Vector2 normalized, float unityY)
    {
        return NormalizedToWorld(normalized.x, normalized.y, unityY);
    }

    /// <summary>
    /// Convert Unity world position to normalized grid coordinates.
    /// </summary>
    public Vector2 WorldToNormalized(Vector3 worldPos)
    {
        return new Vector2(worldPos.x / gridScale, worldPos.z / gridScale);
    }

    /// <summary>
    /// Get the hand start position in Unity world coordinates.
    /// </summary>
    public Vector3 GetHandStartPosition()
    {
        return NormalizedToWorld(handStartNormalized, handHeight);
    }

    /// <summary>
    /// Get the object spawn position in Unity world coordinates.
    /// </summary>
    public Vector3 GetObjectSpawnPosition()
    {
        return NormalizedToWorld(objectSpawnNormalized, objectHeight);
    }

    /// <summary>
    /// Get the delivery zone position in Unity world coordinates.
    /// </summary>
    public Vector3 GetDeliveryZonePosition()
    {
        return NormalizedToWorld(deliveryZoneNormalized, deliveryZoneHeight);
    }

    /// <summary>
    /// Static helper: Convert normalized position to world using Instance settings.
    /// Falls back to default scale if no instance exists.
    /// </summary>
    public static Vector3 ToWorld(float normalizedX, float normalizedY, float unityY)
    {
        if (Instance != null)
            return Instance.NormalizedToWorld(normalizedX, normalizedY, unityY);

        // Fallback with default scale
        float defaultScale = 2.0f;
        return new Vector3(normalizedX * defaultScale, unityY, normalizedY * defaultScale);
    }

    /// <summary>
    /// Static helper: Convert normalized Vector2 to world.
    /// </summary>
    public static Vector3 ToWorld(Vector2 normalized, float unityY)
    {
        return ToWorld(normalized.x, normalized.y, unityY);
    }

    /// <summary>
    /// Static helper: Convert world position to normalized.
    /// </summary>
    public static Vector2 ToNormalized(Vector3 worldPos)
    {
        if (Instance != null)
            return Instance.WorldToNormalized(worldPos);

        float defaultScale = 2.0f;
        return new Vector2(worldPos.x / defaultScale, worldPos.z / defaultScale);
    }

    /// <summary>
    /// Get grid scale (static access).
    /// </summary>
    public static float Scale => Instance != null ? Instance.gridScale : 4.0f;

    // =========================================================================
    // Position State Mapping (from bio-bridge protocol)
    // =========================================================================

    /// <summary>
    /// Get normalized grid position for a discrete position state.
    /// </summary>
    /// <param name="state">Position state: 0=Start, 1=Forward, 2=Right</param>
    /// <returns>Normalized grid coordinates (x, y)</returns>
    public Vector2 GetNormalizedForState(int state)
    {
        switch (state)
        {
            case 0:
                return positionStateStart;
            case 1:
                return positionStateForward;
            case 2:
                return positionStateRight;
            default:
                Debug.LogWarning($"[WorkspaceGrid] Unknown position state: {state}, using Start");
                return positionStateStart;
        }
    }

    /// <summary>
    /// Get normalized grid position for a PositionState enum.
    /// </summary>
    public Vector2 GetNormalizedForState(PositionState state)
    {
        return GetNormalizedForState((int)state);
    }

    /// <summary>
    /// Get Unity world position for a discrete position state.
    /// </summary>
    /// <param name="state">Position state: 0=Start, 1=Forward, 2=Right</param>
    /// <returns>Unity world position</returns>
    public Vector3 GetWorldPositionForState(int state)
    {
        Vector2 normalized = GetNormalizedForState(state);
        return NormalizedToWorld(normalized, handHeight);
    }

    /// <summary>
    /// Get Unity world position for a PositionState enum.
    /// </summary>
    public Vector3 GetWorldPositionForState(PositionState state)
    {
        return GetWorldPositionForState((int)state);
    }

    /// <summary>
    /// Static helper: Get world position for position state.
    /// </summary>
    public static Vector3 GetPositionForState(int state)
    {
        if (Instance != null)
            return Instance.GetWorldPositionForState(state);

        // Fallback with defaults
        float defaultScale = 4.0f;
        float defaultHeight = 0.5f;
        Vector2 normalized;
        switch (state)
        {
            case 0:
                normalized = new Vector2(0f, -1f);
                break; // Start
            case 1:
                normalized = new Vector2(0f, 0f);
                break; // Forward (object)
            case 2:
                normalized = new Vector2(0.8f, 0f);
                break; // Right (delivery zone center)
            default:
                normalized = new Vector2(0f, -1f);
                break;
        }
        return new Vector3(normalized.x * defaultScale, defaultHeight, normalized.y * defaultScale);
    }

    void OnDrawGizmos()
    {
        if (!showGizmos)
            return;

        // Draw grid bounds
        Gizmos.color = gridColor;
        Vector3 center = new Vector3(0, objectHeight, 0);
        Vector3 size = new Vector3(gridScale * 2, 0.01f, gridScale * 2);
        Gizmos.DrawCube(center, size);

        // Draw grid lines
        Gizmos.color = new Color(gridColor.r, gridColor.g, gridColor.b, 0.5f);
        for (float i = -1; i <= 1; i += 0.25f)
        {
            // Vertical lines (along Z)
            Vector3 start = NormalizedToWorld(i, -1, objectHeight);
            Vector3 end = NormalizedToWorld(i, 1, objectHeight);
            Gizmos.DrawLine(start, end);

            // Horizontal lines (along X)
            start = NormalizedToWorld(-1, i, objectHeight);
            end = NormalizedToWorld(1, i, objectHeight);
            Gizmos.DrawLine(start, end);
        }

        // Draw key positions
        float sphereRadius = 0.15f;

        // Position State 0: Start (hand start)
        Gizmos.color = handStartColor;
        Vector3 startPos = GetWorldPositionForState(0);
        Gizmos.DrawSphere(startPos, sphereRadius);
        Gizmos.DrawWireSphere(startPos, sphereRadius * 1.5f);
#if UNITY_EDITOR
        UnityEditor.Handles.Label(startPos + Vector3.up * 0.3f, "State 0: Start");
#endif

        // Position State 1: Forward (at object)
        Gizmos.color = objectSpawnColor;
        Vector3 forwardPos = GetWorldPositionForState(1);
        Gizmos.DrawSphere(forwardPos, sphereRadius);
        Gizmos.DrawWireSphere(forwardPos, sphereRadius * 1.5f);
#if UNITY_EDITOR
        UnityEditor.Handles.Label(forwardPos + Vector3.up * 0.3f, "State 1: Forward");
#endif

        // Position State 2: Right (delivery zone)
        Gizmos.color = deliveryZoneColor;
        Vector3 rightPos = GetWorldPositionForState(2);
        Gizmos.DrawSphere(rightPos, sphereRadius);
        Gizmos.DrawWireSphere(rightPos, sphereRadius * 1.5f);
#if UNITY_EDITOR
        UnityEditor.Handles.Label(rightPos + Vector3.up * 0.3f, "State 2: Right");
#endif

        // Draw path between states
        Gizmos.color = new Color(1f, 1f, 1f, 0.5f);
        Gizmos.DrawLine(startPos, forwardPos);
        Gizmos.DrawLine(forwardPos, rightPos);
    }
}
