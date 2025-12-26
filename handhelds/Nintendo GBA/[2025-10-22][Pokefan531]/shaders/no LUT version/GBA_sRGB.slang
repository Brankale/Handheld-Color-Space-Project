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
   1.904, // gamma[0] = gamma[1]
   1.904, 1.708, 1.910, 2.056, 2.165, 2.281, 2.2815, 2.282, 2.473, 2.401,
   2.532, 2.522, 2.586, 2.626, 2.781, 2.884, 2.919, 3.099, 3.199, 3.247,
   3.413, 3.481, 3.657, 3.825, 3.889, 4.056, 4.377, 4.581, 4.067, 3.916,
   3.916  // gamma[31] = gamma[30]
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   2.304, // gamma[0] = gamma[1]
   2.304, 2.692, 2.161, 2.356, 2.364, 2.520, 2.459, 2.398, 2.412, 2.420,
   2.429, 2.432, 2.527, 2.684, 2.691, 2.756, 2.886, 2.975, 3.163, 3.309,
   3.368, 3.577, 3.741, 3.876, 4.088, 4.298, 4.669, 4.690, 4.574, 4.222,  
   4.222  // gamma[31] = gamma[30]
);

const float GAMMA_B[GAMMA_SAMPLES] = float[](
   1.279, // gamma[0] = gamma[1]
   1.279, 1.480, 1.806, 1.944, 2.431, 2.430, 2.468, 2.505, 2.688, 2.634,
   2.807, 2.740, 2.830, 2.754, 2.984, 3.076, 2.993, 3.195, 3.188, 3.144,
   3.415, 3.352, 3.440, 3.685, 3.612, 3.680, 3.814, 3.934, 3.195, 3.112, 
   3.112  // gamma[31] = gamma[30]
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

   // gamma curve fitting for x in [0.05, 0.8]
   float gr = 7.5825 * (color.x * color.x * color.x) - 8.1241 * (color.x * color.x) + 4.7556 * color.x + 1.5203;        // R² = 0.9913
   float gg = 0.7103 * (color.y * color.y * color.y) + 4.1803 * (color.y * color.y) - 1.9739 * color.y + 2.5991;        // R² = 0.9666
   float gb = 13.8330 *(color.z * color.z * color.z) - 19.3738 * (color.z * color.z) + 10.1671 * color.z + 0.9957;      // R² = 0.9712
   
   return pow(color, vec3(gr, gg, gb));
}

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.427313436084, 0.345215119328, 0.132100954413,
   0.286434714607, 0.507734531257, 0.205830754136,
   0.174987963445, 0.25827860705,  0.467085882964
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
   1.00855387127, 0.00705743076042, 0.0344652829859,
   0.0148087961079, 0.97773177157, 0.00985364612739,
   0.00895124615429, -0.0163448010231, 1.21875048615
);


const float WHITE_Y = 1.157845;
const vec3 BLACK_XYZ = vec3(0.195024, 0.19176, 0.20561);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB_WITH_BLACK = mat3(
   0.832870533683,    0.00090286363876, 0.0249758701734,
   0.00424230409107,  0.823512283492,   0.00748587453091,
   0.00600591958223, -0.0107356895586,  0.983918439602
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
