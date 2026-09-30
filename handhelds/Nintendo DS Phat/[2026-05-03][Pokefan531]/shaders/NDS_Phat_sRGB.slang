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


const int GAMMA_SAMPLES = 22;

const float GAMMA_R[GAMMA_SAMPLES] = float[](
   1.87737176, // gamma[0] = gamma[1]
   1.87737176, 1.82048314, 1.95909622, 1.86438456, 1.95186334, 1.83855526, 1.90936134, 1.82046966, 1.90673908, 1.83734752,
   1.93856764, 1.85512424, 1.95275951, 1.86988474, 2.03689444, 1.87070282, 2.06629294, 1.89357797, 2.28527094, 1.52647976,
   1.52647976  // gamma[31] = gamma[30]
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   2.11165086, // gamma[0] = gamma[1]
   2.11165086, 2.07894442, 2.24799787, 2.16371328, 2.28111671, 2.17879005, 2.27950006, 2.20816886, 2.32959419, 2.28229452,
   2.42126622, 2.36926675, 2.52676332, 2.46731631, 2.65844105, 2.61701026, 2.87024828, 2.6974767 , 3.15116901, 2.62935232,
   2.62935232  // gamma[31] = gamma[30]
);

const float GAMMA_B[GAMMA_SAMPLES]  = float[](
   2.36270063, // gamma[0] = gamma[1]
   2.36270063, 2.06310079, 2.14259882, 1.92368565, 1.96383186, 1.75848196, 1.78118224, 1.61740708, 1.65176213, 1.50804811,
   1.54152574, 1.3786611 , 1.397314  , 1.20584912, 1.2122414 , 0.96839024, 0.92846417, 0.56209545, 0.40887741, -0.2571288,
   -0.2571288  // gamma[31] = gamma[30]
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
   0.40680985, 0.37635021, 0.20830245,
   0.25691796, 0.52379249, 0.21928955,
   0.13913594, 0.27466174, 0.87629653
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    0.99755918, -0.00521725, -0.02586583,
   -0.0109917,   1.02044656, -0.00740155,
   -0.00670877,  0.01224573,  0.83983286
);

const float WHITE_Y = 35.117145;
const vec3 BLACK_XYZ = vec3(0.345786, 0.325394, 0.543663);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    0.9975749,  -0.00528465, -0.02625574,
   -0.01114005,  1.0207726,  -0.00751405,
   -0.00680861,  0.01242736,  0.83747437
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