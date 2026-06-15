// Copyright University of Bologna - ETH Zurich 2026
// Licensed under Apache v2.0 see LICENSE for details.
//
// SPDX-License-Identifier: Apache-2.0

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class MaterialSwithcer : MonoBehaviour
{
    public List<MeshRenderer> renderers;
    public Text materialName;
    public List<Material> materials = new List<Material>();

    int currentIndex = 0;

    public void Go2NextMaterial()
    {
        currentIndex = ++currentIndex % materials.Count;

        SwitchMaterial();
    }

    public void Go2PrevMaterial()
    {
        currentIndex = --currentIndex;
        if (currentIndex < 0)
            currentIndex = materials.Count - 1;

        SwitchMaterial();
    }

    private void SwitchMaterial()
    {
        for (int i = 0; i < renderers.Count; i++)
        {
            Material[] mats = renderers[i].materials;
            mats[0] = materials[currentIndex];
            renderers[i].materials = mats;
        }

        materialName.text = materials[currentIndex].name;
        Debug.Log(materials[currentIndex].name);

    }
}
