// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using System;
using TMPro;
using UnityEngine;

public class TrainingModeManager : MonoBehaviour
{
    [Header("References")]
    public MiddlewareClient middleware;
    public HandController handController;

    [Header("Timing")]
    public float startDelaySeconds = 3f;
    public float segmentDurationSeconds = 5f;
    public float restDurationSeconds = 3f;
    public int repetitionsPerGesture = 10;

    [Header("UI")]
    public TextMeshProUGUI taskInfoText;
    public TextMeshProUGUI timerText;

    [Header("Demo Hand Settings")]
    [Range(0f, 1f)]
    public float demoPoseBlend = 1f;
    public float fadeSpeed = 3f;

    [Header("Debug")]
    public bool debugLogs = false;

    // Phases: Warmup -> Rest -> Fist -> Open -> Rest -> Fist -> Open -> ... -> Completed
    private enum Phase
    {
        Warmup,
        Rest,
        Fist,
        Open,
        Completed,
    }

    private Phase phase;
    private int currentRep; // 0 to repetitionsPerGesture-1
    private float phaseElapsed;
    private float warmupRemaining;

    // For smooth fading
    private float targetCurl = 0f; // 0 = open, 1 = fist
    private float currentCurl = 0f;

    void OnEnable()
    {
        ResetSession();
    }

    void OnDisable()
    {
        if (handController != null)
        {
            handController.ClearDemoPose();
        }
    }

    void Update()
    {
        switch (phase)
        {
            case Phase.Warmup:
                UpdateWarmup();
                break;
            case Phase.Rest:
                UpdateRest();
                break;
            case Phase.Fist:
                UpdateFist();
                break;
            case Phase.Open:
                UpdateOpen();
                break;
            case Phase.Completed:
                break;
        }

        UpdateDemoHandSmooth();
        UpdateUI();
    }

    void ResetSession()
    {
        currentRep = 0;
        phaseElapsed = 0f;
        warmupRemaining = Mathf.Max(0f, startDelaySeconds);
        phase = Phase.Warmup;
        targetCurl = 0f;
        currentCurl = 0f;

        SetStatus("Get ready...\nPrepare your hand");
        if (timerText)
            timerText.text = $"Starts in: {warmupRemaining:0.0}s";
    }

    /// <summary>
    /// Get current Unix timestamp in milliseconds.
    /// </summary>
    private long GetUnixTimestampMs()
    {
        return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
    }

    void UpdateWarmup()
    {
        warmupRemaining -= Time.deltaTime;
        if (warmupRemaining <= 0f)
        {
            StartRest();
        }
    }

    void UpdateRest()
    {
        phaseElapsed += Time.deltaTime;
        if (phaseElapsed >= restDurationSeconds)
        {
            StartFist();
        }
    }

    void UpdateFist()
    {
        phaseElapsed += Time.deltaTime;
        if (phaseElapsed >= segmentDurationSeconds)
        {
            // Fist done, go directly to Open (no rest between)
            StartOpen();
        }
    }

    void UpdateOpen()
    {
        phaseElapsed += Time.deltaTime;
        if (phaseElapsed >= segmentDurationSeconds)
        {
            // Open done, increment rep
            currentRep++;

            if (currentRep >= repetitionsPerGesture)
            {
                FinishTraining();
            }
            else
            {
                // Rest before next fist-open pair
                StartRest();
            }
        }
    }

    void StartRest()
    {
        phase = Phase.Rest;
        phaseElapsed = 0f;
        targetCurl = 0f; // Open hand during rest

        // Send rest gesture with absolute Unix timestamp and duration
        long timestampMs = GetUnixTimestampMs();
        int durationMs = (int)(restDurationSeconds * 1000f);
        middleware?.SendGesture("rest", timestampMs, durationMs);

        if (debugLogs)
            Debug.Log($"[Training] REST ({restDurationSeconds}s) before rep {currentRep + 1}");
    }

