// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

/// <summary>
/// Central configuration for hand rotation limits.
/// These constants match the bio-bridge Python configuration (core/config.py).
/// </summary>
public static class HandRotationLimits
{
    // ─────────────────────────────────────────────────────────────────
    // Flexion/Extension Limits (X-axis rotation)
    // ─────────────────────────────────────────────────────────────────
    public const float FLEXION_MAX = -89f; // Maximum flexion
    public const float EXTENSION_MAX = 89f; // Maximum extension

    // ─────────────────────────────────────────────────────────────────
    // Supination/Pronation Limits (Z-axis rotation)
    // ─────────────────────────────────────────────────────────────────
    public const float PRONATION_MAX = -35f; // Maximum pronation
    public const float SUPINATION_MAX = 149f; // Maximum supination

    // ─────────────────────────────────────────────────────────────────
    // Grab Constraint: Hand must be flat (near neutral rotation)
    // ─────────────────────────────────────────────────────────────────
    public const float GRAB_FLAT_TOLERANCE = 5f; // ±5° from neutral (0°)

    // ─────────────────────────────────────────────────────────────────
    // Pouring Task Configuration
    // ─────────────────────────────────────────────────────────────────
    public const float POUR_ANGLE_RANGE = 45f; // Absolute value of SUPINATION_MIN
}
