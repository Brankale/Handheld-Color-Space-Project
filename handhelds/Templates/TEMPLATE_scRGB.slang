#version 450

// scRGB output (R16G16B16A16_SFLOAT, linear Rec.709, extended range).
// Requires RetroArch with HDR enabled (Windows D3D11/D3D12 backend).
// The OS compositor converts scRGB to the display's HDR format automatically.
// PaperWhiteNits sets the nit level that maps to scRGB 1.0.
// (doc: "R16G16B16A16_SFLOAT — Linear values can be written directly")

#pragma name TEMPLATE_scRGB
#pragma format R16G16B16A16_SFLOAT

layout(set = 0, binding = 0, std140) uniform UBO
{
    mat4 MVP;
};

layout(push_constant) uniform Push
{
    float ChromaticAdaptation;
    float ImproveContrast;
    float PaperWhiteNits;
    float DebugOutOfGamut;
    float DebugDeltaEMax;
    float RedScale;
    float GreenScale;
    float BlueScale;
};

#pragma parameter ChromaticAdaptation "D65 illuminant (0=OFF,1=CIECAT16,2=CIECAM16)" 0.0 0.0 2.0 1.0
#pragma parameter ImproveContrast "Remove backlight distortion (0=OFF,1=ON)" 1.0 0.0 1.0 1.0
#pragma parameter PaperWhiteNits "scRGB paper white nits (SDR ref white)" 203.0 80.0 400.0 1.0
#pragma parameter DebugOutOfGamut "[Debug] 0=OFF 1=clip 2=deltaE heat" 0.0 0.0 2.0 1.0
#pragma parameter DebugDeltaEMax "[Debug] deltaE00 = full red in heatmap" 3.0 1.0 50.0 1.0
#pragma parameter RedScale "[Debug] RED scale" 0.0 0.0 1.0 1.0
#pragma parameter GreenScale "[Debug] GREEN scale" 0.0 0.0 1.0 1.0
#pragma parameter BlueScale "[Debug] BLUE scale" 0.0 0.0 1.0 1.0

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

// ============================================================
// Device-specific data — Nintendo DS Lite Top [2023-07-28][Pokefan531]
// Replace ALL values in this section when targeting a different device.
// ============================================================

// Number of entries in the per-channel gamma lookup table.
// Duplicate the first and last entries for boundary handling.
const int GAMMA_SAMPLES = 32;

// Measured per-channel gamma exponents at GAMMA_SAMPLES evenly
// spaced input levels over [0, 1].
const float GAMMA_R[GAMMA_SAMPLES] = float[](
    2.0767131,
    2.0767131,  2.13710327, 2.16192389, 2.174535,   2.18082821, 2.17736862, 2.18590351, 2.19329852, 2.20582927, 2.21727465,
    2.22441409, 2.23665199, 2.24936615, 2.2554995,  2.28611537, 2.29853204, 2.31237332, 2.32314759, 2.34484611, 2.38284314,
    2.39525252, 2.41673623, 2.46492914, 2.48669639, 2.52784711, 2.56367325, 2.63291794, 2.73672018, 2.85988438, 3.01728606,
    3.01728606
);

const float GAMMA_G[GAMMA_SAMPLES] = float[](
    2.03869367,
    2.03869367, 2.10226738, 2.12656252, 2.1376844,  2.14225133, 2.13764196, 2.14233572, 2.14473351, 2.15260244, 2.15837463,
    2.16270391, 2.16922457, 2.17524887, 2.17353028, 2.19437723, 2.19713962, 2.20355689, 2.2006526,  2.20930412, 2.23443641,
    2.22931336, 2.23224255, 2.26851194, 2.25249423, 2.25892754, 2.26643039, 2.29540508, 2.35013924, 2.37799253, 2.36084201,
    2.36084201
);

const float GAMMA_B[GAMMA_SAMPLES] = float[](
    1.91615459,
    1.91615459, 1.94367982, 1.93405157, 1.91393789, 1.88824277, 1.8507469,  1.82631097, 1.80331521, 1.77831729, 1.75575943,
    1.72070312, 1.69625874, 1.66332715, 1.62494244, 1.61367298, 1.56844866, 1.53154955, 1.48234401, 1.43629385, 1.40338909,
    1.33513557, 1.27789131, 1.26039319, 1.13948331, 1.05192119, 0.99264375, 0.8816358,  0.84398413, 0.66308729, 0.35011463,
    0.35011463
);