    void StartFist()
    {
        phase = Phase.Fist;
        phaseElapsed = 0f;
        targetCurl = 1f; // Fist

        // Send fist gesture with absolute Unix timestamp and duration
        long timestampMs = GetUnixTimestampMs();
        int durationMs = (int)(segmentDurationSeconds * 1000f);
        middleware?.SendGesture("fist", timestampMs, durationMs);

        if (debugLogs)
            Debug.Log($"[Training] FIST rep {currentRep + 1}/{repetitionsPerGesture}");
    }

    void StartOpen()
    {
        phase = Phase.Open;
        phaseElapsed = 0f;
        targetCurl = 0f; // Open

        // Send open gesture with absolute Unix timestamp and duration
        long timestampMs = GetUnixTimestampMs();
        int durationMs = (int)(segmentDurationSeconds * 1000f);
        middleware?.SendGesture("open", timestampMs, durationMs);

        if (debugLogs)
            Debug.Log($"[Training] OPEN rep {currentRep + 1}/{repetitionsPerGesture}");
    }

    void FinishTraining()
    {
        phase = Phase.Completed;
        targetCurl = 0f;

        if (handController != null)
        {
            handController.ClearDemoPose();
        }

        // Send finish signal to trigger training
        middleware?.SendFinishTraining();

        SetStatus("Training Complete!\nModel is being updated...");
        if (timerText)
            timerText.text = $"{repetitionsPerGesture} reps completed";

        if (debugLogs)
            Debug.Log("[Training] Session finished - model training started");
    }

    void UpdateDemoHandSmooth()
    {
        if (phase == Phase.Completed)
        {
            currentCurl = Mathf.Lerp(currentCurl, 0f, Time.deltaTime * fadeSpeed);
            if (handController != null && currentCurl > 0.01f)
            {
                float[] curls = { currentCurl, currentCurl, currentCurl, currentCurl, currentCurl };
                handController.SetDemoPose(curls, demoPoseBlend);
            }
            return;
        }

        // Smoothly interpolate current curl towards target
        currentCurl = Mathf.Lerp(currentCurl, targetCurl, Time.deltaTime * fadeSpeed);

        // Apply to hand
        if (handController != null)
        {
            float[] curls = { currentCurl, currentCurl, currentCurl, currentCurl, currentCurl };
            handController.SetDemoPose(curls, demoPoseBlend);
        }
    }

    void UpdateUI()
    {
        if (phase == Phase.Warmup)
        {
            SetStatus("Get Ready...\nTraining will begin shortly");
            if (timerText)
                timerText.text = $"Starts in: {Mathf.Max(0f, warmupRemaining):0.0}s";
            return;
        }

        if (phase == Phase.Rest)
        {
            SetStatus($"REST\nRelax - next: FIST (rep {currentRep + 1}/{repetitionsPerGesture})");
            float remain = Mathf.Max(0f, restDurationSeconds - phaseElapsed);
            if (timerText)
                timerText.text = $"Rest: {remain:0.0}s";
            return;
        }

        if (phase == Phase.Fist)
        {
            SetStatus($"FIST\nHold fist ({currentRep + 1}/{repetitionsPerGesture})");
            float remain = Mathf.Max(0f, segmentDurationSeconds - phaseElapsed);
            if (timerText)
                timerText.text = $"Hold: {remain:0.0}s";
            return;
        }

        if (phase == Phase.Open)
        {
            SetStatus($"OPEN\nHold open ({currentRep + 1}/{repetitionsPerGesture})");
            float remain = Mathf.Max(0f, segmentDurationSeconds - phaseElapsed);
            if (timerText)
                timerText.text = $"Hold: {remain:0.0}s";
            return;
        }

        // Completed - already handled in FinishTraining
    }

    void SetStatus(string s)
    {
        if (taskInfoText)
            taskInfoText.text = s;
    }

    // Public API

    public void StartTraining()
    {
        ResetSession();
    }

    public void StopTraining()
    {
        phase = Phase.Completed;
        if (handController != null)
        {
            handController.ClearDemoPose();
        }
        SetStatus("Training Stopped");
    }

    public bool IsTraining => phase != Phase.Completed;
    public float Progress =>
        repetitionsPerGesture > 0 ? (float)currentRep / repetitionsPerGesture : 0f;
}
