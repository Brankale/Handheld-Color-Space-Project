// ============================================================
// Output colour space: XYZ (D65) -> linear RGB matrices
//
// All four target spaces use D65 as white point, so the
// chromatic-adaptation step targets D65 uniformly.
// Matrices are column-major (GLSL convention):
//   column n = contributions of the n-th XYZ input to R, G, B.
// ============================================================

// D65 white point in XYZ (reference target for chromatic adaptation)
const vec3 W_REF = vec3(0.95045593, 1.0, 1.08905775);

// sRGB / Rec.709 (IEC 61966-2-1)
const mat3 SRGB_XYZ_TO_RGB_LIN_MTX = mat3(
    3.2406255, -0.9689307,  0.0557101,   // column 0 (X -> R, G, B)
   -1.5372080,  1.8757561, -0.2040211,   // column 1 (Y -> R, G, B)
   -0.4986286,  0.0415175,  1.0569959    // column 2 (Z -> R, G, B)
);

// Display P3 (D65 white point, sRGB transfer function — ICC / DCI P3-D65)
const mat3 DISPLAY_P3_XYZ_TO_RGB_LIN_MTX = mat3(
    2.4934969, -0.9313836, -0.4027108,   // column 0 (X -> R, G, B)
   -0.8294890,  1.7626641,  0.0236247,   // column 1 (Y -> R, G, B)
    0.0358458, -0.0761724,  0.9568845    // column 2 (Z -> R, G, B)
);

// Adobe RGB (1998) (D65 white point, gamma 2.2 transfer — ICC)
const mat3 ADOBE_RGB_XYZ_TO_RGB_LIN_MTX = mat3(
    2.0413690, -0.9692660,  0.0134474,   // column 0 (X -> R, G, B)
   -0.5649464,  1.8760108, -0.1183897,   // column 1 (Y -> R, G, B)
   -0.3446944,  0.0415560,  1.0154096    // column 2 (Z -> R, G, B)
);

// Rec. 2020 (D65 white point — ITU-R BT.2020)
const mat3 REC2020_XYZ_TO_RGB_LIN_MTX = mat3(
    1.7166512, -0.6666844,  0.0176399,   // column 0 (X -> R, G, B)
   -0.3556708,  1.6164812, -0.0427706,   // column 1 (Y -> R, G, B)
   -0.2533663,  0.0157685,  0.9421031    // column 2 (Z -> R, G, B)
);
