// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

/// <summary>
/// Manages continuous task execution with configurable task selection and CSV logging.
/// </summary>
public class ContinuousTaskManager : MonoBehaviour
{
    [Header("Position Control")]
    [Tooltip(
        "Position mode for all continuous tasks: Delta for incremental movement, State for discrete positions (start/forward/right)"
    )]
    public PositionMode positionMode = PositionMode.State;

    [Header("Task Selection")]
    [Tooltip("If enabled, tasks are selected randomly. If disabled, tasks run in order.")]
    public bool randomSelection = false;

    [Header("Active Tasks")]
    [Tooltip("Enable/disable specific tasks. Only enabled tasks will be available.")]
    public bool enableBoxDeliveryTask = true;
    public bool enableCylinderDeliveryTask = false;
    public bool enableBottlePouringTask = false;
    public bool enableMarbleDeliveryTask = false;

    [Header("Task References")]
    public BoxDeliveryTask boxDeliveryTask;
    public CylinderDeliveryTask cylinderDeliveryTask;
    public BottlePouringTask bottlePouringTask;
    public MarbleDeliveryTask marbleDeliveryTask;

    [Header("Delivery Zone")]
    public DeliveryZone deliveryZone;
    public GameObject deliveryZonePrefab; // Prefab to spawn if deliveryZone is null

    [Header("Hand References")]
    public HandController handController;
    public HandGrabber handGrabber;

    [Header("UI (Optional)")]
    public TMPro.TextMeshProUGUI taskInfoText;
    public TMPro.TextMeshProUGUI timerText;

    [Header("Task Timing")]
    [Tooltip("Countdown time in seconds before each task starts")]
    public float preTaskCountdown = 10.0f;

    [Tooltip("Maximum time in seconds allowed for task completion (0 = no timeout)")]
    public float taskTimeout = 60.0f;

    [Header("Hand Reset")]
    [Tooltip("Hand position to reset to at the beginning of each task (during countdown)")]
    public Vector3 handStartPosition = new Vector3(0f, 0.5f, -4f);

    [Header("Task Completion")]
    [Tooltip("Delay in seconds before switching to the next task after completion")]
    public float taskCompletionDelay = 2.0f;

    private List<ContinuousTask> activeTasks = new List<ContinuousTask>();
    private ContinuousTask currentTask;
    private int currentTaskIndex = 0;
    private int taskCounter = 0;
    private float sessionStartTime;
    private List<TaskResult> taskResults = new List<TaskResult>();
    private HashSet<int> exportedTaskNumbers = new HashSet<int>(); // Track which tasks have been exported
    private bool isRunning = false;
    private bool isWaitingForNextTask = false; // Flag to prevent multiple task switches
    private string sessionCsvFilePath; // Path to CSV file for this session

    // Countdown and timeout tracking
    private bool isInCountdown = false;
    private float countdownStartTime = -1f;
    private float taskStartTime = -1f;
    private bool hasTimedOut = false;

    public static ContinuousTaskManager Instance { get; private set; }

    [Serializable]
    public class TaskResult
    {
        public int taskNumber;
        public string taskType;
        public float startTime;
        public float endTime;
        public float duration;
        public bool success;
        public bool timedOut;
        public string timestamp;
    }

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
        isRunning = false;

        // Initialize CSV file for this session
        InitializeCsvFile();

        // Find HandController if not assigned
        if (handController == null)
        {
            handController = FindFirstObjectByType<HandController>();
        }

        // Set position mode on HandController
        if (handController != null)
        {
            handController.currentPositionMode = positionMode;
            Debug.Log(
                $"[ContinuousTaskManager] Set HandController position mode to: {positionMode}"
            );
        }

        // Setup delivery zone if needed
        if (deliveryZone == null && deliveryZonePrefab != null)
        {
            GameObject zoneObj = Instantiate(deliveryZonePrefab);
            deliveryZone = zoneObj.GetComponent<DeliveryZone>();
            if (deliveryZone == null)
            {
                Debug.LogError(
                    "[ContinuousTaskManager] DeliveryZone prefab missing DeliveryZone component!"
                );
            }
            else
            {
                Debug.Log("[ContinuousTaskManager] Spawned delivery zone from prefab");
            }
        }

        // Fallback: Try to find delivery zone in scene if not assigned
        if (deliveryZone == null)
        {
            deliveryZone = FindFirstObjectByType<DeliveryZone>();
            if (deliveryZone != null)
            {
                Debug.Log("[ContinuousTaskManager] Found delivery zone in scene");
            }
            else
            {
                Debug.LogWarning(
                    "[ContinuousTaskManager] No delivery zone found! Please assign deliveryZone or deliveryZonePrefab in the inspector."
                );
            }
        }

