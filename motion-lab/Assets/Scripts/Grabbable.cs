// Copyright ETH Zurich - University of Bologna 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

public class Grabbable : MonoBehaviour
{
    // True while the item is held by the hand
    public bool IsHeld { get; private set; }

    public void SetHeld(bool held)
    {
        IsHeld = held;
    }
}
