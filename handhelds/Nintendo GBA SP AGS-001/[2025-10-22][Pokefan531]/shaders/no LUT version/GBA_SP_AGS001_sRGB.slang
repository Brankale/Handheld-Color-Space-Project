#version 450

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
   //float BitDepth;
   float ChromaticAdaptation;
   float ImproveContrast;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
};

//#pragma parameter BitDepth "Screen bit depth" 5.0 1.0 12.0 1.0
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

const float GAMMA_RED[GAMMA_SAMPLES] = float[](
   1.654, // gamma[0] = gamma[1]
   1.654, 2.281, 2.265, 2.402, 2.319, 2.316, 2.262, 2.240, 2.280, 2.289,
   2.245, 2.280, 2.352, 2.408, 2.452, 2.528, 2.589, 2.671, 2.762, 2.828,
   2.909, 2.990, 3.100, 3.170, 3.229, 3.332, 3.502, 3.467, 3.077, 2.679,
   2.679  // gamma[31] = gamma[30]
);

const float GAMMA_GREEN[GAMMA_SAMPLES] = float[](
   1.767, // gamma[0] = gamma[1]
   1.767, 1.733, 1.838, 1.873, 1.900, 1.854, 1.804, 1.805, 1.819, 1.846,
   1.868, 1.890, 1.946, 2.003, 2.074, 2.123, 2.206, 2.274, 2.360, 2.437,
   2.507, 2.591, 2.687, 2.760, 2.828, 2.933, 3.117, 3.074, 2.758, 2.480, 
   2.480  // gamma[31] = gamma[30]
);

const float GAMMA_BLUE[GAMMA_SAMPLES]  = float[](
   2.069, // gamma[0] = gamma[1]
   2.069, 5.324, 5.324, 5.324, 5.324, 5.324, 5.324, 5.324, 5.324, 3.564,
   3.056, 3.029, 3.041, 3.052, 2.991, 3.062, 3.057, 3.139, 3.179, 3.204,
   3.267, 3.310, 3.412, 3.457, 3.486, 3.588, 3.754, 3.789, 3.410, 3.075, 
   3.075  // gamma[31] = gamma[30]
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
   float gr = get_handheld_gamma_for_color(color.x, GAMMA_RED);
   float gg = get_handheld_gamma_for_color(color.y, GAMMA_GREEN);
   float gb = get_handheld_gamma_for_color(color.z, GAMMA_BLUE);
   return pow(color, vec3(gr, gg, gb));
}

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.457763768564, 0.398987450294, 0.107993440399,
   0.293675562257, 0.529541990512, 0.176782447231,
   0.130185745534, 0.199858879518, 0.362270576041
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    0.939812649899, -0.0326690966101, 0.110420497555,
   -0.0377328521735, 1.01140916393, 0.0361011915427,
    0.0223676693816, -0.0378107543673, 1.59651183999
);


