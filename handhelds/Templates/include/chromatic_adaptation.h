// ============================================================
// CIECAT16 (CAT16, CIE 248:2022) Chromatic Adaptation
//
// PREREQUISITES — define before including this file:
//   const vec3 W_SRC   handheld source white point in XYZ
//   const vec3 W_REF   target white point in XYZ (from color_matrices.h)
// ============================================================

// CAT16 cone-response matrix and its inverse (column-major)
const mat3 M_CAT16 = mat3(
    0.401288, -0.250268, -0.002079,  // column 0 (X -> L, M, S)
    0.650173,  1.204414,  0.048952,  // column 1 (Y -> L, M, S)
   -0.051461,  0.045854,  0.953127   // column 2 (Z -> L, M, S)
);

const mat3 M_CAT16_INV = mat3(
    1.862068,  0.387527, -0.015841,  // column 0 (L -> X, Y, Z)
   -1.011255,  0.621447, -0.034123,  // column 1 (M -> X, Y, Z)
    0.149187, -0.008974,  1.049964   // column 2 (S -> X, Y, Z)
);

// LMS white points (computed from W_SRC / W_REF defined by the caller)
const vec3 LMS_W_SRC = M_CAT16 * W_SRC;
const vec3 LMS_W_REF = M_CAT16 * W_REF;

// Per-channel scale for full adaptation (degree D = 1): LMS_W_REF / LMS_W_SRC
const vec3 CIECAT16_FULL_SCALE = LMS_W_REF / LMS_W_SRC;

const float F = 0.8; // dark surround environment factor

// Degree of chromatic adaptation as a function of adapting luminance L_A (cd/m²)
float get_degree_of_adaptation(float L_A)
{
    float D = F * (1.0 - (1.0 / 3.6) * exp(-(L_A + 42.0) / 92.0));
    return clamp(D, 0.0, 1.0);
}

// CIECAT16 full chromatic adaptation (D = 1, complete adaptation)
vec3 ciecat16(vec3 xyz)
{
    return M_CAT16_INV * (CIECAT16_FULL_SCALE * (M_CAT16 * xyz));
}

// CIECAM16 partial chromatic adaptation (D in [0, 1])
vec3 ciecam16(vec3 xyz, float D)
{
    vec3 lms   = M_CAT16 * xyz;
    vec3 d_src = D / LMS_W_SRC + (1.0 - D);
    vec3 d_dst = D / LMS_W_REF + (1.0 - D);
    return M_CAT16_INV * ((d_src / d_dst) * lms);
}
