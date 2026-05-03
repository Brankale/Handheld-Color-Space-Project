#version 450

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
   float ChromaticAdaptation;
   float Mode;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
};

#pragma parameter ChromaticAdaptation "Chromatic Adaptation (0 = OFF, 1 = ON)" 0.0 0.0 1.0 1.0
#pragma parameter Mode "Mode: 0 = linear fit of 1, 1 = white scaled gamma, 2 = exp fit)" 0.0 0.0 2.0 1.0
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

const float GAMMA_RED[GAMMA_SAMPLES] = float[](
   1.855,
   1.855, 1.855, 1.855, 1.440, 1.404, 1.371, 1.215, 1.171, 1.220, 1.152,
   1.108, 1.136, 1.195, 1.224, 1.220, 1.149, 1.157, 1.098, 1.076, 1.120,
   1.101, 1.045, 1.148, 1.005, 0.942, 0.904, 0.966, 0.580, 0.518, -0.597,
   -0.597
);

const float GAMMA_GREEN[GAMMA_SAMPLES] = float[](
   1.040,
   1.040, 1.002, 0.988, 1.025, 0.932, 0.871, 0.781, 0.759, 0.690, 0.660,
   0.604, 0.588, 0.589, 0.587, 0.584, 0.557, 0.514, 0.480, 0.399, 0.369,
   0.377, 0.435, 0.306, 0.367, 0.388, 0.389, 0.342, 0.325, 0.104, 0.027,
   0.027
);

const float GAMMA_BLUE[GAMMA_SAMPLES]  = float[](
   3.644,
   3.644, 3.644, 3.644, 3.644, 3.644, 3.644, 2.206, 1.852, 2.020, 1.664,
   1.598, 1.711, 1.743, 1.717, 1.716, 1.567, 1.490, 1.405, 1.540, 1.575,
   1.519, 1.250, 1.637, 1.206, 1.022, 0.912, 0.978, 0.378, 0.240, 1.323,
   1.323
);

float get_handheld_gamma_for_color(float normalized_color, float gamma[GAMMA_SAMPLES])
{
   float denormalized_color = normalized_color * float(GAMMA_SAMPLES - 1);
   int idx_low = int(floor(denormalized_color));
   int idx_high = int(ceil(denormalized_color));
   float weight = fract(denormalized_color);
   return mix(gamma[idx_low], gamma[idx_high], weight);
}

vec3 handheld_eotf(vec3 color)
{
   float gr = 0.0;
   float gg = 0.0;
   float gb = 0.0;

   if (Mode == 0.0) {
      gr = -1.123440 * color.x + 1.666639;
      gg = -0.903290 * color.y + 1.020945;
      gb = -2.136544 * color.z + 2.757094;
   } else if (Mode == 1.0) {
      gr = get_handheld_gamma_for_color(color.x, GAMMA_RED);
      gg = get_handheld_gamma_for_color(color.y, GAMMA_GREEN);
      gb = get_handheld_gamma_for_color(color.z, GAMMA_BLUE);
   } else if (Mode == 2.0) {
      gr = 1.653894e-6 * exp(17.090399 * color.x) + 2.607381;
      gg = 9.605274e-8 * exp(19.000905 * color.y) + 1.145976;
      gb = 1.766850e-4 * exp(11.746733 * color.z) + 2.966668;
   }
   
   return pow(color, vec3(gr, gg, gb));
}


const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
0.39047014,  0.37545817,  0.13172946,
0.26012326,  0.53277684,  0.2070999 ,
0.12999515,  0.26123617,  0.39747487
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
0.99839751,  0.00201684,  0.06620946,
0.0106658,   0.97474986,  0.01987546,
0.01587832, -0.02836048,  1.39870201
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

const vec3 BLACK_XYZ = vec3(0.302392, 0.314958, 0.281989);
const vec3 R_XYZ = vec3(0.414076, 0.275849, 0.137854);
const vec3 G_XYZ = vec3(0.370922, 0.52634, 0.38557);
const vec3 B_XYZ = vec3(0.302392, 0.314958, 0.281989);

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

   // 3. chromatic adaptation (handheld XYZ -> target XYZ)
   vec3 target_xyz = handheld_xyz;
   if (ChromaticAdaptation == 1.0)
      target_xyz = transpose(CAT_BRADFORD_HANDHELD_TO_SRGB) * handheld_xyz;

   // 4. target XYZ -> target linearized RGB
   vec3 target_linearized_rgb = transpose(SRGB_XYZ_TO_RGB_LIN_MTX) * target_xyz;

   // 5. target colorspace OETF
   vec3 target_rgb = srgb_oetf(target_linearized_rgb);

   // post processing: out of gamut
   if (DebugOutOfGamut == 1.0)
      target_rgb = compute_out_of_gamut(target_rgb);
   
   FragColor = vec4(target_rgb, handheld_rgba.w);
}
