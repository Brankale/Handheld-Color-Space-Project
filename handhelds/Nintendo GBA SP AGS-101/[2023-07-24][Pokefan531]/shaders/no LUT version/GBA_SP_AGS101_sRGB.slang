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

#pragma parameter ChromaticAdaptation "Chromatic Adaptation (0 = OFF, 1 = ON)" 1.0 0.0 1.0 1.0
#pragma parameter ImproveContrast "Improve Contrast (1 = ON, 0 = OFF)" 1.0 0.0 1.0 1.0
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
   2.110, // gamma[0] = gamma[1]
   2.110, 2.283, 2.428, 2.482, 2.457, 2.388, 2.323, 2.258, 2.271, 2.276,
   2.247, 2.259, 2.328, 2.355, 2.408, 2.467, 2.496, 2.582, 2.669, 2.729,
   2.742, 2.811, 2.780, 2.832, 2.797, 2.942, 2.976, 2.833, 2.458, 1.974, 
   1.974  // gamma[31] = gamma[30]
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   2.097, // gamma[0] = gamma[1]
   2.097, 2.272, 2.422, 2.468, 2.443, 2.371, 2.298, 2.228, 2.238, 2.240,
   2.204, 2.216, 2.276, 2.298, 2.346, 2.396, 2.423, 2.501, 2.575, 2.635,
   2.637, 2.685, 2.635, 2.669, 2.617, 2.747, 2.745, 2.608, 2.232, 1.644, 
   1.644  // gamma[31] = gamma[30]
);

const float GAMMA_B[GAMMA_SAMPLES]  = float[](
   1.987, // gamma[0] = gamma[1]
   1.987, 2.134, 2.255, 2.276, 2.229, 2.133, 2.039, 1.947, 1.933, 1.909,
   1.855, 1.837, 1.871, 1.863, 1.876, 1.892, 1.877, 1.913, 1.949, 1.956,
   1.900, 1.899, 1.774, 1.740, 1.614, 1.673, 1.564, 1.382, 1.114, 0.877, 
   0.877  // gamma[31] = gamma[30]
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
   0.425287783341, 0.34714068541, 0.212756689885,
   0.237300233948, 0.638744541979, 0.123955224073,
   0.0209770211289, 0.060791803406, 1.15243512768
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    0.99435579934, -0.00591198866531, -0.0188434497843,
   -0.0112605313102, 1.01753503324, -0.00521901173748,
   -0.0051283888247, 0.00947697145491, 0.878811958039
);

const float WHITE_Y = 122.963692;
const vec3 BLACK_XYZ = vec3(0.50662, 0.476724, 0.78571);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    0.990502545742, -0.00592081191287, -0.0189626817761,
   -0.0112877375384, 1.01374036194, -0.00525437847233,
   -0.00515757560115, 0.00952941070824, 0.874236252693
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