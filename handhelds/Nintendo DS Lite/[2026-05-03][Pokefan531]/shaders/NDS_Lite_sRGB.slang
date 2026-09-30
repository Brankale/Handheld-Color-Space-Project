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
   float gamma_R = -3.35795391 * pow(color.x, 3.0) + 4.96861865 * pow(color.x, 2.0) -1.91746513 * color.x + 2.26822719;
   float gamma_G = -4.06412851 * pow(color.y, 3.0) + 5.38865183 * pow(color.y, 2.0) -2.05475486 * color.y + 2.32401748;
   float gamma_B = -4.1474596  * pow(color.z, 3.0) + 4.58327354 * pow(color.z, 2.0) -2.63975762 * color.z + 2.18035343;

   return pow(color, vec3(gamma_R, gamma_G, gamma_B));
}

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.40094039, 0.36094504, 0.22899434,
   0.22103627, 0.65116361, 0.12780012,
   0.02965359, 0.06665591, 1.15413578
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    0.99240914, -0.00739114, -0.0204016,
   -0.01371755,  1.02055665, -0.00556938,
   -0.0056655,   0.01052136,  0.86701133
);

const float WHITE_Y = 192.666743;
const vec3 BLACK_XYZ = vec3(0.334487, 0.538120, 0.901550);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    0.99333851, -0.00686969, -0.02071604,
   -0.01294997,  1.01996195, -0.00570731,
   -0.00568029,  0.01051622,  0.86620034
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