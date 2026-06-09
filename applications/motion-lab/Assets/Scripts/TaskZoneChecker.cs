// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using UnityEngine;

/// <summary>
/// Shared zone checks for delivery tasks (delivery trigger + pickup spawn area).
/// </summary>
public static class TaskZoneChecker
{
    public static bool IsInDeliveryZone(DeliveryZone zone, Rigidbody rb, GameObject obj)
    {
        if (zone == null)
            return false;

        return zone.ContainsObject(rb, obj);
    }

    public static bool IsInPickupZone(
        Vector3 spawnPosition,
        float radius,
        Rigidbody rb,
        GameObject obj
    )
    {
        if (rb == null)
            return false;

        float radiusSq = radius * radius;
        if ((rb.worldCenterOfMass - spawnPosition).sqrMagnitude <= radiusSq)
            return true;

        if (obj != null && (obj.transform.position - spawnPosition).sqrMagnitude <= radiusSq)
            return true;

        return false;
    }

    /// <summary>
    /// Object is no longer held by the hand (Grabbable flag and grab joint cleared).
    /// </summary>
    public static bool IsReleased(Grabbable grabbable, Rigidbody rb)
    {
        if (rb == null)
            return false;

        bool heldByGrabbable = grabbable != null && grabbable.IsHeld;
        bool heldByJoint = rb.GetComponent<FixedJoint>() != null;

        return !heldByGrabbable && !heldByJoint;
    }
}
