#version 450

// Portable (standalone) variant of TEMPLATE_HDR.slang.
// All shared code is inlined — no external #include dependencies.
// Copy this single file anywhere and it will work as-is.
//
// NOTE: HDR output (PQ / HLG) requires RetroArch with HDR pipeline enabled
//       and an HDR-capable display. Set OutputTransfer = 3 for PQ (HDR10)
//       or 4 for HLG, and configure PeakLuminance to match your display.

#pragma name TEMPLATE_HDR_portable
#pragma format R16G16B16A16_SFLOAT

layout(set = 0, binding = 0, std140) uniform UBO
{
    mat4 MVP;
};

layout(push_constant) uniform Push
{
    float ChromaticAdaptation;
    float ImproveContrast;
    float OutputColorSpace;
    float OutputTransfer;
    float PeakLuminance;
    float DebugOutOfGamut;
    float DebugDeltaEMax;
    float RedScale;
    float GreenScale;
    float BlueScale;
    float DebugSplitScreen;
};

#pragma parameter ChromaticAdaptation "D65 illuminant (0=OFF,1=CIECAT16,2=CIECAM16)" 0.0 0.0 2.0 1.0
#pragma parameter ImproveContrast "Remove backlight distortion (0=OFF,1=ON)" 1.0 0.0 1.0 1.0
#pragma parameter OutputColorSpace "Gamut (0=sRGB,1=P3,2=Adobe,3=Rec2020)" 0.0 0.0 3.0 1.0
#pragma parameter OutputTransfer "OETF (0=sRGB,1=G2.2,2=G2.4,3=PQ,4=HLG)" 0.0 0.0 4.0 1.0
#pragma parameter PeakLuminance "HDR peak luminance nits (for PQ/HLG)" 1000.0 100.0 10000.0 100.0
#pragma parameter DebugOutOfGamut "[Debug] 0=OFF 1=clip 2=deltaE heat" 0.0 0.0 2.0 1.0
#pragma parameter DebugDeltaEMax "[Debug] deltaE00 = full red in heatmap" 3.0 1.0 50.0 1.0
#pragma parameter RedScale "[Debug] RED scale" 0.0 0.0 1.0 1.0
#pragma parameter GreenScale "[Debug] GREEN scale" 0.0 0.0 1.0 1.0
#pragma parameter BlueScale "[Debug] BLUE scale" 0.0 0.0 1.0 1.0
#pragma parameter DebugSplitScreen "[Debug] Average luminance" 0.0 0.0 1.0 1.0

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
// TODO: Replace the following with values measured from the
//       target handheld device and screen. Refer to an existing
//       device shader (e.g. NDS_Lite_Top_sRGB.slang) for the
//       expected format and scale of each constant.
// ============================================================

const int GAMMA_SAMPLES = 32; // TODO

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

const mat3 HANDHELD_RGB_LIN_TO_XYZ = mat3(
    0.39223169,  0.21674235,  0.0364544,   // column 0 (R -> X, Y, Z)
    0.36370755,  0.65064109,  0.06923906,  // column 1 (G -> X, Y, Z)
    0.23391794,  0.13261656,  1.18130254   // column 2 (B -> X, Y, Z)
);

const float WHITE_Y = 199.22644; // TODO
const vec3 BLACK_XYZ = vec3(0.332459, 0.318527, 0.545375); // TODO
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;
const vec3 W_SRC = vec3(0.98985718, 1.0, 1.28699600); // TODO

// ============================================================
// end TODO
// ============================================================

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

// ============================================================
// color_matrices.h (inlined)
// ============================================================

const vec3 W_REF = vec3(0.95045593, 1.0, 1.08905775);

const mat3 SRGB_XYZ_TO_RGB_LIN_MTX = mat3(
    3.2406255, -0.9689307,  0.0557101,
   -1.5372080,  1.8757561, -0.2040211,
   -0.4986286,  0.0415175,  1.0569959
);

const mat3 DISPLAY_P3_XYZ_TO_RGB_LIN_MTX = mat3(
    2.4934969, -0.9313836, -0.4027108,
   -0.8294890,  1.7626641,  0.0236247,
    0.0358458, -0.0761724,  0.9568845
);

const mat3 ADOBE_RGB_XYZ_TO_RGB_LIN_MTX = mat3(
    2.0413690, -0.9692660,  0.0134474,
   -0.5649464,  1.8760108, -0.1183897,
   -0.3446944,  0.0415560,  1.0154096
);

const mat3 REC2020_XYZ_TO_RGB_LIN_MTX = mat3(
    1.7166512, -0.6666844,  0.0176399,
   -0.3556708,  1.6164812, -0.0427706,
   -0.2533663,  0.0157685,  0.9421031
);

