// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Resolves the Grabbable physics layer for task objects and HandGrabber detection.
/// </summary>
public static class GrabbableLayerHelper
{
    /// <summary>Layer index used in ContinuousTasksScene HandGrabber (m_Bits: 256).</summary>
    public const int DefaultGrabbableLayerIndex = 8;

    public static int GrabbableLayer
    {
        get
        {
            int named = LayerMask.NameToLayer("Grabbable");
            return named >= 0 ? named : DefaultGrabbableLayerIndex;
        }
    }

    public static void ApplyToObject(GameObject obj)
    {
        if (obj == null)
            return;

        int layer = GrabbableLayer;
        SetLayerRecursively(obj.transform, layer);
    }

    static void SetLayerRecursively(Transform root, int layer)
    {
        root.gameObject.layer = layer;
        foreach (Transform child in root)
            SetLayerRecursively(child, layer);
    }
}
