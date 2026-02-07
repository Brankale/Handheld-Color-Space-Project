#version 450

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
   float ChromaticAdaptation;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
};

#pragma parameter ChromaticAdaptation "Chromatic Adaptation (0 = OFF, 1 = D65)" 0.0 0.0 1.0 1.0
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
   1.741,
   1.741, 1.978, 2.084, 2.138, 2.168, 2.185, 2.193, 2.248, 2.268, 2.281,
   2.296, 2.317, 2.335, 2.346, 2.372, 2.388, 2.405, 2.416, 2.440, 2.467,
   2.497, 2.524, 2.553, 2.662, 2.715, 2.753, 2.836, 2.922, 3.080, 3.272,
   3.272
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
   1.739,
   1.739, 1.955, 2.043, 2.083, 2.101, 2.107, 2.101, 2.148, 2.157, 2.158,
   2.161, 2.172, 2.177, 2.172, 2.185, 2.184, 2.187, 2.180, 2.184, 2.181,
   2.189, 2.191, 2.195, 2.260, 2.264, 2.247, 2.280, 2.286, 2.346, 2.351,
   2.351
);

const float GAMMA_B[GAMMA_SAMPLES]  = float[](
   1.659,
   1.659, 1.840, 1.893, 1.903, 1.891, 1.868, 1.831, 1.848, 1.830, 1.794,
   1.767, 1.757, 1.729, 1.692, 1.669, 1.627, 1.594, 1.538, 1.496, 1.437,
   1.401, 1.342, 1.281, 1.246, 1.159, 1.043, 0.956, 0.846, 0.694, 0.507,
   0.507
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
    0.38154552,   0.35864595,   0.21545496,
    0.21216461,   0.65123694,   0.13659845,
    0.03269853,   0.07298532,   1.08431300
);

const mat3 CAT_BRADFORD_HANDHELD_TO_SRGB = mat3(
     1.01054329,  0.00420323, -0.01636087,
     0.00460884,  1.00189878, -0.00529682,
    -0.00338694,  0.00577018,  0.91304804
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
