#version 450

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
   float Mode;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
};

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

float trilinearInterpolation(
   float v000, float v100, float v010, float v110, 
   float v001, float v101, float v011, float v111, 
   vec3 t
) {
   // x axis interpolation
   float c00 = mix(v000, v100, t.x);
   float c01 = mix(v001, v101, t.x);
   float c10 = mix(v010, v110, t.x);
   float c11 = mix(v011, v111, t.x);

   // y axis intepolation
   float c0 = mix(c00, c10, t.y);
   float c1 = mix(c01, c11, t.y);

   // z axis interpolation
   return mix(c0, c1, t.z);
}

vec3 handheld_eotf(vec3 color)
{
   // gamma functions interpolated
   float gr = -5.168 * pow(color.r, 3.0) + 7.722 * pow(color.r, 2.0) - 4.076 * color.r + 1.367;
   float gg = -3.500 * pow(color.g, 3.0) + 5.788 * pow(color.g, 3.0) - 3.531 * color.g + 1.438;
   float gb = -1.231 * pow(color.b, 3.0) + 2.016 * pow(color.b, 3.0) - 1.820 * color.b + 1.206;

   // 1.1 is to simulate a higher gamma for 45° angle. Use only for testing.
   vec3 XYZ = pow(color, vec3(gr, gg, gb) + vec3(1.1));

   // K, R, G, Y, B, M, C, W luminance scaling factors
   // These scaling factors are an approximated
   float scalingFactor = trilinearInterpolation(1.0, 1.0, 1.0, 0.9, 1.0, 0.9, 0.96, 0.92, color);

   return scalingFactor * XYZ;
}

// row major matrix
const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.431832006015918,	0.288933432229816,	0.165794478393771,
   0.37193718191221,	0.541635333762797,	0.306883657185095,
   0.123090189999307,	0.189126691014365,	0.419281734350017
);


// sRGB

const mat3 SRGB_XYZ_TO_RGB_LIN_MTX = mat3(
    3.2406255, -1.5372080, -0.4986286,
   -0.9689307,  1.8757561,  0.0415175,
    0.0557101, -0.2040211,  1.0569959
);

const vec3 BLACK_XYZ = vec3(0.165186, 0.167075, 0.133113); 

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
   vec3 handheld_xyz = HANDHELD_RGB_LIN_TO_XYZ * handheld_linearized_rgb;

   // 3. chromatic adaptation (handheld XYZ -> target XYZ)
//   vec3 target_xyz = handheld_xyz + BLACK_XYZ;
   vec3 target_xyz = handheld_xyz;


   // 4. target XYZ -> target linearized RGB
   vec3 target_linearized_rgb = transpose(SRGB_XYZ_TO_RGB_LIN_MTX) * target_xyz;

   // 5. target colorspace OETF
   vec3 target_rgb = srgb_oetf(target_linearized_rgb);

   // post processing: out of gamut
   if (DebugOutOfGamut == 1.0)
      target_rgb = compute_out_of_gamut(target_rgb);
   
   FragColor = vec4(target_rgb, handheld_rgba.w);
}
