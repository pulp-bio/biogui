// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Marker for colliders that should participate in physics but never be considered
/// grabbable by the hand. Useful for support colliders that keep complex props from
/// sinking into the table.
/// </summary>
public class IgnoreGrabCollider : MonoBehaviour { }
