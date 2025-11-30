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

#pragma parameter ChromaticAdaptation "Chromatic Adaptation (0 = OFF, 1 = ON)" 0.0 0.0 1.0 1.0
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
   2.616, // gamma[0] = gamma[1]
   2.616, 2.301, 1.652, 1.403, 1.331, 1.257, 1.130, 1.090, 1.098, 1.035,
   0.988, 1.010, 1.047, 1.063, 1.065, 1.007, 0.990, 0.940, 0.920, 0.939,
   0.930, 0.887, 0.953, 0.841, 0.789, 0.752, 0.783, 0.473, 0.352, -0.111, 
   -0.111  // gamma[31] = gamma[30]
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   1.139, // gamma[0] = gamma[1]
   1.139, 1.123, 1.103, 1.114, 1.024, 0.957, 0.863, 0.838, 0.783, 0.747,
   0.694, 0.688, 0.695, 0.697, 0.698, 0.665, 0.625, 0.589, 0.526, 0.506,
   0.512, 0.544, 0.466, 0.482, 0.483, 0.473, 0.444, 0.350, 0.149, 0.085, 
   0.085  // gamma[31] = gamma[30]
);

const float GAMMA_B[GAMMA_SAMPLES] = float[](
   1.928, // gamma[0] = gamma[1]
   1.928, 1.928, 1.928, 1.928, 1.718, 1.477, 1.328, 1.257, 1.280, 1.171,
   1.124, 1.168, 1.199, 1.203, 1.210, 1.136, 1.093, 1.038, 1.067, 1.084,
   1.066, 0.955, 1.116, 0.910, 0.814, 0.752, 0.783, 0.394, 0.243, 0.627, 
   0.627  // gamma[31] = gamma[30]
);

vec3 handheld_eotf(vec3 color)
{
   /*
   vec3 denormalized_color = color * float(GAMMA_SAMPLES - 1);
   ivec3 idx_low = ivec3(floor(denormalized_color));
   ivec3 idx_high = ivec3(ceil(denormalized_color));
   vec3 weight = fract(denormalized_color);
   
   float gr = mix(GAMMA_R[idx_low.x], GAMMA_R[idx_high.x], weight.x);
   float gg = mix(GAMMA_G[idx_low.y], GAMMA_G[idx_high.y], weight.y);
   float gb = mix(GAMMA_B[idx_low.z], GAMMA_B[idx_high.z], weight.z);
   */

   // gamma fitting for x in [0.05, 0.8]
   float gr = 0.75 * pow(color.x, -0.36);                            // R^2 = 0.886
   float gg = 1.03 * (color.y * color.y) - 1.78 * color.y + 1.25;    // R^2 = 0.967
   float gb = 0.87 * pow(color.z, -0.31);                            // R^2 = 0.883

   return pow(color, vec3(gr, gg, gb));
}

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.390470139319, 0.375458169316, 0.131729460778,
   0.260123256264, 0.532776844829, 0.207099898906,
   0.129995147233, 0.261236174552, 0.397474865335
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
   0.998397507758,   0.00201683618286, 0.0662094604064,
   0.0106658019316,  0.974749864629,   0.0198754563564,
   0.0158783241456, -0.0283604802683,  1.39870201098
);


const float WHITE_Y = 1.337146;
const vec3 BLACK_XYZ = vec3(0.302392, 0.314958, 0.281989);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
   0.757337119121,  -0.00178567149701, 0.0459532100933,
   0.00249437130211, 0.750740324888,   0.0140558694563,
   0.0106568397365, -0.0188450944148,  1.03420748482
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