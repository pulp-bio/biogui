using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using TMPro;
using UnityEngine;

/// <summary>
/// Manages BoxTask sequence and timing.
/// </summary>
public class BoxTaskManager : MonoBehaviour
{
    [Header("UI")]
    public TextMeshProUGUI taskInfoText;
    public TextMeshProUGUI timerText;

    private List<BoxTask> sequence = new List<BoxTask>();
    private BoxTask currentTask;
    private bool allComplete;
    private float sessionStartTime;
    private float finalTotalTime = -1f;

    public static BoxTaskManager Instance { get; private set; }

    void Awake()
    {
        if (Instance == null)
            Instance = this;
        else
            Destroy(gameObject);
    }

    void Start()
    {
        sessionStartTime = Time.time;

        sequence = FindObjectsByType<BoxTask>(FindObjectsSortMode.None)
            .OrderBy(t => t.orderIndex)
            .ThenBy(t => t.gameObject.name)
            .ToList();

        UpdateCurrentTask();
        UpdateUI();
    }

    void Update()
    {
        if (!allComplete)
        {
            UpdateCurrentTask();
            if (sequence.All(t => t.isComplete))
            {
                allComplete = true;
                finalTotalTime = Time.time - sessionStartTime;
                ExportResults();
            }
        }

        UpdateUI();
    }

    void UpdateCurrentTask()
    {
        currentTask = sequence.FirstOrDefault(t => !t.isComplete);
    }

    // Fixed order of tasks/boxes
    public bool AllowStart(BoxTask task) => currentTask != null && task == currentTask;

    public void ShowWrongBoxHint()
    {
        if (!taskInfoText)
            return;

        if (currentTask == null)
        {
            taskInfoText.text = "All tasks complete!";
            return;
        }

        taskInfoText.text = $"Wrong box! Grab Box {currentTask.orderIndex}";
    }

    void UpdateUI()
    {
        UpdateTaskInfoText();
        UpdateTimerText();
    }

    void UpdateTaskInfoText()
    {
        if (!taskInfoText)
            return;

        if (allComplete)
        {
            taskInfoText.text = $"All tasks completed!";
            return;
        }

        if (currentTask == null)
        {
            taskInfoText.text = "Grab Box 1 to begin";
            return;
        }

        // Check if box is currently held
        var grabbable = currentTask.GetComponent<Grabbable>();
        bool isHeld = grabbable != null && grabbable.IsHeld;

        // Live angle display for rotation tasks
        string angleDisplay = "";
        if (
            currentTask.taskType == TaskType.SupinationRotation
            || currentTask.taskType == TaskType.FlexionExtensionRotation
        )
        {
            var rt = currentTask.GetComponent<RotationTracker>();

            if (rt != null && isHeld)
            {
                int ang = Mathf.RoundToInt(rt.CurrentAngleDeg);
                angleDisplay = $" ({ang}°)";
            }
        }

        string progress = currentTask.GetProgressText(isHeld);
        taskInfoText.text = $"Box {currentTask.orderIndex}: {progress}{angleDisplay}";
    }

    void UpdateTimerText()
    {
        if (!timerText)
            return;

        if (allComplete)
        {
            timerText.text = FormatTime(finalTotalTime);
            return;
        }

        if (currentTask != null && currentTask.startTime >= 0 && !currentTask.isComplete)
            timerText.text = FormatTime(currentTask.GetDuration());
        else
            timerText.text = "00:00.00";
    }

    string FormatTime(float t)
    {
        int m = (int)(t / 60f);
        int s = (int)(t % 60f);
        int cs = (int)((t % 1f) * 100f);
        return $"{m:00}:{s:00}.{cs:00}";
    }

    void ExportResults()
    {
        try
        {
            // Target folder (relative to project)
            string dir = Path.Combine(Application.dataPath, "..", "Results");
            if (!Directory.Exists(dir))
                Directory.CreateDirectory(dir);

            // Timestamp for CSV filename
            string stamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
            string fileName = $"box_task_{stamp}.csv";
            string filePath = Path.Combine(dir, fileName);

            using (var sw = new StreamWriter(filePath, false, Encoding.UTF8))
            {
                // CSV header
                sw.WriteLine(
                    "Timestamp,Seq,BoxName,OrderIndex,TaskType,Description,Duration,Start,End"
                );

                string now = DateTime.Now.ToString("yyyy-MM-dd_HH:mm:ss");

                for (int i = 0; i < sequence.Count; i++)
                {
                    var t = sequence[i];
                    sw.WriteLine(
                        $"{now},{i + 1},{t.gameObject.name},{t.orderIndex},{t.taskType},"
                            + $"\"{t.GetTaskDescription()}\",{t.GetDuration():F3},"
                            + $"{t.startTime:F3},{t.endTime:F3}"
                    );
                }
            }

            Debug.Log($"✅ BoxTask results exported to: {Path.GetFullPath(filePath)}");
        }
        catch (Exception e)
        {
            Debug.LogError($"BoxTask export failed: {e.Message}");
        }
    }
}
