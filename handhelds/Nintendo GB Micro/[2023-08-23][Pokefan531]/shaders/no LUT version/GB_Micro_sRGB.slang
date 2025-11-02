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
   1.987, // gamma[0] = gamma[1]
   1.987, 2.100, 2.078, 1.999, 2.051, 2.106, 2.136, 2.151, 2.166, 2.177,
   2.205, 2.218, 2.242, 2.256, 2.271, 2.290, 2.305, 2.314, 2.333, 2.363,
   2.383, 2.396, 2.432, 2.448, 2.504, 2.534, 2.584, 2.632, 2.685, 2.743,
   2.743  // gamma[31] = gamma[30]
);

const float GAMMA_GREEN[GAMMA_SAMPLES] = float[](
   1.878, // gamma[0] = gamma[1]
   1.878, 1.972, 1.962, 1.900, 1.957, 2.017, 2.053, 2.075, 2.098, 2.113,
   2.146, 2.166, 2.195, 2.214, 2.235, 2.260, 2.280, 2.294, 2.318, 2.351,
   2.375, 2.393, 2.435, 2.452, 2.511, 2.544, 2.595, 2.640, 2.690, 2.729,
   2.729  // gamma[31] = gamma[30]
);

const float GAMMA_BLUE[GAMMA_SAMPLES]  = float[](
   2.673, // gamma[0] = gamma[1]
   2.673, 2.673, 2.378, 2.131, 2.127, 2.135, 2.113, 2.080, 2.053, 2.019,
   2.004, 1.975, 1.957, 1.924, 1.893, 1.862, 1.821, 1.772, 1.727, 1.688,
   1.633, 1.561, 1.503, 1.411, 1.338, 1.219, 1.086, 0.902, 0.659, 0.311,
   0.311  // gamma[31] = gamma[30]
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
   0.366645774426, 0.38924042231, 0.200934775614,
   0.239258756177, 0.565537333215, 0.195203910608,
   0.166628148042, 0.21931085149, 0.932932250802
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
    1.02898172299, 0.0119107472384, -0.0348829447139,
    0.0143705152728, 1.00146330104, -0.0115350997518,
   -0.00688463559115, 0.0115260887127, 0.822005199896
);



const vec3 BLACK_XYZ_NORMALIZED = vec3(0.00549878150266412, 0.00553600051934818, 0.00652387393808294);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
    1.0230015164, 0.0117054514261, -0.0345552152528,
    0.0140915987157, 0.996029423829, -0.0114190696469,
   -0.00683061492514, 0.0114423898027, 0.817941293736
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
