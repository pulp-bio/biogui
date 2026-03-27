// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

public class MiddlewareClient : MonoBehaviour
{
    [Header("UDP Connection")]
    public string host = "127.0.0.1";
    public int port = 6000; // Online training port
    public bool autoConnectOnStart = true;

    [Header("Debug")]
    public bool debugLogs = false;

    private UdpClient udpClient;
    private IPEndPoint udpEndpoint;
    private bool ready;

    void Start()
    {
        if (autoConnectOnStart)
        {
            Connect();
        }
    }

    public void Connect()
    {
        try
        {
            udpClient = new UdpClient();
            udpEndpoint = new IPEndPoint(IPAddress.Parse(host), port);
            ready = true;
            Debug.Log($"[MiddlewareClient] Connected to {host}:{port}");
        }
        catch (Exception ex)
        {
            ready = false;
            Debug.LogError($"[MiddlewareClient] Connection failed: {ex.Message}");
        }
    }

    public void Disconnect()
    {
        try
        {
            udpClient?.Close();
        }
        catch { }

        udpClient = null;
        ready = false;

        if (debugLogs)
            Debug.Log("[MiddlewareClient] Disconnected");
    }

    void OnApplicationQuit()
    {
        Disconnect();
    }

    // ============================================================================
    // GESTURE MESSAGES (for online training)
    // ============================================================================

    [Serializable]
    private class GestureMessage
    {
        public string gesture; // "rest", "fist", "open"
        public long timestamp; // Absolute Unix timestamp in milliseconds (from DateTimeOffset.UtcNow)
        public int duration; // Duration of gesture phase in milliseconds
    }

    /// <summary>
    /// Send current gesture to middleware with absolute Unix timestamp and duration.
    /// </summary>
    /// <param name="gesture">Gesture type: "rest", "fist", or "open"</param>
    /// <param name="timestampMs">Absolute Unix timestamp in milliseconds</param>
    /// <param name="durationMs">Duration of gesture phase in milliseconds</param>
    public bool SendGesture(string gesture, long timestampMs, int durationMs)
    {
        if (!ready)
        {
            Connect();
            if (!ready)
                return false;
        }

        try
        {
            var msg = new GestureMessage
            {
                gesture = gesture,
                timestamp = timestampMs,
                duration = durationMs,
            };
            string json = JsonUtility.ToJson(msg);
            byte[] payload = Encoding.UTF8.GetBytes(json);

            udpClient.Send(payload, payload.Length, udpEndpoint);

            if (debugLogs)
                Debug.Log(
                    $"[MiddlewareClient] Sent gesture: {gesture}, timestamp: {timestampMs}, duration: {durationMs}ms"
                );

            return true;
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"[MiddlewareClient] Send failed: {ex.Message}");
            ready = false;
            return false;
        }
    }

    // ============================================================================
    // FINISH SIGNAL (triggers training)
    // ============================================================================

    [Serializable]
    private class FinishMessage
    {
        public string action; // "finish"
    }

    /// <summary>
    /// Send finish signal to middleware.
    /// This triggers the final model training with all collected data.
    /// </summary>
    public bool SendFinishTraining()
    {
        if (!ready)
        {
            Connect();
            if (!ready)
                return false;
        }

        try
        {
            var msg = new FinishMessage { action = "finish" };
            string json = JsonUtility.ToJson(msg);
            byte[] payload = Encoding.UTF8.GetBytes(json);

            udpClient.Send(payload, payload.Length, udpEndpoint);

            Debug.Log("[MiddlewareClient] Sent FINISH signal - training will start");

            return true;
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"[MiddlewareClient] Finish signal failed: {ex.Message}");
            ready = false;
            return false;
        }
    }

    // ============================================================================
    // LEGACY METHODS (kept for compatibility)
    // ============================================================================

    /// <summary>
    /// Legacy method - now just calls SendGesture internally.
    /// </summary>
    [Obsolete("Use SendGesture() instead")]
    public bool SendLabelEventMinimal(string gesture, long startUnixMs, int durationMs)
    {
        return SendGesture(gesture, startUnixMs, durationMs);
    }

    /// <summary>
    /// Legacy method - now calls SendFinishTraining().
    /// </summary>
    [Obsolete("Use SendFinishTraining() instead")]
    public bool SendSessionEnd()
    {
        return SendFinishTraining();
    }
}
