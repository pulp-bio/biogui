using UnityEngine;

public enum AppMode
{
    BoxTasks,
    LiveTraining,
    RotationTask,
}

public class AppModeSwitcher : MonoBehaviour
{
    [Header("Mode")]
    public AppMode mode = AppMode.BoxTasks;

    [Header("References")]
    public BoxTaskManager boxTaskManager;
    public TrainingModeManager trainingModeManager;
    public RotationTaskManager rotationTaskManager;

    void OnEnable()
    {
        ApplyMode();
    }

    void OnValidate()
    {
        ApplyMode();
    }

    public void ApplyMode()
    {
        if (boxTaskManager)
            boxTaskManager.gameObject.SetActive(mode == AppMode.BoxTasks);

        if (trainingModeManager)
            trainingModeManager.gameObject.SetActive(mode == AppMode.LiveTraining);

        if (rotationTaskManager)
            rotationTaskManager.gameObject.SetActive(mode == AppMode.RotationTask);
    }
}
