#version 450

layout(set = 0, binding = 0, std140) uniform UBO
{
   mat4 MVP;
   float Mode;
   float Simulate45Degrees;
   float DebugOutOfGamut;
   float RedScale;
   float GreenScale;
   float BlueScale;
};

#pragma parameter Simulate45Degrees "[Test] Simulate light at 45° angle" 0.0 0.0 1.0 1.0
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


// Calculates a single scalar multiplier for luminance based on the chromatic composition
// of the color. The resulting float should be multiplied with the XYZ coordinates.
float calculateLuminanceScale(vec3 rgb, float k_c, float k_m, float k_y, float k_gray)
{
   // 1. Find the maximum channel value (Value in HSV)
   float maxVal = max(rgb.r, max(rgb.g, rgb.b));

   // If the color is black, avoid division by zero. Black has 0 luminance anyway.
   if (maxVal <= 0.0)
      return 1.0;

   // 2. Normalize the color to separate its pure hue/saturation from its lightness.
   // A dark yellow (0.5, 0.5, 0) becomes pure yellow (1.0, 1.0, 0).
   vec3 c = rgb / maxVal;

   // 3. Isolate the neutral axis on the normalized color
   float neutral = min(c.r, min(c.g, c.b));

   // 4. Remove neutral to find the pure hues
   vec3 p = c - neutral;

   // 5. Calculate the proportions of Yellow, Cyan, and Magenta
   float yellow  = min(p.r, p.g);
   float cyan    = min(p.g, p.b);
   float magenta = min(p.b, p.r);

   // 6. Calculate the final scalar multiplier.
   // The base multiplier is 1.0 (for pure Red, Green, Blue).
   // We add the negative deltas introduced by the secondary and neutral components.
   float scale = 1.0  
      + yellow  * (k_y - 1.0)
      + cyan    * (k_c - 1.0)
      + magenta * (k_m - 1.0)
      + neutral * (k_gray - 1.0);

   return scale;
}

const int DEGREE = 3;
const float K_R[DEGREE + 1] = float[](1.36979727, -4.14270587, 8.01244043, -5.47643094);
const float K_G[DEGREE + 1] = float[](1.43777549, -3.52940120, 5.78584678, -3.49844932);
const float K_B[DEGREE + 1] = float[](1.23189191, -2.20101067, 3.22390865, -2.24645952);


vec3 handheld_eotf(vec3 color)
{
   // gamma functions interpolated
   float gr = K_R[3] * pow(color.r, 3.0) + K_R[2] * pow(color.r, 2.0) + K_R[1] * color.r + K_R[0];
   float gg = K_G[3] * pow(color.g, 3.0) + K_G[2] * pow(color.g, 2.0) + K_G[1] * color.g + K_G[0];
   float gb = K_B[3] * pow(color.b, 3.0) + K_B[2] * pow(color.b, 2.0) + K_B[1] * color.b + K_B[0];

   if (Simulate45Degrees == 0.0) {
      return pow(color, vec3(gr, gg, gb));
   } else {
      return pow(color, vec3(gr, gg, gb) + vec3(1.05));
   }
}

// row major matrix

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
   0.438125278,   0.384985008,   0.127082453,
   0.293906497,   0.559309610,   0.195290753,
   0.152115685,   0.321358983,   0.432852544
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
   vec3 handheld_xyz = transpose(HANDHELD_RGB_LIN_TO_XYZ) * handheld_linearized_rgb;

   // C M Y K luminance scaling factors
   // These scaling factors are calculated to minimize the CAM16-UCS delta E between the estimated values and the measured values.
   handheld_xyz = calculateLuminanceScale(
      handheld_linearized_rgb, 
      0.965647, 
      0.898962, 
      0.944302, 
      0.953737
   ) * handheld_xyz;

   // 3. chromatic adaptation (handheld XYZ -> target XYZ)
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
