using UnityEngine;

/// <summary>
/// Controls liquid fill level.
/// fillAmount 1.0 = 100% full and visible
/// fillAmount 0.0 = 0% empty and invisible
/// Visual ALWAYS matches percentage.
/// </summary>
[RequireComponent(typeof(Renderer))]
[RequireComponent(typeof(MeshFilter))]
public class LiquidWobble : MonoBehaviour
{
    [Header("Fill Settings")]
    [Range(0f, 1f)]
    public float fillAmount = 1f;

    [Header("Pouring Settings")]
    [Tooltip("Minimum angle to start pouring (degrees from upright). 90 = horizontal.")]
    public float pourAngle = 90f;
    public float pourSpeed = 0.5f;

    [Tooltip(
        "If true, only pours when enabled externally (e.g., by BottlePouringTask). If false, pours based on tilt angle."
    )]
    public bool requireExternalPouring = false;

    [Header("References")]
    public Transform containerTransform;

    private Material mat;
    private float initialFillAmount;
    private bool externalPouringEnabled = false; // Set externally by BottlePouringTask
    private float externalPourRate = 0f; // Set externally - 0 to 1 pour speed multiplier

    private static readonly int FillAmountID = Shader.PropertyToID("_FillAmount");
    private static readonly int MinYID = Shader.PropertyToID("_MinY");
    private static readonly int MaxYID = Shader.PropertyToID("_MaxY");

    void Awake()
    {
        Renderer rend = GetComponent<Renderer>();
        mat = rend.material;

        if (containerTransform == null)
            containerTransform = transform.parent;

        initialFillAmount = fillAmount;

        // Get ACTUAL mesh bounds and send to shader
        MeshFilter mf = GetComponent<MeshFilter>();
        if (mf != null && mf.sharedMesh != null)
        {
            Bounds bounds = mf.sharedMesh.bounds;
            mat.SetFloat(MinYID, bounds.min.y);
            mat.SetFloat(MaxYID, bounds.max.y);
            Debug.Log($"[LiquidWobble] Mesh Y bounds: {bounds.min.y:F4} to {bounds.max.y:F4}");
        }

        mat.SetFloat(FillAmountID, fillAmount);
    }

    void Update()
    {
        if (mat == null || containerTransform == null)
            return;

        // Pour when tilted (and external pouring is enabled if required)
        if (fillAmount > 0)
        {
            bool canPour = !requireExternalPouring || externalPouringEnabled;

            if (canPour)
            {
                float pourRate;

                if (requireExternalPouring && externalPouringEnabled)
                {
                    // Use external pour rate (based on hand rotation, not tilt)
                    pourRate = externalPourRate;
                }
                else
                {
                    // Use tilt-based pour rate
                    float tiltAngle = Vector3.Angle(containerTransform.up, Vector3.up);
                    if (tiltAngle > pourAngle)
                    {
                        pourRate = (tiltAngle - pourAngle) / (180f - pourAngle);
                    }
                    else
                    {
                        pourRate = 0f;
                    }
                }

                if (pourRate > 0f)
                {
                    fillAmount = Mathf.Max(0f, fillAmount - pourRate * pourSpeed * Time.deltaTime);
                }
            }
        }

        mat.SetFloat(FillAmountID, fillAmount);
    }

    public float GetFillAmount() => fillAmount;

    public void SetFillAmount(float amount) => fillAmount = Mathf.Clamp01(amount);

    public void ResetFill() => fillAmount = initialFillAmount;

    public void SetPouringEnabled(bool enabled) => externalPouringEnabled = enabled;

    public void SetPourRate(float rate) => externalPourRate = Mathf.Clamp01(rate);

    void OnDestroy()
    {
        if (mat != null)
            Destroy(mat);
    }
}
