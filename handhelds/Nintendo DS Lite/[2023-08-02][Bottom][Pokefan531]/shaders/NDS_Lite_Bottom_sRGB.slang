#version 450

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
   float ChromaticAdaptation;
   float ImproveContrast;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
};

#pragma parameter ChromaticAdaptation "Chromatic Adaptation (0 = OFF, 1 = D65)" 0.0 0.0 1.0 1.0
#pragma parameter ImproveContrast "Remove backlight distortion (0 = OFF, 1 = ON)" 1.0 0.0 1.0 1.0
#pragma parameter DebugOutOfGamut "[Debug] Show `out of Gamut` colours" 0.0 0.0 1.0 1.0
#pragma parameter RedScale "[Debug] RED scale " 0.0 0.0 1.0 1.0
#pragma parameter GreenScale "[Debug] GREEN scale " 0.0 0.0 1.0 1.0
#pragma parameter BlueScale "[Debug] BLUE scale " 0.0 0.0 1.0 1.0

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
   2.0889809,
   2.0889809, 2.16369471, 2.19318528, 2.20868335, 2.21625806, 2.21872198, 2.21755273, 2.23767818, 2.25404818, 2.26306022,
   2.27567691, 2.29553187, 2.3120031, 2.32141088, 2.34647193, 2.36044514, 2.37740879, 2.38787912, 2.41070109, 2.43785607,
   2.46973277, 2.49904537, 2.53051448, 2.58250042, 2.63292519, 2.66891042, 2.74766432, 2.8334605, 2.98412571, 3.18127648,
   3.18127648
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   2.05717975,
   2.05717975, 2.13308838, 2.16162911, 2.17541164, 2.17994879, 2.17999979, 2.17173195, 2.19173225, 2.20266639, 2.20687968,
   2.21408425, 2.22730918, 2.23676628, 2.23575425, 2.253627, 2.25771606, 2.26585769, 2.26514961, 2.27680006, 2.28182854,
   2.29631772, 2.30780647, 2.32146634, 2.34882315, 2.36074455, 2.35148186, 2.39425467, 2.40720025, 2.48433354, 2.49865074,
   2.49865074
);

const float GAMMA_B[GAMMA_SAMPLES] = float[](
   1.97753741,
   1.97753741, 2.00229294, 1.98981193, 1.97054847, 1.94354164, 1.91194126, 1.87008775, 1.86090767, 1.84263286, 1.80647262,
   1.78022339, 1.77132536, 1.74368648, 1.7081508, 1.68618597, 1.64577383, 1.61474142, 1.56131889, 1.52141484, 1.46445073,
   1.43152594, 1.37532805, 1.31810622, 1.25869644, 1.1747797, 1.06178035, 0.97890751, 0.87293473, 0.72718189, 0.54586209,
   0.54586209
);

vec3 handheld_eotf(vec3 color)
{
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
   0.38196329,  0.35866769,  0.21493801,
   0.2116574,   0.6526344,   0.1357082, 
   0.03043753,  0.07076411,  1.08789792
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    1.01047239,  0.00417994, -0.01623085,
    0.00458779,  1.00186543, -0.00525556,
   -0.00335887,  0.00572165,  0.91375505
);

const float WHITE_Y = 176.062531;
const vec3 BLACK_XYZ = vec3(0.3017, 0.299404, 0.443914);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    1.01047625,  0.00417298, -0.01629654,
    0.00456957,  1.00190804, -0.00527487,
   -0.00337519,  0.0057511 ,  0.9133602
);



// sRGB

const mat3 SRGB_XYZ_TO_RGB_LIN_MTX = mat3(
    3.2406255, -1.5372080, -0.4986286,
   -0.9689307,  1.8757561,  0.0415175,
    0.0557101, -0.2040211,  1.0569959
);

vec3 srgb_oetf(vec3 color)
{
   vec3 linear = 12.92 * color;
   vec3 nonlinear = 1.055 * pow(color, vec3(1.0 / 2.4)) - 0.055;
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
   vec3 handheld_xyz = transpose(HANDHELD_RGB_LIN_TO_XYZ) * handheld_linearized_rgb;

   if (ImproveContrast == 0.0)
      handheld_xyz += BLACK_XYZ_NORMALIZED;

   // 3. chromatic adaptation (handheld XYZ -> target XYZ)
   vec3 target_xyz = handheld_xyz;
   if (ChromaticAdaptation == 1.0)
      if (ImproveContrast == 0.0) {
         target_xyz = transpose(CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK) * handheld_xyz;
      } else {
         target_xyz = transpose(CAT_BRADFORD_HANDHELD_TO_SRGB) * handheld_xyz;
      }

   // 4. target XYZ -> target linearized RGB
   vec3 target_linearized_rgb = transpose(SRGB_XYZ_TO_RGB_LIN_MTX) * target_xyz;

   // 5. target colorspace OETF
   vec3 target_rgb = srgb_oetf(target_linearized_rgb);

   // post processing: out of gamut
   if (DebugOutOfGamut == 1.0)
      target_rgb = compute_out_of_gamut(target_rgb);
   
   FragColor = vec4(target_rgb, handheld_rgba.w);
}