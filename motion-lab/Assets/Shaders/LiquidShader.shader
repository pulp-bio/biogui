Shader "Custom/LiquidShader"
{
    Properties
    {
        _Color ("Liquid Color", Color) = (1, 0, 0, 0.8)
        _FillAmount ("Fill Amount", Range(0, 1)) = 1.0
        _TopColor ("Top Surface Color", Color) = (1, 0.3, 0.3, 1)
        _MinY ("Min Y", Float) = -0.5
        _MaxY ("Max Y", Float) = 0.5
    }
    
    SubShader
    {
        Tags {"Queue"="Transparent" "RenderType"="Transparent"}
        LOD 100
        
        Cull Off
        ZWrite On
        Blend SrcAlpha OneMinusSrcAlpha
        
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            
            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
            };
            
            struct v2f
            {
                float4 vertex : SV_POSITION;
                float3 normal : TEXCOORD0;
                float fillEdge : TEXCOORD1;
            };
            
            float4 _Color;
            float _FillAmount;
            float4 _TopColor;
            float _MinY;
            float _MaxY;
            
            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.normal = v.normal;
                
                // Normalize Y to 0-1 range using actual mesh bounds
                float normalizedY = (v.vertex.y - _MinY) / (_MaxY - _MinY);
                
                // fillEdge: positive = above fill level (discard)
                // fillAmount 1.0 = full, 0.0 = empty
                o.fillEdge = normalizedY - _FillAmount;
                
                return o;
            }
            
            fixed4 frag (v2f i) : SV_Target
            {
                if (i.fillEdge > 0)
                    discard;
                
                // Top surface
                if (i.fillEdge > -0.03 && i.normal.y > 0.3)
                    return _TopColor;
                
                return _Color;
            }
            ENDCG
        }
    }
    FallBack "Transparent/Diffuse"
}
