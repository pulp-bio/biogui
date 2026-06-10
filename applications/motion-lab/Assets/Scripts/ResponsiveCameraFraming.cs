// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Keeps the main scene framing usable across wide fullscreen and narrow splitscreen layouts.
/// Attach to the camera and tune the "narrow" values while Unity is docked to half-screen.
/// </summary>
[ExecuteAlways]
[RequireComponent(typeof(Camera))]
public class ResponsiveCameraFraming : MonoBehaviour
{
    [Header("Aspect Targets")]
    [Tooltip("Aspect ratio where the reference framing should be used (e.g. fullscreen 16:9)")]
    public float referenceAspect = 16f / 9f;

    [Tooltip("Aspect ratio where the narrow framing should be fully applied (e.g. half-screen window)")]
    public float narrowAspect = 1.0f;

    [Header("Reference Framing")]
    [Tooltip("Camera local position used for the reference/fullscreen framing")]
    public Vector3 referenceLocalPosition = new Vector3(0f, 4f, -6f);

    [Tooltip("Perspective FOV used for the reference/fullscreen framing")]
    public float referenceFieldOfView = 60f;

    [Tooltip("Orthographic size used for the reference/fullscreen framing")]
    public float referenceOrthographicSize = 5f;

    [Header("Narrow Framing")]
    [Tooltip("Camera local position used for narrow/splitscreen framing")]
    public Vector3 narrowLocalPosition = new Vector3(0f, 4.6f, -7.4f);

    [Tooltip("Perspective FOV used for narrow/splitscreen framing")]
    public float narrowFieldOfView = 70f;

    [Tooltip("Orthographic size used for narrow/splitscreen framing")]
    public float narrowOrthographicSize = 6f;

    [Header("Tools")]
    [Tooltip("Use the camera's current transform/FOV as the reference framing")]
    public bool captureCurrentAsReference;

    [Tooltip("Use the camera's current transform/FOV as the narrow framing")]
    public bool captureCurrentAsNarrow;

    Camera cachedCamera;

    void Awake()
    {
        cachedCamera = GetComponent<Camera>();
        ApplyFraming();
    }

    void OnEnable()
    {
        cachedCamera = GetComponent<Camera>();
        ApplyFraming();
    }

    void Update()
    {
        ApplyFraming();
    }

    void OnValidate()
    {
        cachedCamera = GetComponent<Camera>();

        if (captureCurrentAsReference)
        {
            CaptureCurrentFraming(asReference: true);
            captureCurrentAsReference = false;
        }

        if (captureCurrentAsNarrow)
        {
            CaptureCurrentFraming(asReference: false);
            captureCurrentAsNarrow = false;
        }

        referenceAspect = Mathf.Max(0.2f, referenceAspect);
        narrowAspect = Mathf.Clamp(narrowAspect, 0.2f, referenceAspect);
        ApplyFraming();
    }

    void CaptureCurrentFraming(bool asReference)
    {
        if (cachedCamera == null)
            return;

        if (asReference)
        {
            referenceLocalPosition = transform.localPosition;
            if (cachedCamera.orthographic)
                referenceOrthographicSize = cachedCamera.orthographicSize;
            else
                referenceFieldOfView = cachedCamera.fieldOfView;
        }
        else
        {
            narrowLocalPosition = transform.localPosition;
            if (cachedCamera.orthographic)
                narrowOrthographicSize = cachedCamera.orthographicSize;
            else
                narrowFieldOfView = cachedCamera.fieldOfView;
        }
    }

    void ApplyFraming()
    {
        if (cachedCamera == null)
            return;

        float aspect = cachedCamera.aspect;
        float t;

        if (aspect >= referenceAspect)
        {
            t = 0f;
        }
        else if (aspect <= narrowAspect)
        {
            t = 1f;
        }
        else
        {
            t = (referenceAspect - aspect) / (referenceAspect - narrowAspect);
        }

        transform.localPosition = Vector3.Lerp(referenceLocalPosition, narrowLocalPosition, t);

        if (cachedCamera.orthographic)
        {
            cachedCamera.orthographicSize = Mathf.Lerp(
                referenceOrthographicSize,
                narrowOrthographicSize,
                t
            );
        }
        else
        {
            cachedCamera.fieldOfView = Mathf.Lerp(referenceFieldOfView, narrowFieldOfView, t);
        }
    }
}