// ============================================================
// chromatic_adaptation.h (inlined)
// ============================================================

const mat3 M_CAT16 = mat3(
    0.401288, -0.250268, -0.002079,
    0.650173,  1.204414,  0.048952,
   -0.051461,  0.045854,  0.953127
);

const mat3 M_CAT16_INV = mat3(
    1.862068,  0.387527, -0.015841,
   -1.011255,  0.621447, -0.034123,
    0.149187, -0.008974,  1.049964
);

const vec3 LMS_W_SRC = M_CAT16 * W_SRC;
const vec3 LMS_W_REF = M_CAT16 * W_REF;
const vec3 CIECAT16_FULL_SCALE = LMS_W_REF / LMS_W_SRC;

const float F = 0.8;

float get_degree_of_adaptation(float L_A)
{
    float D = F * (1.0 - (1.0 / 3.6) * exp(-(L_A + 42.0) / 92.0));
    return clamp(D, 0.0, 1.0);
}

vec3 ciecat16(vec3 xyz)
{
    return M_CAT16_INV * (CIECAT16_FULL_SCALE * (M_CAT16 * xyz));
}

vec3 ciecam16(vec3 xyz, float D)
{
    vec3 lms   = M_CAT16 * xyz;
    vec3 d_src = D / LMS_W_SRC + (1.0 - D);
    vec3 d_dst = D / LMS_W_REF + (1.0 - D);
    return M_CAT16_INV * ((d_src / d_dst) * lms);
}

// ============================================================
// transfer_functions.h (inlined)
// ============================================================

