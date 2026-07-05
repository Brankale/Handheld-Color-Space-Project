#version 450

#pragma name NDS_Lite_Top_sRGB
#pragma format R8G8B8A8_UNORM

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
};

layout(push_constant) uniform Push
{
   float ChromaticAdaptation;
   float ImproveContrast;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
   float DebugSplitScreen;
};

#pragma parameter ChromaticAdaptation "D65 illuminant (0=OFF, 1=CIECAT16, 2=CIECAM16)" 0.0 0.0 2.0 1.0
#pragma parameter ImproveContrast "Remove backlight distortion (0 = OFF, 1 = ON)" 1.0 0.0 1.0 1.0
#pragma parameter DebugOutOfGamut "[Debug] Show `out of Gamut` colours" 0.0 0.0 1.0 1.0
#pragma parameter RedScale "[Debug] RED scale " 0.0 0.0 1.0 1.0
#pragma parameter GreenScale "[Debug] GREEN scale " 0.0 0.0 1.0 1.0
#pragma parameter BlueScale "[Debug] BLUE scale " 0.0 0.0 1.0 1.0
#pragma parameter DebugSplitScreen "[Debug] Average luminance" 0.0 0.0 1.0 1.0

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

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.39223169,  0.21674235,  0.0364544,   // column 0 (R -> X, Y, Z)
   0.36370755,  0.65064109,  0.06923906,  // column 1 (G -> X, Y, Z)
   0.23391794,  0.13261656,  1.18130254   // column 2 (B -> X, Y, Z)
);

const float WHITE_Y = 199.22644;
const vec3 BLACK_XYZ = vec3(0.332459, 0.318527, 0.545375);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;


// sRGB

const mat3 SRGB_XYZ_TO_RGB_LIN_MTX = mat3(
    3.2406255, -0.9689307,  0.0557101,   // column 0 (X -> R, G, B)
   -1.5372080,  1.8757561, -0.2040211,   // column 1 (Y -> R, G, B)
   -0.4986286,  0.0415175,  1.0569959    // column 2 (Z -> R, G, B)
);

// end (sRGB)



// CIECAT16 (CAT16, CIE 248:2022) Chromatic Adaptation

// column-major
const mat3 M_CAT16 = mat3(
    0.401288, -0.250268, -0.002079,  // column 0 (X -> L, M, S)
    0.650173,  1.204414,  0.048952,  // column 1 (Y -> L, M, S)
   -0.051461,  0.045854,  0.953127   // column 2 (Z -> L, M, S)
);

const mat3 M_CAT16_INV = mat3(
    1.862068,  0.387527, -0.015841,  // column 0 (L -> X, Y, Z)
   -1.011255,  0.621447, -0.034123,  // column 1 (M -> X, Y, Z)
    0.149187, -0.008974,  1.049964   // column 2 (S -> X, Y, Z)
);

// NDS Lite white point: column sums of HANDHELD_RGB_LIN_TO_XYZ
const vec3 W_SRC = vec3(0.98985718, 1.0, 1.28699600);

// sRGB D65 white point
const vec3 W_REF = vec3(0.95045593, 1.0, 1.08905775);


const vec3 LMS_W_SRC = M_CAT16 * W_SRC;
const vec3 LMS_W_REF = M_CAT16 * W_REF;

// Per-channel scale for full adaptation (D=1): LMS_W_REF / LMS_W_SRC
const vec3 CIECAT16_FULL_SCALE = LMS_W_REF / LMS_W_SRC;

// CIECAT16 full chromatic adaptation (D=1, complete adaptation)
vec3 ciecat16(vec3 xyz)
{
   return M_CAT16_INV * (CIECAT16_FULL_SCALE * (M_CAT16 * xyz));
}

const float F = 0.8; // dark environment

float get_degree_of_adaptation(float L_A)
{
   float D = F * (1.0 - (1.0 / 3.6) * exp(-(L_A + 42.0) / 92.0));
   return clamp(D, 0.0, 1.0);
}