const float WHITE_Y = 4.946332;
const vec3 BLACK_XYZ = vec3(0.514237, 0.612946, 0.659477);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    0.837007903334, -0.0200280871269, 0.0787346559391,
   -0.0218721503496, 0.877993902482, 0.0254739483185,
    0.0163220076967, -0.0278207620789, 1.30625192056
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

   // pre processing: quantization (very imprecise DON'T USE IT)
   //handheld_rgba = floor(handheld_rgba * float(1 << BIT_DEPTH)) / float(1 << BIT_DEPTH);

   // 1. handheld colorspace EOTF
   vec3 handheld_linearized_rgb = handheld_eotf(handheld_rgba.rgb);

   // 2. handheld linearized RGB -> handheld XYZ
   vec3 handheld_xyz = vec3(
      (HANDHELD_RGB_LIN_TO_XYZ[0][0] * handheld_linearized_rgb.r) + (HANDHELD_RGB_LIN_TO_XYZ[0][1] * handheld_linearized_rgb.g) + (HANDHELD_RGB_LIN_TO_XYZ[0][2] * handheld_linearized_rgb.b),
      (HANDHELD_RGB_LIN_TO_XYZ[1][0] * handheld_linearized_rgb.r) + (HANDHELD_RGB_LIN_TO_XYZ[1][1] * handheld_linearized_rgb.g) + (HANDHELD_RGB_LIN_TO_XYZ[1][2] * handheld_linearized_rgb.b),
      (HANDHELD_RGB_LIN_TO_XYZ[2][0] * handheld_linearized_rgb.r) + (HANDHELD_RGB_LIN_TO_XYZ[2][1] * handheld_linearized_rgb.g) + (HANDHELD_RGB_LIN_TO_XYZ[2][2] * handheld_linearized_rgb.b)
   );

   if (ImproveContrast == 0.0)
      handheld_xyz += BLACK_XYZ_NORMALIZED;

   // 3. chromatic adaptation (handheld XYZ -> target XYZ)
   vec3 target_xyz = handheld_xyz;
   if (ChromaticAdaptation == 1.0)
      if (ImproveContrast == 0.0) {
         target_xyz = vec3(
            (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[0][0] * handheld_xyz.r) + (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[0][1] * handheld_xyz.g) + (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[0][2] * handheld_xyz.b),
            (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[1][0] * handheld_xyz.r) + (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[1][1] * handheld_xyz.g) + (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[1][2] * handheld_xyz.b),
            (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[2][0] * handheld_xyz.r) + (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[2][1] * handheld_xyz.g) + (CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK[2][2] * handheld_xyz.b)
         ); 
      } else {
         target_xyz = vec3(
            (CAT_BRADFORD_HANDHELD_TO_SRGB[0][0] * handheld_xyz.r) + (CAT_BRADFORD_HANDHELD_TO_SRGB[0][1] * handheld_xyz.g) + (CAT_BRADFORD_HANDHELD_TO_SRGB[0][2] * handheld_xyz.b),
            (CAT_BRADFORD_HANDHELD_TO_SRGB[1][0] * handheld_xyz.r) + (CAT_BRADFORD_HANDHELD_TO_SRGB[1][1] * handheld_xyz.g) + (CAT_BRADFORD_HANDHELD_TO_SRGB[1][2] * handheld_xyz.b),
            (CAT_BRADFORD_HANDHELD_TO_SRGB[2][0] * handheld_xyz.r) + (CAT_BRADFORD_HANDHELD_TO_SRGB[2][1] * handheld_xyz.g) + (CAT_BRADFORD_HANDHELD_TO_SRGB[2][2] * handheld_xyz.b)
         ); 
      }
      

   // 4. target XYZ -> target linearized RGB
   vec3 target_linearized_rgb = vec3(
      (SRGB_XYZ_TO_RGB_LIN_MTX[0][0] * target_xyz.r) + (SRGB_XYZ_TO_RGB_LIN_MTX[0][1] * target_xyz.g) + (SRGB_XYZ_TO_RGB_LIN_MTX[0][2] * target_xyz.b),
      (SRGB_XYZ_TO_RGB_LIN_MTX[1][0] * target_xyz.r) + (SRGB_XYZ_TO_RGB_LIN_MTX[1][1] * target_xyz.g) + (SRGB_XYZ_TO_RGB_LIN_MTX[1][2] * target_xyz.b),
      (SRGB_XYZ_TO_RGB_LIN_MTX[2][0] * target_xyz.r) + (SRGB_XYZ_TO_RGB_LIN_MTX[2][1] * target_xyz.g) + (SRGB_XYZ_TO_RGB_LIN_MTX[2][2] * target_xyz.b)
   );   

   // 5. target colorspace OETF
   vec3 target_rgb = srgb_oetf(target_linearized_rgb);

   // post processing: out of gamut
   if (DebugOutOfGamut == 1.0)
      target_rgb = compute_out_of_gamut(target_rgb);
   
   FragColor = vec4(target_rgb, handheld_rgba.w);
}
