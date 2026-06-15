// Made with Amplify Shader Editor
// Available at the Unity Asset Store - http://u3d.as/y3X
Shader "WorldMatLite"
{
	Properties
	{
		_ColorTint("Color Tint", Color) = (1,1,1,0)
		_Albedo("Albedo", 2D) = "white" {}
		_Normal("Normal", 2D) = "bump" {}
		_NormalScale("Normal Scale", Range( 0 , 3)) = 1
		_Metallic("Metallic", 2D) = "white" {}
		_MetallicStrength("Metallic Strength", Range( 0 , 1)) = 0
		_Smoothness("Smoothness", 2D) = "white" {}
		_SmoothnessStrength("Smoothness Strength", Range( 0 , 2)) = 1
		_Tile("Tile", Range( 1 , 10)) = 1
		[HideInInspector] _texcoord( "", 2D ) = "white" {}
		[HideInInspector] __dirty( "", Int ) = 1
	}

	SubShader
	{
		Tags{ "RenderType" = "Opaque"  "Queue" = "Geometry+0" }
		Cull Back
		CGPROGRAM
		#include "UnityStandardUtils.cginc"
		#pragma target 3.0
		#pragma surface surf Standard keepalpha addshadow fullforwardshadows
		struct Input
		{
			float2 uv_texcoord;
		};

		uniform float _NormalScale;
		uniform sampler2D _Normal;
		uniform float _Tile;
		uniform sampler2D _Albedo;
		uniform float4 _ColorTint;
		uniform sampler2D _Metallic;
		uniform float _MetallicStrength;
		uniform sampler2D _Smoothness;
		uniform float _SmoothnessStrength;

		void surf( Input i , inout SurfaceOutputStandard o )
		{
			float2 temp_cast_0 = (_Tile).xx;
			float2 uv_TexCoord2 = i.uv_texcoord * temp_cast_0;
			o.Normal = UnpackScaleNormal( tex2D( _Normal, uv_TexCoord2 ), _NormalScale );
			o.Albedo = ( tex2D( _Albedo, uv_TexCoord2 ) * _ColorTint ).rgb;
			o.Metallic = ( tex2D( _Metallic, uv_TexCoord2 ) * _MetallicStrength ).r;
			o.Smoothness = ( tex2D( _Smoothness, uv_TexCoord2 ) * _SmoothnessStrength ).r;
			o.Alpha = 1;
		}

		ENDCG
	}
	Fallback "Diffuse"
	CustomEditor "ASEMaterialInspector"
}
/*ASEBEGIN
Version=16400
242;100;1334;586;2270.065;843.0399;2.457362;True;True
Node;AmplifyShaderEditor.RangedFloatNode;1;-2270.301,-15.65767;Float;False;Property;_Tile;Tile;8;0;Create;True;0;0;False;0;1;1;1;10;0;1;FLOAT;0
Node;AmplifyShaderEditor.TextureCoordinatesNode;2;-1960.844,-34.65752;Float;False;0;-1;2;3;2;SAMPLER2D;;False;0;FLOAT2;1,1;False;1;FLOAT2;0,0;False;5;FLOAT2;0;FLOAT;1;FLOAT;2;FLOAT;3;FLOAT;4
Node;AmplifyShaderEditor.RangedFloatNode;5;-1561.757,-134.7136;Float;False;Property;_NormalScale;Normal Scale;3;0;Create;True;0;0;False;0;1;0;0;3;0;1;FLOAT;0
Node;AmplifyShaderEditor.ColorNode;6;-541.751,-522.0322;Float;False;Property;_ColorTint;Color Tint;0;0;Create;True;0;0;False;0;1,1,1,0;0,0,0,0;True;0;5;COLOR;0;FLOAT;1;FLOAT;2;FLOAT;3;FLOAT;4
Node;AmplifyShaderEditor.RangedFloatNode;7;-865.2714,216.3725;Float;False;Property;_SmoothnessStrength;Smoothness Strength;7;0;Create;True;0;0;False;0;1;0;0;2;0;1;FLOAT;0
Node;AmplifyShaderEditor.SamplerNode;11;-1226.722,119.2961;Float;True;Property;_Smoothness;Smoothness;6;0;Create;True;0;0;False;0;None;None;True;0;False;white;Auto;False;Object;-1;Auto;Texture2D;6;0;SAMPLER2D;;False;1;FLOAT2;0,0;False;2;FLOAT;0;False;3;FLOAT2;0,0;False;4;FLOAT2;0,0;False;5;FLOAT;1;False;5;COLOR;0;FLOAT;1;FLOAT;2;FLOAT;3;FLOAT;4
Node;AmplifyShaderEditor.SamplerNode;9;-1222.04,-77.16355;Float;True;Property;_Metallic;Metallic;4;0;Create;True;0;0;False;0;None;None;True;0;False;white;Auto;False;Object;-1;Auto;Texture2D;6;0;SAMPLER2D;;False;1;FLOAT2;0,0;False;2;FLOAT;0;False;3;FLOAT2;0,0;False;4;FLOAT2;0,0;False;5;FLOAT;1;False;5;COLOR;0;FLOAT;1;FLOAT;2;FLOAT;3;FLOAT;4
Node;AmplifyShaderEditor.RangedFloatNode;8;-904.4976,51.49081;Float;False;Property;_MetallicStrength;Metallic Strength;5;0;Create;True;0;0;False;0;0;0;0;1;0;1;FLOAT;0
Node;AmplifyShaderEditor.SamplerNode;12;-1243.926,-466.3678;Float;True;Property;_Albedo;Albedo;1;0;Create;True;0;0;False;0;None;None;True;0;False;white;Auto;False;Object;-1;Auto;Texture2D;6;0;SAMPLER2D;;False;1;FLOAT2;0,0;False;2;FLOAT;0;False;3;FLOAT2;0,0;False;4;FLOAT2;0,0;False;5;FLOAT;1;False;5;COLOR;0;FLOAT;1;FLOAT;2;FLOAT;3;FLOAT;4
Node;AmplifyShaderEditor.SimpleMultiplyOpNode;18;-497.4125,5.999759;Float;False;2;2;0;COLOR;0,0,0,0;False;1;FLOAT;0;False;1;COLOR;0
Node;AmplifyShaderEditor.SimpleMultiplyOpNode;15;-165.0952,-218.4337;Float;False;2;2;0;COLOR;0,0,0,0;False;1;COLOR;0,0,0,0;False;1;COLOR;0
Node;AmplifyShaderEditor.SamplerNode;16;-1251.434,-274.1252;Float;True;Property;_Normal;Normal;2;0;Create;True;0;0;False;0;None;None;True;0;True;bump;Auto;True;Object;-1;Auto;Texture2D;6;0;SAMPLER2D;;False;1;FLOAT2;0,0;False;2;FLOAT;0;False;3;FLOAT2;0,0;False;4;FLOAT2;0,0;False;5;FLOAT;1;False;5;FLOAT3;0;FLOAT;1;FLOAT;2;FLOAT;3;FLOAT;4
Node;AmplifyShaderEditor.SimpleMultiplyOpNode;17;-471.3352,116.875;Float;False;2;2;0;COLOR;0,0,0,0;False;1;FLOAT;0;False;1;COLOR;0
Node;AmplifyShaderEditor.StandardSurfaceOutputNode;0;0,0;Float;False;True;2;Float;ASEMaterialInspector;0;0;Standard;WorldMatLite;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;False;Back;0;False;-1;0;False;-1;False;0;False;-1;0;False;-1;False;0;Opaque;0.5;True;True;0;False;Opaque;;Geometry;All;True;True;True;True;True;True;True;True;True;True;True;True;True;True;True;True;True;0;False;-1;False;0;False;-1;255;False;-1;255;False;-1;0;False;-1;0;False;-1;0;False;-1;0;False;-1;0;False;-1;0;False;-1;0;False;-1;0;False;-1;False;2;15;10;25;False;0.5;True;0;0;False;-1;0;False;-1;0;0;False;-1;0;False;-1;0;False;-1;0;False;-1;0;False;0;0,0,0,0;VertexOffset;True;False;Cylindrical;False;Relative;0;;-1;-1;-1;-1;0;False;0;0;False;-1;-1;0;False;-1;0;0;0;False;0.1;False;-1;0;False;-1;16;0;FLOAT3;0,0,0;False;1;FLOAT3;0,0,0;False;2;FLOAT3;0,0,0;False;3;FLOAT;0;False;4;FLOAT;0;False;5;FLOAT;0;False;6;FLOAT3;0,0,0;False;7;FLOAT3;0,0,0;False;8;FLOAT;0;False;9;FLOAT;0;False;10;FLOAT;0;False;13;FLOAT3;0,0,0;False;11;FLOAT3;0,0,0;False;12;FLOAT3;0,0,0;False;14;FLOAT4;0,0,0,0;False;15;FLOAT3;0,0,0;False;0
WireConnection;2;0;1;0
WireConnection;11;1;2;0
WireConnection;9;1;2;0
WireConnection;12;1;2;0
WireConnection;18;0;9;0
WireConnection;18;1;8;0
WireConnection;15;0;12;0
WireConnection;15;1;6;0
WireConnection;16;1;2;0
WireConnection;16;5;5;0
WireConnection;17;0;11;0
WireConnection;17;1;7;0
WireConnection;0;0;15;0
WireConnection;0;1;16;0
WireConnection;0;3;18;0
WireConnection;0;4;17;0
ASEEND*/
//CHKSM=FEAA8385AFB16F223CDA862591CE2E4EE3BD8B76