// CIECAM16 partial chromatic adaptation
vec3 ciecam16(vec3 xyz, float D)
{
   vec3 lms = M_CAT16 * xyz;
   vec3 d_src = D / LMS_W_SRC + (1.0 - D);
   vec3 d_dst = D / LMS_W_REF + (1.0 - D);
   return M_CAT16_INV * ((d_src / d_dst) * lms);
}

// end (CIECAT16)



// sRGB

vec3 srgb_oetf(vec3 color)
{
   vec3 linear = 12.92 * color;
   vec3 nonlinear = 1.055 * pow(max(color, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
   bvec3 cond = lessThanEqual(color, vec3(0.0031308));
   return mix(nonlinear, linear, vec3(cond));
}

// end (sRGB)



// Pre-Processing & Post-Processing

vec3 compute_out_of_gamut(vec3 color)
{
   float error = 1.0 / (255.0 * 10.0);
   bool is_out_of_gamut = any(lessThan(color, vec3(0.0 - error))) || any(greaterThan(color, vec3(1.0 + error)));
   color = clamp(color, 0.0, 1.0);
   float grey = (color.x + color.y + color.z) / 3.0;
   vec3 out_of_gamut = vec3(1.0, grey / 2.5, grey / 2.5);
   vec3 non_out_of_gamut = vec3(grey, grey, grey);
   return mix(non_out_of_gamut, out_of_gamut, float(is_out_of_gamut));
}

// end (Pre-Processing & Post-Processing)

void main()
{
   // L_A: frame-average absolute luminance - mipmap LOD 100 clamps to the 1x1 level
   // (true linear average because pass 0 stored linear Y in the A channel)
   float Y_avg = textureLod(Source, vec2(0.5, 0.5), 100.0).a;
   float L_A = Y_avg * WHITE_Y;

   // use 20% gray world assumption because Y_avg seems to have issues
   L_A = 0.2 * WHITE_Y;

   // Original NDS pixel from pass 0 RGB channels
   vec4 handheld_rgba = texture(Source, vTexCoord);

   // debug: color scales
   if ((RedScale + GreenScale + BlueScale) > 0.0) {
      handheld_rgba = vec4(
         mix(0.0, vTexCoord.x, RedScale), 
         mix(0.0, vTexCoord.x, GreenScale), 
         mix(0.0, vTexCoord.x, BlueScale), 
         1.0
      );
   }

   // 1. handheld colorspace EOTF
   vec3 handheld_linearized_rgb = handheld_eotf(handheld_rgba.rgb);

   // 2. handheld linearized RGB -> handheld XYZ
   vec3 handheld_xyz = HANDHELD_RGB_LIN_TO_XYZ * handheld_linearized_rgb;

   if (ImproveContrast == 0.0)
      handheld_xyz += BLACK_XYZ_NORMALIZED;

   // 3. chromatic adaptation (handheld XYZ -> target XYZ)
   vec3 target_xyz = handheld_xyz;

   if (ChromaticAdaptation == 1.0) {
      target_xyz = ciecat16(handheld_xyz);
   } else if (ChromaticAdaptation == 2.0) {
      target_xyz = ciecam16(handheld_xyz, get_degree_of_adaptation(L_A));
   }

   // 4. target XYZ -> target linearized RGB
   vec3 target_linearized_rgb = SRGB_XYZ_TO_RGB_LIN_MTX * target_xyz;

   // 5. target colorspace OETF
   vec3 target_rgb = srgb_oetf(target_linearized_rgb);

   // post processing: out of gamut
   if (DebugOutOfGamut == 1.0)
      target_rgb = compute_out_of_gamut(target_rgb);

   if (DebugSplitScreen == 1.0) {
      if (vTexCoord.x < 0.2 && vTexCoord.y < 0.2) {
         target_rgb = vec3(Y_avg);
      }
   }

   FragColor = vec4(target_rgb, handheld_rgba.w);
}