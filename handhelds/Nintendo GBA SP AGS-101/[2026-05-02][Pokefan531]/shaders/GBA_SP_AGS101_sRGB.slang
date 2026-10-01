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




vec3 handheld_eotf(vec3 color)
{
   float gamma_R = -276.71950874 * pow(color.x, 6.0) + 825.14938357 * pow(color.x, 5.0) - 973.83696825 * pow(color.x, 4.0) + 569.88994586 * pow(color.x, 3.0) - 166.38515899 * pow(color.x, 2.0) + 21.45383770 * color.x + 1.54204699;
   float gamma_G = -261.42182814 * pow(color.y, 6.0) + 783.16083954 * pow(color.y, 5.0) - 932.21927145 * pow(color.y, 4.0) + 551.64968748 * pow(color.y, 3.0) - 163.12517384 * pow(color.y, 2.0) + 21.26951692 * color.y + 1.58882018;
   float gamma_B = -171.26978328 * pow(color.z, 6.0) + 540.59098977 * pow(color.z, 5.0) - 684.06106573 * pow(color.z, 4.0) + 429.32913192 * pow(color.z, 3.0) - 133.78319113 * pow(color.z, 2.0) + 17.49508882 * color.z + 1.56564286;

   return pow(color, vec3(gamma_R, gamma_G, gamma_B));
}

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.43396254, 0.34492423, 0.20792384,
   0.24320469, 0.63657751, 0.12021780,
   0.01820903, 0.06273079, 1.12683885
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    0.98947016, -0.00824300, -0.01467216,
   -0.01437608,  1.01873414, -0.00376531,
   -0.00440864,  0.00833743,  0.89840203
);

const float WHITE_Y = 123.381279;
const vec3 BLACK_XYZ = vec3(0.427354, 0.391151, 0.650539);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    0.98942409, -0.00829935, -0.01484475,
   -0.01448260,  1.01890713, -0.00381294,
   -0.00445586,  0.00842481,  0.89729700
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