// Handheld linear RGB -> CIE XYZ matrix (column-major).
// Each column is the XYZ chromaticity of the R, G, B primary respectively.
const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
    0.39223169,  0.21674235,  0.0364544,   // column 0 (R -> X, Y, Z)
    0.36370755,  0.65064109,  0.06923906,  // column 1 (G -> X, Y, Z)
    0.23391794,  0.13261656,  1.18130254   // column 2 (B -> X, Y, Z)
);

// Peak white luminance of the handheld display in cd/m² (measured).
const float WHITE_Y = 199.22644;

// Absolute XYZ of the measured black level (not normalised).
const vec3 BLACK_XYZ = vec3(0.332459, 0.318527, 0.545375);

const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;

// Handheld source white point in XYZ.
// = column sums of HANDHELD_RGB_LIN_TO_XYZ (equal-energy white input).
const vec3 W_SRC = vec3(0.98985718, 1.0, 1.28699600);

// ============================================================
// end device-specific data
// ============================================================

// Handheld display EOTF — linearises the encoded signal using
// an interpolated per-channel gamma lookup table.
vec3 handheld_eotf(vec3 color)
{
    color = clamp(color, 0.0, 1.0);
    vec3 denormalized = color * float(GAMMA_SAMPLES - 1);
    ivec3 idx_low  = ivec3(floor(denormalized));
    ivec3 idx_high = ivec3(ceil(denormalized));
    vec3 weight    = fract(denormalized);

    float gr = mix(GAMMA_R[idx_low.x], GAMMA_R[idx_high.x], weight.x);
    float gg = mix(GAMMA_G[idx_low.y], GAMMA_G[idx_high.y], weight.y);
    float gb = mix(GAMMA_B[idx_low.z], GAMMA_B[idx_high.z], weight.z);

    return pow(color, vec3(gr, gg, gb));
}

// Include order matters: color_matrices.h defines W_REF used by
// chromatic_adaptation.h, which in turn uses W_SRC defined above.
#include "include/color_matrices.h"
#include "include/chromatic_adaptation.h"
#include "include/transfer_functions.h"
#include "include/debug_utils.h"

void main()
{
    // Ambient adapting luminance: 20% gray world assumption (single-pass, no prepass).
    float L_A = 0.2 * WHITE_Y;

    // Read source pixel
    vec4 handheld_rgba = texture(Source, vTexCoord);

    // Debug: colour-channel ramp sweep
    if ((RedScale + GreenScale + BlueScale) > 0.0) {
        handheld_rgba = vec4(
            vTexCoord.x * RedScale,
            vTexCoord.x * GreenScale,
            vTexCoord.x * BlueScale,
            1.0
        );
    }

    // 1. Handheld display EOTF -> linear light
    vec3 handheld_linear = handheld_eotf(handheld_rgba.rgb);

    // 2. Handheld linear RGB -> XYZ
    vec3 handheld_xyz = HANDHELD_RGB_LIN_TO_XYZ * handheld_linear;

    // 3. Optional black-level correction (disabled when ImproveContrast = 1)
    if (ImproveContrast == 0.0)
        handheld_xyz += BLACK_XYZ_NORMALIZED;

    // 4. Chromatic adaptation: handheld white -> D65
    vec3 adapted_xyz = handheld_xyz;
    if (ChromaticAdaptation == 1.0)
        adapted_xyz = ciecat16(handheld_xyz);
    else if (ChromaticAdaptation == 2.0)
        adapted_xyz = ciecam16(handheld_xyz, get_degree_of_adaptation(L_A));

    // 5. XYZ -> sRGB linear (scRGB uses Rec.709 primaries)
    // (doc: "R16G16B16A16_SFLOAT — 16-bit, Rec. 709, Linear (scRGB)")
    vec3 target_linear_rgb = SRGB_XYZ_TO_RGB_LIN_MTX * adapted_xyz;

    // 6. Debug: gamut visualisation (applied before scRGB scaling)
    vec3 display_rgb = target_linear_rgb;
    if      (DebugOutOfGamut == 1.0) display_rgb = compute_out_of_gamut(target_linear_rgb, target_linear_rgb);
    else if (DebugOutOfGamut == 2.0) display_rgb = compute_out_of_gamut_deltaE(target_linear_rgb, target_linear_rgb, DebugDeltaEMax);

    // 7. scRGB output: scale linear [0,1] to absolute nits
    // scRGB 1.0 = PaperWhiteNits; handheld white = WHITE_Y nits
    FragColor = vec4(display_rgb * (WHITE_Y / PaperWhiteNits), handheld_rgba.w);
}