vec3 srgb_oetf(vec3 color)
{
    vec3 linear    = 12.92 * color;
    vec3 nonlinear = 1.055 * pow(max(color, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
    bvec3 cond = lessThanEqual(color, vec3(0.0031308));
    return mix(nonlinear, linear, vec3(cond));
}

vec3 gamma_oetf(vec3 color, float exponent)
{
    return pow(max(color, vec3(0.0)), vec3(1.0 / exponent));
}

vec3 pq_oetf(vec3 linear, float white_y, float peak_nits)
{
    vec3 abs_nits = min(linear * white_y, vec3(peak_nits));
    vec3 Lp = abs_nits / 10000.0;

    const float m1 = 0.1593017578125;
    const float m2 = 78.84375;
    const float c1 = 0.8359375;
    const float c2 = 18.8515625;
    const float c3 = 18.6875;

    vec3 Lp_m1 = pow(max(Lp, vec3(0.0)), vec3(m1));
    return pow((c1 + c2 * Lp_m1) / (1.0 + c3 * Lp_m1), vec3(m2));
}

vec3 hlg_oetf(vec3 linear, float white_y, float peak_nits)
{
    vec3 normalized = linear * (white_y / peak_nits);

    const float a = 0.17883277;
    const float b = 0.28466892;
    const float c = 0.55991073;

    bvec3 lo       = lessThanEqual(normalized, vec3(1.0 / 12.0));
    vec3 low_part  = sqrt(3.0 * normalized);
    vec3 high_part = a * log(max(12.0 * normalized - b, vec3(1e-5))) + c;
    return clamp(mix(high_part, low_part, vec3(lo)), 0.0, 1.0);
}

// ============================================================
// debug_utils.h (inlined)
// ============================================================

const float GAMUT_DE_THRESHOLD = 0.01;

vec3 srgb_linear_to_oklab(vec3 rgb)
{
    const mat3 SRGB_TO_LMS = mat3(
        0.4122214708, 0.2119034982, 0.0883024619,
        0.5363325363, 0.6806995451, 0.2817188376,
        0.0514459929, 0.1073969566, 0.6299787005
    );
    const mat3 LMS_TO_OKLAB = mat3(
        0.2104542553,  1.9779984951,  0.0259040371,
        0.7936177850, -2.4285922050,  0.7827717662,
       -0.0040720468,  0.4505937099, -0.8086757660
    );
    vec3 lms   = SRGB_TO_LMS * rgb;
    vec3 lms_g = sign(lms) * pow(abs(lms), vec3(1.0 / 3.0));
    return LMS_TO_OKLAB * lms_g;
}

vec3 compute_out_of_gamut(vec3 linear_rgb, vec3 encoded_rgb)
{
    vec3 clamped = clamp(linear_rgb, 0.0, 1.0);
    float dE    = length(srgb_linear_to_oklab(linear_rgb) -
                         srgb_linear_to_oklab(clamped));
    float grey  = (encoded_rgb.r + encoded_rgb.g + encoded_rgb.b) / 3.0;
    return mix(vec3(grey),
               vec3(1.0, grey / 2.5, grey / 2.5),
               float(dE >= GAMUT_DE_THRESHOLD));
}

vec3 turbo_colormap(float t)
{
    const vec4 kRedVec4   = vec4( 0.13572138,   4.61539260, -42.66032258, 132.13108234);
    const vec4 kGreenVec4 = vec4( 0.09140261,   2.19418839,   4.84296658, -14.18503333);
    const vec4 kBlueVec4  = vec4( 0.10667330,  12.64194608, -60.58204836, 110.36276771);
    const vec2 kRedVec2   = vec2(-152.94239396,  59.28637943);
    const vec2 kGreenVec2 = vec2(   4.27729857,   2.82956604);
    const vec2 kBlueVec2  = vec2( -89.90310912,  27.34824973);

    t = clamp(t, 0.0, 1.0);
    vec4 v4 = vec4(1.0, t, t * t, t * t * t);
    vec2 v2 = v4.zw * v4.z;
    return clamp(vec3(
        dot(v4, kRedVec4)   + dot(v2, kRedVec2),
        dot(v4, kGreenVec4) + dot(v2, kGreenVec2),
        dot(v4, kBlueVec4)  + dot(v2, kBlueVec2)
    ), 0.0, 1.0);
}

vec3 compute_out_of_gamut_deltaE(vec3 linear_rgb, vec3 encoded_rgb, float dE_max)
{
    vec3 clamped = clamp(linear_rgb, 0.0, 1.0);
    float dE    = length(srgb_linear_to_oklab(linear_rgb) -
                         srgb_linear_to_oklab(clamped));
    float grey  = (encoded_rgb.r + encoded_rgb.g + encoded_rgb.b) / 3.0;
    if (dE < GAMUT_DE_THRESHOLD)
        return vec3(grey);
    return turbo_colormap(dE * 100.0 / dE_max);
}

// ============================================================

void main()
{
    float L_A = 0.2 * WHITE_Y;

    vec4 handheld_rgba = texture(Source, vTexCoord);

    if ((RedScale + GreenScale + BlueScale) > 0.0) {
        handheld_rgba = vec4(
            mix(0.0, vTexCoord.x, RedScale),
            mix(0.0, vTexCoord.x, GreenScale),
            mix(0.0, vTexCoord.x, BlueScale),
            1.0
        );
    }

    vec3 handheld_linear = handheld_eotf(handheld_rgba.rgb);
    vec3 handheld_xyz    = HANDHELD_RGB_LIN_TO_XYZ * handheld_linear;

    if (ImproveContrast == 0.0)
        handheld_xyz += BLACK_XYZ_NORMALIZED;

    vec3 adapted_xyz = handheld_xyz;
    if (ChromaticAdaptation == 1.0)
        adapted_xyz = ciecat16(handheld_xyz);
    else if (ChromaticAdaptation == 2.0)
        adapted_xyz = ciecam16(handheld_xyz, get_degree_of_adaptation(L_A));

    mat3 xyz_to_rgb;
    if      (OutputColorSpace == 1.0) xyz_to_rgb = DISPLAY_P3_XYZ_TO_RGB_LIN_MTX;
    else if (OutputColorSpace == 2.0) xyz_to_rgb = ADOBE_RGB_XYZ_TO_RGB_LIN_MTX;
    else if (OutputColorSpace == 3.0) xyz_to_rgb = REC2020_XYZ_TO_RGB_LIN_MTX;
    else                              xyz_to_rgb = SRGB_XYZ_TO_RGB_LIN_MTX;
    vec3 target_linear_rgb = xyz_to_rgb * adapted_xyz;

    vec3 target_rgb;
    if      (OutputTransfer == 1.0) target_rgb = gamma_oetf(target_linear_rgb, 2.2);
    else if (OutputTransfer == 2.0) target_rgb = gamma_oetf(target_linear_rgb, 2.4);
    else if (OutputTransfer == 3.0) target_rgb = pq_oetf(target_linear_rgb, WHITE_Y, PeakLuminance);
    else if (OutputTransfer == 4.0) target_rgb = hlg_oetf(target_linear_rgb, WHITE_Y, PeakLuminance);
    else                            target_rgb = srgb_oetf(target_linear_rgb);

    if      (DebugOutOfGamut == 1.0) target_rgb = compute_out_of_gamut(target_linear_rgb, target_rgb);
    else if (DebugOutOfGamut == 2.0) target_rgb = compute_out_of_gamut_deltaE(target_linear_rgb, target_rgb, DebugDeltaEMax);

    if (DebugSplitScreen == 1.0) {
        if (vTexCoord.x < 0.2 && vTexCoord.y < 0.2)
            target_rgb = vec3(0.2);
    }

    FragColor = vec4(target_rgb, handheld_rgba.w);
}
