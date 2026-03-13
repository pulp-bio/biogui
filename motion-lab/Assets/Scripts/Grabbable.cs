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
