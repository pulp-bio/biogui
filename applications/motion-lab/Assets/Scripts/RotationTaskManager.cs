// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMPro;
using UnityEngine;

/// <summary>
/// Manages rotation task with simple timing export.
/// </summary>
public class RotationTaskManager : MonoBehaviour
{
    [Header("UI")]
    public TextMeshProUGUI taskInfoText;
    public TextMeshProUGUI timerText;

    [Header("Task")]
    public RotationTask rotationTask;

    [Header("Export")]
    public string exportFolderPath = "Results";

    private bool hasExported = false;

    void Start()
    {
        if (!rotationTask)
            rotationTask = FindFirstObjectByType<RotationTask>();

        if (!rotationTask)
        {
            Debug.LogError("[RotationTaskManager] No RotationTask found in scene!");
            enabled = false;
        }
    }

    void Update()
    {
        UpdateUI();

        // Export when task is complete
        if (rotationTask.IsComplete && !hasExported)
        {
            ExportResults();
            hasExported = true;
        }
    }

    void UpdateUI()
    {
        if (rotationTask.IsComplete)
        {
            // Task is complete - show completion message and total time
            if (taskInfoText)
            {
                taskInfoText.text = "Complete!";
            }

            if (timerText)
            {
                float totalDuration = rotationTask.GetTotalTaskDuration();
                timerText.text = FormatTime(totalDuration);
            }
            return;
        }

        // Task in progress - show simplified instructions
        if (taskInfoText)
        {
            string repInfo =
                $"Repetition {rotationTask.CurrentRepetition + 1} of {rotationTask.TotalRepetitions}";
            string instruction = GetSimplifiedInstruction();
            taskInfoText.text = $"{repInfo}\n{instruction}";
        }

        // Timer (current repetition time)
        if (timerText)
        {
            float duration = rotationTask.GetCurrentRepetitionDuration();
            timerText.text = FormatTime(duration);
        }
    }

    string GetSimplifiedInstruction()
    {
        RotationTask.TaskState state = rotationTask.GetCurrentState();
        float target = rotationTask.targetSupinationAngle;
        float current = rotationTask.CurrentRelativeAngle;

        switch (state)
        {
            case RotationTask.TaskState.WaitingForGrabAtNeutral:
                return "Close hand";

            case RotationTask.TaskState.WaitingForReleaseAtNeutral:
                return "Open hand";

            case RotationTask.TaskState.RotatingToSupination:
                return $"Supinate to {target:F0}° ({current:F0}°)";

            case RotationTask.TaskState.WaitingForGrabAtSupination:
                return "Close hand";

            case RotationTask.TaskState.WaitingForReleaseAtSupination:
                return "Open hand";

            case RotationTask.TaskState.RotatingToNeutral:
                return "Rotate back to neutral";

            default:
                return "";
        }
    }

    string FormatTime(float seconds)
    {
        int m = (int)(seconds / 60f);
        int s = (int)(seconds % 60f);
        int cs = (int)((seconds % 1f) * 100f);
        return $"{m:00}:{s:00}.{cs:00}";
    }

    void ExportResults()
    {
        try
        {
            string dir = Path.Combine(Application.dataPath, "..", exportFolderPath);
            if (!Directory.Exists(dir))
                Directory.CreateDirectory(dir);

            string timestamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
            string fileName = $"rotation_task_{timestamp}.csv";
            string filePath = Path.Combine(dir, fileName);

            float totalTaskDuration = rotationTask.GetTotalTaskDuration();
            var timings = rotationTask.GetRepetitionTimings();

            using (var writer = new StreamWriter(filePath, false, Encoding.UTF8))
            {
                // Simple CSV Header
                writer.WriteLine("Repetition,Duration_s");

                // Write each repetition (one line per rep)
                foreach (var rep in timings)
                {
                    writer.WriteLine($"{rep.repetitionNumber},{rep.duration:F3}");
                }
            }

            Debug.Log($"✅ RotationTask results exported to: {Path.GetFullPath(filePath)}");
        }
        catch (Exception e)
        {
            Debug.LogError($"RotationTask export failed: {e.Message}");
        }
    }
}
