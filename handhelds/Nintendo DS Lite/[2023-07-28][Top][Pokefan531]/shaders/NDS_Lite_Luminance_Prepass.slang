#version 450

// Pass 0: linearize each pixel and output relative luminance Y.
// The output of this pass is mipmap-filtered by RetroArch (mipmap_input1 = true
// in the .slangp), so textureLod() on this pass's output in pass 1 yields the
// true frame-average linear luminance - no Jensen's-inequality bias.

#pragma name NDS_Lite_Luminance_Prepass
#pragma format R8G8B8A8_UNORM

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
};

#pragma stage vertex
layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;

void main()
{
   gl_Position = MVP * Position;
   vTexCoord = TexCoord;
}

#pragma stage fragment
layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(binding = 1) uniform sampler2D Source;


const int GAMMA_SAMPLES = 32;

const float GAMMA_R[GAMMA_SAMPLES] = float[](
   2.0767131,
   2.0767131, 2.13710327, 2.16192389, 2.174535, 2.18082821, 2.17736862, 2.18590351, 2.19329852, 2.20582927, 2.21727465,
   2.22441409, 2.23665199, 2.24936615, 2.2554995, 2.28611537, 2.29853204, 2.31237332, 2.32314759, 2.34484611, 2.38284314,
   2.39525252, 2.41673623, 2.46492914, 2.48669639, 2.52784711, 2.56367325, 2.63291794, 2.73672018, 2.85988438, 3.01728606,
   3.01728606
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   2.03869367,
   2.03869367, 2.10226738, 2.12656252, 2.1376844, 2.14225133, 2.13764196, 2.14233572, 2.14473351, 2.15260244, 2.15837463,
   2.16270391, 2.16922457, 2.17524887, 2.17353028, 2.19437723, 2.19713962, 2.20355689, 2.2006526, 2.20930412, 2.23443641,
   2.22931336, 2.23224255, 2.26851194, 2.25249423, 2.25892754, 2.26643039, 2.29540508, 2.35013924, 2.37799253, 2.36084201,
   2.36084201
);

const float GAMMA_B[GAMMA_SAMPLES] = float[](
   1.91615459,
   1.91615459, 1.94367982, 1.93405157, 1.91393789, 1.88824277, 1.8507469, 1.82631097, 1.80331521, 1.77831729, 1.75575943,
   1.72070312, 1.69625874, 1.66332715, 1.62494244, 1.61367298, 1.56844866, 1.53154955, 1.48234401, 1.43629385, 1.40338909,
   1.33513557, 1.27789131, 1.26039319, 1.13948331, 1.05192119, 0.99264375, 0.8816358, 0.84398413, 0.66308729, 0.35011463,
   0.35011463
);

vec3 handheld_eotf(vec3 color)
{
   color = clamp(color, 0.0, 1.0);
   vec3 denormalized_color = color * float(GAMMA_SAMPLES - 1);
   ivec3 idx_low = ivec3(floor(denormalized_color));
   ivec3 idx_high = ivec3(ceil(denormalized_color));
   vec3 weight = fract(denormalized_color);

   float gr = mix(GAMMA_R[idx_low.x], GAMMA_R[idx_high.x], weight.x);
   float gg = mix(GAMMA_G[idx_low.y], GAMMA_G[idx_high.y], weight.y);
   float gb = mix(GAMMA_B[idx_low.z], GAMMA_B[idx_high.z], weight.z);

   return pow(color, vec3(gr, gg, gb));
}

// Y row of HANDHELD_RGB_LIN_TO_XYZ: luminance coefficients for the NDS Lite display
const vec3 LUM_COEFFS = vec3(0.21674235, 0.65064109, 0.13261656);

void main()
{
   vec4 original = texture(Source, vTexCoord);
   float Y = dot(handheld_eotf(original.rgb), LUM_COEFFS);
   // RGB: original encoded NDS pixels (read at LOD 0 in pass 1)
   // A:   linear relative luminance Y (mipmap-averaged to get frame mean)
   FragColor = vec4(original.rgb, Y);
}
