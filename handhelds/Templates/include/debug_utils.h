// ============================================================
// Debug visualisation utilities
// ============================================================

// OKLab distance threshold shared by both gamut-debug modes (~1 CIEDE2000 unit).
// Values below this are treated as in-gamut, filtering sub-JND floating-point noise.
const float GAMUT_DE_THRESHOLD = 0.01;

// OKLab conversion from sRGB linear (Björn Ottosson, 2020).
// Treats the input as sRGB-linear — valid approximation for sRGB,
// P3 and Adobe RGB; slightly off for Rec.2020, but acceptable for
// debug purposes. sign/abs are used to handle negative values from
// out-of-gamut inputs without producing NaN from pow().
vec3 srgb_linear_to_oklab(vec3 rgb)
{
    const mat3 SRGB_TO_LMS = mat3(
        0.4122214708, 0.2119034982, 0.0883024619,  // column 0 (R)
        0.5363325363, 0.6806995451, 0.2817188376,  // column 1 (G)
        0.0514459929, 0.1073969566, 0.6299787005   // column 2 (B)
    );
    const mat3 LMS_TO_OKLAB = mat3(
        0.2104542553,  1.9779984951,  0.0259040371,  // column 0 (l)
        0.7936177850, -2.4285922050,  0.7827717662,  // column 1 (m)
       -0.0040720468,  0.4505937099, -0.8086757660   // column 2 (s)
    );
    vec3 lms   = SRGB_TO_LMS * rgb;
    vec3 lms_g = sign(lms) * pow(abs(lms), vec3(1.0 / 3.0));
    return LMS_TO_OKLAB * lms_g;
}

// Binary out-of-gamut visualisation.
// Uses the same OKLab ΔE threshold as the heatmap mode — both modes
// agree exactly on which pixels are out of gamut.
// In-gamut -> neutral grey, out-of-gamut -> red-tinted grey.
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

// Turbo colormap polynomial approximation.
// (Anton Mikhailov, Google LLC, 2019 — Apache-2.0 licence)
// t = 0 -> dark blue/purple  |  t = 1 -> dark red
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

// OKLab deltaE heatmap visualisation.
// Uses GAMUT_DE_THRESHOLD for the in/out-gamut boundary (same as clip mode).
// In-gamut -> neutral grey, out-of-gamut -> Turbo(dE00 / dE_max).
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
