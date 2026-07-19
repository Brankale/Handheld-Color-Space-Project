#version 450

// Portable (standalone) variant of TEMPLATE_HDR10.slang.
// All shared code is inlined — no external #include dependencies.
// Copy this single file anywhere and it will work as-is.
//
// HDR10 output (A2B10G10R10_UNORM_PACK32, PQ/ST 2084, Rec. 2020).
// Requires RetroArch with an HDR10-capable display (Windows D3D11/D3D12).
// (doc: "A2B10G10R10_UNORM_PACK32 — HDR10-encoded (PQ) values can be
//        written directly. Linear values must be converted to PQ before output.")
// Debug gamut tools are excluded: in PQ space, SDR values (0–1) map to
// near-black; the red OOG indicator (1.0) would equal 10 000 nits.

#pragma name TEMPLATE_HDR10_portable
#pragma format A2B10G10R10_UNORM_PACK32

layout(set = 0, binding = 0, std140) uniform UBO
{
    mat4 MVP;
};

layout(push_constant) uniform Push
{
    float ChromaticAdaptation;
    float ImproveContrast;
    float PeakLuminance;
    float RedScale;
    float GreenScale;
    float BlueScale;
};

#pragma parameter ChromaticAdaptation "D65 illuminant (0=OFF,1=CIECAT16,2=CIECAM16)" 0.0 0.0 2.0 1.0
#pragma parameter ImproveContrast "Remove backlight distortion (0=OFF,1=ON)" 1.0 0.0 1.0 1.0
#pragma parameter PeakLuminance "HDR10 peak luminance nits" 1000.0 100.0 10000.0 100.0
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

const int GAMMA_SAMPLES = 32;

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

const float WHITE_Y = 199.22644;
const vec3 BLACK_XYZ = vec3(0.332459, 0.318527, 0.545375);
const vec3 BLACK_XYZ_NORMALIZED = BLACK_XYZ / WHITE_Y;
const vec3 W_SRC = vec3(0.98985718, 1.0, 1.28699600);

// ============================================================
// end device-specific data
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
// transfer_functions.h (inlined — pq_oetf only)
// ============================================================

// PQ (ST.2084) OETF — for HDR10 output
// linear    : [0, 1] where 1.0 = white_y nits (handheld peak white)
// white_y   : handheld peak white luminance in cd/m² (= WHITE_Y)
// peak_nits : output display peak luminance in nits
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

// ============================================================

void main()
{
    // Ambient adapting luminance: 20% gray world assumption (single-pass, no prepass).
    float L_A = 0.2 * WHITE_Y;

    vec4 handheld_rgba = texture(Source, vTexCoord);

    if ((RedScale + GreenScale + BlueScale) > 0.0) {
        handheld_rgba = vec4(
            vTexCoord.x * RedScale,
            vTexCoord.x * GreenScale,
            vTexCoord.x * BlueScale,
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

    vec3 target_linear_rgb = REC2020_XYZ_TO_RGB_LIN_MTX * adapted_xyz;

    FragColor = vec4(pq_oetf(target_linear_rgb, WHITE_Y, PeakLuminance), handheld_rgba.w);
}
