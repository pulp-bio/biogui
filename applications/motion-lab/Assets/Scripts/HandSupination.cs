// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Shared forearm supination reading (IMU rotation[2] from BioBridge, in degrees).
/// Positive values = supination, 0 = neutral.
/// </summary>
public static class HandSupination
{
    public static float GetDegrees(HandController hand)
    {
        if (hand == null)
            return 0f;

        return hand.CurrentImuSupinationDegrees;
    }

    public static bool IsWithinTarget(float current, float target, float tolerance)
    {
        float minAngle = target - tolerance;
        float maxAngle = target + tolerance;
        return current >= minAngle && current <= maxAngle;
    }

    public static float RotationFromGrab(float grabAngle, float currentAngle)
    {
        return grabAngle - currentAngle;
    }
}