        // Assign delivery zone to tasks
        if (deliveryZone != null)
        {
            if (boxDeliveryTask != null)
            {
                boxDeliveryTask.deliveryZone = deliveryZone;
                Debug.Log("[ContinuousTaskManager] Assigned delivery zone to BoxDeliveryTask");
            }
            if (cylinderDeliveryTask != null)
            {
                cylinderDeliveryTask.deliveryZone = deliveryZone;
                Debug.Log("[ContinuousTaskManager] Assigned delivery zone to CylinderDeliveryTask");
            }
            if (marbleDeliveryTask != null)
            {
                marbleDeliveryTask.deliveryZone = deliveryZone;
                Debug.Log("[ContinuousTaskManager] Assigned delivery zone to MarbleDeliveryTask");
            }
        }
        else
        {
            Debug.LogError(
                "[ContinuousTaskManager] Cannot assign delivery zone to tasks - deliveryZone is null!"
            );
        }

        // Build active tasks list based on enabled flags
        BuildActiveTasksList();

        // Prepare first task immediately (show objects, start countdown)
        if (activeTasks.Count > 0)
        {
            currentTask = activeTasks[0];
            // Set index to -1 so that when SelectNextTask() is called, it will first increment to 0,
            // then select the next task (index 1) instead of selecting the same task (index 0) again
            currentTaskIndex = -1;
            if (currentTask != null)
            {
                currentTask.gameObject.SetActive(true);
                currentTask.PrepareTask(); // Show objects, but don't start timing

                // Start countdown and reset hand (freeze input to prevent movement during countdown)
                isInCountdown = true;
                countdownStartTime = Time.time;
                StartCoroutine(ResetHandAndFreezeInput());

                Debug.Log(
                    $"[ContinuousTaskManager] Prepared task: {currentTask.taskName} - starting {preTaskCountdown}s countdown"
                );
            }
        }
        else
        {
            // Hide all tasks if none are active
            foreach (var task in GetAllTasks())
            {
                if (task != null)
                {
                    task.gameObject.SetActive(false);
                    task.ResetTask();
                }
            }
        }
    }

    IEnumerator DelayedSelectNextTask()
    {
        Debug.Log(
            $"[ContinuousTaskManager] Task completed! Waiting {taskCompletionDelay}s before next task..."
        );

        // Wait for the specified delay
        yield return new WaitForSeconds(taskCompletionDelay);

        // Select next task
        SelectNextTask();
        isWaitingForNextTask = false;
    }

    void OnDestroy()
    {
        ExportResults();
    }

    void BuildActiveTasksList()
    {
        activeTasks.Clear();

        if (enableBoxDeliveryTask && boxDeliveryTask != null)
        {
            activeTasks.Add(boxDeliveryTask);
            Debug.Log("[ContinuousTaskManager] Box Delivery task enabled");
        }

        if (enableCylinderDeliveryTask && cylinderDeliveryTask != null)
        {
            activeTasks.Add(cylinderDeliveryTask);
            Debug.Log("[ContinuousTaskManager] Cylinder Delivery task enabled");
        }

        if (enableBottlePouringTask && bottlePouringTask != null)
        {
            activeTasks.Add(bottlePouringTask);
            Debug.Log("[ContinuousTaskManager] Bottle Pouring task enabled");
        }

        if (enableMarbleDeliveryTask && marbleDeliveryTask != null)
        {
            activeTasks.Add(marbleDeliveryTask);
            Debug.Log("[ContinuousTaskManager] Marble Delivery task enabled");
        }

        Debug.Log($"[ContinuousTaskManager] Built active tasks list: {activeTasks.Count} tasks");
    }

    List<ContinuousTask> GetAllTasks()
    {
        var allTasks = new List<ContinuousTask>();
        if (boxDeliveryTask != null)
            allTasks.Add(boxDeliveryTask);
        if (cylinderDeliveryTask != null)
            allTasks.Add(cylinderDeliveryTask);
        if (bottlePouringTask != null)
            allTasks.Add(bottlePouringTask);
        if (marbleDeliveryTask != null)
            allTasks.Add(marbleDeliveryTask);
        return allTasks;
    }

    void Update()
    {
        // Update UI even if no task is selected (to show status messages)
        UpdateUI();

        if (currentTask == null)
            return;

        // Handle pre-task countdown
        if (isInCountdown && !isRunning)
        {
            float elapsed = Time.time - countdownStartTime;
            float remaining = preTaskCountdown - elapsed;

            if (remaining <= 0)
            {
                // Countdown finished - activate objects and start the task
                isInCountdown = false;
                currentTask.ActivateTask(); // Make objects grabbable
                currentTask.StartTiming(); // Start timing
                taskStartTime = Time.time;
                isRunning = true;
                hasTimedOut = false;

                // Re-enable hand input
                EnableHandInput();

                Debug.Log($"[ContinuousTaskManager] Countdown finished - task activated and started!");
            }
            return;
        }

        // Check for task timeout
        if (isRunning && !currentTask.isComplete && taskTimeout > 0)
        {
            float taskElapsed = Time.time - taskStartTime;
            if (taskElapsed >= taskTimeout)
            {
                // Task timed out
                hasTimedOut = true;
                currentTask.endTime = Time.time;
                currentTask.isComplete = true;
                Debug.Log($"[ContinuousTaskManager] Task {taskCounter} timed out after {taskTimeout}s");

                // Log result with timeout status
                TaskResult result = LogTaskResult(currentTask, true);
                if (result != null && !exportedTaskNumbers.Contains(result.taskNumber))
                {
                    AppendTaskResultToCsv(result);
                    exportedTaskNumbers.Add(result.taskNumber);
                }

                // Wait before selecting next task
                isWaitingForNextTask = true;
                StartCoroutine(DelayedSelectNextTask());
            }
        }

        // Handle task completion
        if (currentTask.isComplete && !isWaitingForNextTask)
        {
            // Task completed - log result (only if timing was started)
            if (currentTask.startTime >= 0 && !hasTimedOut)
            {
                TaskResult result = LogTaskResult(currentTask, false);
                // Export single task result to CSV immediately (only if not already exported)
                if (result != null && !exportedTaskNumbers.Contains(result.taskNumber))
                {
                    AppendTaskResultToCsv(result);
                    exportedTaskNumbers.Add(result.taskNumber);
                }
            }

            // Wait before selecting next task
            isWaitingForNextTask = true;
            StartCoroutine(DelayedSelectNextTask());
        }
    }

    /// <summary>
    /// Start the task system. Call this manually if autoStart is disabled.
    /// </summary>
    public void StartTask()
    {
        if (activeTasks.Count == 0)
        {
            Debug.LogWarning("[ContinuousTaskManager] No active tasks! Enable at least one task.");
            return;
        }

        // Ensure hand input is enabled before starting
        EnableHandInput();
        isRunning = true;
        currentTaskIndex = 0;
        SelectNextTask();
    }

    /// <summary>
    /// Stop the task system.
    /// </summary>
    public void StopTask()
    {
        isRunning = false;
        isInCountdown = false;

        // Re-enable hand input when stopping
        EnableHandInput();

        if (currentTask != null)
        {
            currentTask.gameObject.SetActive(false);
            currentTask.ResetTask();
        }
        currentTask = null;
        UpdateUI();
    }

    void SelectNextTask()
    {
        // Hide current task
        if (currentTask != null)
        {
            currentTask.gameObject.SetActive(false);
            currentTask.ResetTask();
        }

        if (activeTasks.Count == 0)
        {
            Debug.LogWarning("[ContinuousTaskManager] No active tasks available!");
            currentTask = null;
            isRunning = false;
            isInCountdown = false;
            return;
        }

        // Select task based on mode
        if (randomSelection)
        {
            // Random selection (upper bound is exclusive)
            int randomIndex = UnityEngine.Random.Range(0, activeTasks.Count);
            currentTask = activeTasks[randomIndex];
            currentTaskIndex = randomIndex;
        }
        else
        {
            // Sequential selection: increment index first, then select task
            // This ensures we don't select the same task twice in a row
            // If currentTaskIndex is -1 (initial state), we want to select index 1 (next task)
            // Otherwise, increment normally
            if (currentTaskIndex == -1)
            {
                currentTaskIndex = activeTasks.Count > 1 ? 1 : 0;
            }
            else
            {
                currentTaskIndex = (currentTaskIndex + 1) % activeTasks.Count;
            }
            currentTask = activeTasks[currentTaskIndex];
        }

        taskCounter++;

        // Show and prepare new task
        if (currentTask != null)
        {
            currentTask.gameObject.SetActive(true);
            currentTask.PrepareTask(); // Show objects, but don't start timing yet

            // Reset timing state
            isRunning = false;
            hasTimedOut = false;

            // Start countdown and reset hand (freeze input to prevent movement during countdown)
            isInCountdown = true;
            countdownStartTime = Time.time;
            StartCoroutine(ResetHandAndFreezeInput());

            Debug.Log(
                $"[ContinuousTaskManager] Selected task {taskCounter}: {currentTask.taskName} - starting {preTaskCountdown}s countdown ({(randomSelection ? "random" : "sequential")})"
            );
        }
    }

    /// <summary>
    /// Reset hand to start position (instant teleport) and freeze input.
    /// Uses freeze mechanism instead of disabling controller to prevent hand from
    /// getting stuck mid-movement when new messages arrive during reset.
    /// </summary>
    IEnumerator ResetHandAndFreezeInput()
    {
        // First, freeze input to prevent any incoming messages from affecting the hand
        if (handController != null)
        {
            handController.FreezeInput();
        }

        // Wait one frame for any in-flight Update() to complete
        yield return null;

        // Reset hand to start position (instant teleport)
        if (handController != null)
        {
            handController.ResetToStartPosition(handStartPosition);
        }

        // Wait a few frames for Update() to apply curl values through normal ApplyFingers() cycle
        // The hand stays frozen during this time, so no new messages can override the reset
        yield return null;
        yield return null;
        yield return null;

        // Disable hand grabber during countdown (but keep controller enabled for rendering)
        if (handGrabber != null)
        {
            handGrabber.enabled = false;
        }

        Debug.Log("[ContinuousTaskManager] Hand reset complete and input FROZEN during countdown");
    }

    /// <summary>
    /// Unfreeze hand input after countdown finishes.
    /// Uses freeze mechanism to allow smooth transition without getting stuck mid-movement.
    /// </summary>
    void EnableHandInput()
    {
        if (handController != null)
        {
            handController.UnfreezeInput();
            Debug.Log("[ContinuousTaskManager] Hand input UNFROZEN - task started");
        }

        if (handGrabber != null)
        {
            handGrabber.enabled = true;
        }
    }

    TaskResult LogTaskResult(ContinuousTask task, bool timedOut)
    {
        var result = new TaskResult
        {
            taskNumber = taskCounter,
            taskType = task.taskType.ToString(),
            startTime = task.startTime - sessionStartTime,
            endTime = task.endTime - sessionStartTime,
            duration = task.GetDuration(),
            success = !timedOut, // Success only if not timed out
            timedOut = timedOut,
            timestamp = DateTime.Now.ToString("yyyy-MM-dd_HH:mm:ss"),
        };

        taskResults.Add(result);
        return result;
    }

    void UpdateUI()
    {
        if (taskInfoText != null)
        {
            if (currentTask == null)
            {
                if (activeTasks.Count == 0)
                {
                    taskInfoText.text =
                        "No tasks enabled\nEnable at least one task in ContinuousTaskManager";
                }
                else
                {
                    taskInfoText.text = "No task selected\nWaiting for task selection...";
                }
            }
            else
            {
                string statusText = "";

                // Show countdown if in countdown phase
                if (isInCountdown)
                {
                    float elapsed = Time.time - countdownStartTime;
                    float remaining = preTaskCountdown - elapsed;
                    statusText = $"Get ready...\nStarting in {Mathf.Ceil(remaining)}s";
                }
                // Show timeout message if timed out
                else if (hasTimedOut)
                {
                    statusText = "Timed out!";
                }
                // Get task-specific status if available
                else if (currentTask is BoxDeliveryTask boxTask)
                {
                    statusText = boxTask.GetStatusText();
                }
                else if (currentTask is CylinderDeliveryTask cylinderTask)
                {
                    statusText = cylinderTask.GetStatusText();
                }
                else if (currentTask is BottlePouringTask bottleTask)
                {
                    statusText = bottleTask.GetStatusText();
                }
                else if (currentTask is MarbleDeliveryTask marbleTask)
                {
                    statusText = marbleTask.GetStatusText();
                }
                else if (currentTask.isComplete)
                {
                    statusText = "Complete!";
                }
                else if (currentTask.startTime >= 0)
                {
                    statusText = "In Progress";
                }
                else
                {
                    statusText = "Get ready...";
                }

                taskInfoText.text = $"{currentTask.taskName}\n{statusText}";
            }
        }

        if (timerText != null)
        {
            // Show task timer (not countdown - countdown is only in task info)
            if (currentTask != null && currentTask.IsActive())
            {
                float elapsed = currentTask.GetDuration();
                timerText.text = FormatTime(elapsed);
            }
            else
            {
                // During countdown or when no task is running, show 00:00.00
                timerText.text = "00:00.00";
            }
        }
    }

    string FormatTime(float t)
    {
        int minutes = Mathf.FloorToInt(t / 60);
        int seconds = Mathf.FloorToInt(t % 60);
        int hundredths = Mathf.FloorToInt((t * 100) % 100);
        return string.Format("{0:00}:{1:00}.{2:00}", minutes, seconds, hundredths);
    }

    void OnApplicationQuit()
    {
        ExportResults();
    }

    void InitializeCsvFile()
    {
        try
        {
            // Target folder (relative to project)
            string dir = Path.Combine(Application.dataPath, "..", "Results");
            if (!Directory.Exists(dir))
                Directory.CreateDirectory(dir);

            // Timestamp for CSV filename (one file per Unity session)
            string stamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
            string fileName = $"continuous_tasks_{stamp}.csv";
            sessionCsvFilePath = Path.Combine(dir, fileName);

            // Create file with header (added TimedOut column)
            using (var sw = new StreamWriter(sessionCsvFilePath, false, Encoding.UTF8))
            {
                sw.WriteLine("Timestamp,TaskNumber,TaskType,StartTime,EndTime,Duration,Success,TimedOut");
            }

            Debug.Log(
                $"[ContinuousTaskManager] CSV file initialized: {Path.GetFullPath(sessionCsvFilePath)}"
            );
        }
        catch (Exception e)
        {
            Debug.LogError($"ContinuousTask CSV initialization failed: {e.Message}");
        }
    }

    void ExportResults()
    {
        try
        {
            if (taskResults.Count == 0)
            {
                Debug.Log("[ContinuousTaskManager] No task results to export.");
                return;
            }

            if (string.IsNullOrEmpty(sessionCsvFilePath))
            {
                InitializeCsvFile();
            }

            // Append only results that haven't been exported yet
            int newResultsCount = 0;
            using (var sw = new StreamWriter(sessionCsvFilePath, true, Encoding.UTF8))
            {
                foreach (var result in taskResults)
                {
                    // Only write if not already exported
                    if (!exportedTaskNumbers.Contains(result.taskNumber))
                    {
                        sw.WriteLine(
                            $"{result.timestamp},{result.taskNumber},{result.taskType},"
                                + $"{result.startTime:F3},{result.endTime:F3},{result.duration:F3},{result.success},{result.timedOut}"
                        );
                        exportedTaskNumbers.Add(result.taskNumber);
                        newResultsCount++;
                    }
                }
            }

            if (newResultsCount > 0)
            {
                Debug.Log(
                    $"✅ ContinuousTask results exported to: {Path.GetFullPath(sessionCsvFilePath)}"
                );
                Debug.Log(
                    $"   New tasks exported: {newResultsCount}, Total tasks: {taskResults.Count}"
                );
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"ContinuousTask export failed: {e.Message}");
        }
    }

    void AppendTaskResultToCsv(TaskResult result)
    {
        try
        {
            if (string.IsNullOrEmpty(sessionCsvFilePath))
            {
                InitializeCsvFile();
            }

            // Append single result to CSV (added timedOut field)
            using (var sw = new StreamWriter(sessionCsvFilePath, true, Encoding.UTF8))
            {
                sw.WriteLine(
                    $"{result.timestamp},{result.taskNumber},{result.taskType},"
                        + $"{result.startTime:F3},{result.endTime:F3},{result.duration:F3},{result.success},{result.timedOut}"
                );
            }

            string statusMsg = result.timedOut ? "TIMED OUT" : $"Duration: {result.duration:F3}s";
            Debug.Log(
                $"✅ Task {result.taskNumber} ({result.taskType}) exported to CSV. {statusMsg}"
            );
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to append task result to CSV: {e.Message}");
        }
    }

    // ======================
    // Public API for external scripts
    // ======================

    /// <summary>
    /// Manually trigger the next task (useful for testing or manual control).
    /// </summary>
    public void NextTask()
    {
        if (isWaitingForNextTask)
        {
            Debug.LogWarning(
                "[ContinuousTaskManager] Already waiting for next task. Please wait for the current transition to complete."
            );
            return;
        }

        SelectNextTask();
    }

    /// <summary>
    /// Get the current active task (if any).
    /// </summary>
    public ContinuousTask GetCurrentTask()
    {
        return currentTask;
    }

    // ======================
    // Editor/Inspector utilities
    // ======================

    /// <summary>
    /// Refresh the active tasks list. Call this if you change task enable flags at runtime.
    /// </summary>
    public void RefreshActiveTasks()
    {
        BuildActiveTasksList();
        Debug.Log(
            $"[ContinuousTaskManager] Active tasks refreshed: {activeTasks.Count} tasks available"
        );
    }

    void OnValidate()
    {
        // Ensure task counter doesn't go negative
        if (taskCounter < 0)
            taskCounter = 0;

        // Ensure task completion delay is not negative
        if (taskCompletionDelay < 0f)
            taskCompletionDelay = 0f;
    }
}
