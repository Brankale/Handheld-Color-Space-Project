// ============================================================
// Output transfer functions (OETF)
// ============================================================

// sRGB OETF (IEC 61966-2-1)
vec3 srgb_oetf(vec3 color)
{
    vec3 linear    = 12.92 * color;
    vec3 nonlinear = 1.055 * pow(max(color, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
    bvec3 cond = lessThanEqual(color, vec3(0.0031308));
    return mix(nonlinear, linear, vec3(cond));
}

// Pure power-law OETF — pass 2.2 for Adobe RGB, 2.4 for BT.1886
vec3 gamma_oetf(vec3 color, float exponent)
{
    return pow(max(color, vec3(0.0)), vec3(1.0 / exponent));
}

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

// HLG (ARIB STD-B67) OETF — for broadcast HDR output
// linear    : [0, 1] where 1.0 = white_y nits (handheld peak white)
// white_y   : handheld peak white luminance in cd/m²
// peak_nits : HLG reference display peak in nits (typically 1000.0)
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
