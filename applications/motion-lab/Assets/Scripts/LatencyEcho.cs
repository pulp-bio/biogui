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

/// <summary>
/// Simple component to echo ping messages for latency testing.
/// Add this to any GameObject when you want to test roundtrip latency.
///
/// Usage:
///   python latency_test.py
/// </summary>
public class LatencyEcho : MonoBehaviour
{
    [Header("Settings")]
    [Tooltip("Enable/disable latency echo service")]
    public bool enableLatencyTest = false;

    [Header("Network")]
    [Tooltip("Port to listen for ping messages")]
    public int listenPort = 5057;

    [Tooltip("Port to send echo responses to")]
    public int responsePort = 5056;

    [Tooltip("Host to send responses to")]
    public string responseHost = "127.0.0.1";

    [Header("Debug")]
    public bool logPings = false;

    private Thread listenThread;
    private UdpClient udpClient;
    private UdpClient sendClient;
    private volatile bool running;

    void Start()
    {
        if (!enableLatencyTest)
        {
            Debug.Log("LatencyEcho: disabled (enable via Inspector toggle)");
            return;
        }

        try
        {
            udpClient = new UdpClient(listenPort);
            sendClient = new UdpClient();
            running = true;

            listenThread = new Thread(ListenLoop);
            listenThread.IsBackground = true;
            listenThread.Start();

            Debug.Log(
                $"LatencyEcho: listening on port {listenPort}, responding to {responseHost}:{responsePort}"
            );
        }
        catch (Exception e)
        {
            Debug.LogError($"LatencyEcho: failed to start - {e.Message}");
            enabled = false;
        }
    }

    void ListenLoop()
    {
        IPEndPoint endpoint = new IPEndPoint(IPAddress.Any, listenPort);
        IPEndPoint responseEndpoint = new IPEndPoint(IPAddress.Parse(responseHost), responsePort);

        while (running)
        {
            try
            {
                byte[] data = udpClient.Receive(ref endpoint);
                string json = Encoding.UTF8.GetString(data).Trim();

                // Check if it's a ping message (contains "ping" field)
                if (json.Contains("\"ping\""))
                {
                    // Echo it back immediately
                    byte[] response = Encoding.UTF8.GetBytes(json);
                    sendClient.Send(response, response.Length, responseEndpoint);

                    if (logPings)
                    {
                        Debug.Log($"LatencyEcho: ping received and echoed");
                    }
                }
            }
            catch (SocketException)
            {
                // Socket closed, exit loop
                break;
            }
            catch (Exception ex)
            {
                if (running)
                {
                    Debug.LogWarning($"LatencyEcho: {ex.Message}");
                }
            }
        }
    }

    void OnDestroy()
    {
        running = false;

        try
        {
            udpClient?.Close();
        }
        catch { }
        try
        {
            sendClient?.Close();
        }
        catch { }

        if (listenThread != null && listenThread.IsAlive)
        {
            listenThread.Join(100);
        }
    }

    void OnApplicationQuit()
    {
        OnDestroy();
    }
}
