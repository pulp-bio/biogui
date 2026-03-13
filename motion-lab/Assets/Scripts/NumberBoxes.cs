using TMPro;
using UnityEngine;

[ExecuteAlways]
[RequireComponent(typeof(BoxTask))]
public class BoxNumberLabel : MonoBehaviour
{
    public Vector3 offset = new Vector3(0, 0.6f, 0);
    public float fontSize = 0.4f;
    public Color color = Color.white;

    private TextMeshPro _tmp;
    private BoxTask _task;

    void OnEnable()
    {
        _task = GetComponent<BoxTask>();
        EnsureLabel();
        UpdateLabel();
    }

    void EnsureLabel()
    {
        if (_tmp != null)
            return;
        var go = transform.Find("BoxLabel")?.gameObject ?? new GameObject("BoxLabel");
        go.transform.SetParent(transform, false);
        _tmp = go.GetComponent<TextMeshPro>() ?? go.AddComponent<TextMeshPro>();
        _tmp.alignment = TextAlignmentOptions.Center;
        _tmp.textWrappingMode = TextWrappingModes.NoWrap;
        _tmp.fontSize = fontSize;
        _tmp.color = color;
    }

    void Update()
    {
        if (!_tmp)
            return;
        if (Camera.main)
        {
            _tmp.transform.rotation = Quaternion.LookRotation(
                _tmp.transform.position - Camera.main.transform.position
            );
        }
        _tmp.transform.localPosition = offset;
        _tmp.fontSize = fontSize;
        _tmp.color = color;
    }

    void UpdateLabel()
    {
        if (_tmp && _task)
            _tmp.text = _task.orderIndex.ToString();
    }

    void OnValidate() => UpdateLabel();
}
