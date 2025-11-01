import numpy
import colour
import sys
import json
import matplotlib.pyplot as plot

from PIL import Image
from scipy.spatial import ConvexHull

def load_display_config(config_path='display_config.json'):
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

# Load display configuration
config = load_display_config()

BIT_DEPTH = config['bit_depth']

REFERENCE_R_XYZ = numpy.array(config['chromaticity']['r_XYZ'])
REFERENCE_G_XYZ = numpy.array(config['chromaticity']['g_XYZ'])
REFERENCE_B_XYZ = numpy.array(config['chromaticity']['b_XYZ'])
REFERENCE_W_XYZ = numpy.array(config['chromaticity']['w_XYZ'])

GAMMA_RED = numpy.array(config['gamma']['r'])
GAMMA_GREEN = numpy.array(config['gamma']['g'])
GAMMA_BLUE = numpy.array(config['gamma']['b'])

GAMMA_SAMPLES = GAMMA_RED.size

REFERENCE_W_XYZ_NORMALIZED = REFERENCE_W_XYZ / REFERENCE_W_XYZ[1]
REFERENCE_R_XYZ_NORMALIZED = REFERENCE_R_XYZ / REFERENCE_W_XYZ[1]
REFERENCE_G_XYZ_NORMALIZED = REFERENCE_G_XYZ / REFERENCE_W_XYZ[1]
REFERENCE_B_XYZ_NORMALIZED = REFERENCE_B_XYZ / REFERENCE_W_XYZ[1]

TARGET_BIT_DEPTH = 8


def get_reference_color_gamma(normalized_color, gamma_array):
    normalized_color = numpy.asarray(normalized_color)
    denormalized_color = normalized_color * float(GAMMA_SAMPLES - 1)
    idx_low = numpy.floor(denormalized_color).astype(int)
    idx_high = numpy.ceil(denormalized_color).astype(int)

    # Clamp indices to valid range
    idx_low = numpy.clip(idx_low, 0, GAMMA_SAMPLES - 1)
    idx_high = numpy.clip(idx_high, 0, GAMMA_SAMPLES - 1)

    # Calculate fractional part (equivalent to fract() in GLSL)
    weight = denormalized_color - numpy.floor(denormalized_color)

    return gamma_array[idx_low] * (1.0 - weight) + gamma_array[idx_high] * weight



def reference_eotf_decoding(color):
    color = numpy.asarray(color)
    if len(color.shape) == 1:
        gr = get_reference_color_gamma(color[0], GAMMA_RED)
        gg = get_reference_color_gamma(color[1], GAMMA_GREEN)
        gb = get_reference_color_gamma(color[2], GAMMA_BLUE)

        gamma_vec = numpy.array([gr, gg, gb])
    else:
        r_channel = color[..., 0]
        g_channel = color[..., 1]
        b_channel = color[..., 2]

        gr = get_reference_color_gamma(r_channel, GAMMA_RED)
        gg = get_reference_color_gamma(g_channel, GAMMA_GREEN)
        gb = get_reference_color_gamma(b_channel, GAMMA_BLUE)

        gamma_vec = numpy.stack([gr, gg, gb], axis=-1)
    return numpy.power(color, gamma_vec)



def reference_eotf_encoding(RGB):
    RGB = numpy.asarray(RGB)
    if len(RGB.shape) == 1:
        gr = get_reference_color_gamma(RGB[0], GAMMA_RED)
        gg = get_reference_color_gamma(RGB[1], GAMMA_GREEN)
        gb = get_reference_color_gamma(RGB[2], GAMMA_BLUE)

        gamma_vec = numpy.array([1.0/gr, 1.0/gg, 1.0/gb])
    else:
        r_channel = RGB[..., 0]
        g_channel = RGB[..., 1]
        b_channel = RGB[..., 2]
        gr = get_reference_color_gamma(r_channel, GAMMA_RED)
        gg = get_reference_color_gamma(g_channel, GAMMA_GREEN)
        gb = get_reference_color_gamma(b_channel, GAMMA_BLUE)

        gamma_vec = numpy.stack([1.0/gr, 1.0/gg, 1.0/gb], axis=-1)
    return numpy.power(RGB, gamma_vec)



target_colourspace = colour.RGB_Colourspace(
    name = 'Reference Display',
    primaries = numpy.array([
        colour.XYZ_to_xy(REFERENCE_R_XYZ_NORMALIZED),
        colour.XYZ_to_xy(REFERENCE_G_XYZ_NORMALIZED),
        colour.XYZ_to_xy(REFERENCE_B_XYZ_NORMALIZED)
    ]),
    whitepoint = colour.XYZ_to_xy(REFERENCE_W_XYZ_NORMALIZED),
    cctf_encoding=reference_eotf_encoding,   # use custom EOTF encoding
    cctf_decoding=reference_eotf_decoding    # use custom EOTF decoding
)

def generate_lut_colors():
    img_list = []
    for g in range(0, (1 << BIT_DEPTH), 1):
        for b in range(0, (1 << BIT_DEPTH), 1):
            for r in range(0, (1 << BIT_DEPTH), 1):
                pixel = [
                    numpy.float64(r / ((1 << BIT_DEPTH) - 1)),
                    numpy.float64(g / ((1 << BIT_DEPTH) - 1)),
                    numpy.float64(b / ((1 << BIT_DEPTH) - 1))
                ]
                img_list.append(pixel)
    return numpy.array(img_list, dtype=numpy.float64)

def get_target_screen_colors():
    img_list = []
    for g in range(0, (1 << TARGET_BIT_DEPTH), 1):
        for b in range(0, (1 << TARGET_BIT_DEPTH), 1):
            for r in range(0, (1 << TARGET_BIT_DEPTH), 1):
                pixel = [
                    numpy.float64(r / ((1 << TARGET_BIT_DEPTH) - 1)),
                    numpy.float64(g / ((1 << TARGET_BIT_DEPTH) - 1)),
                    numpy.float64(b / ((1 << TARGET_BIT_DEPTH) - 1))
                ]
                img_list.append(pixel)
    return img_list

def plot_deltaE_analysis(deltaE):
    fig, ((ax1, ax2), (ax3, ax4)) = plot.subplots(2, 2, figsize=(15, 10))

    # Histogram of DeltaE values >= 1
    filtered_deltaE = deltaE[deltaE >= 1]
    ax1.hist(filtered_deltaE, bins=50, color='skyblue', alpha=0.7, edgecolor='black')
    ax1.set_title('Delta E Distribution (≥ 1)')
    ax1.set_xlabel('Delta E')
    ax1.set_ylabel('Number of Colors')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(1, color='green', linestyle='--', label='ΔE = 1')
    ax1.axvline(2, color='orange', linestyle='--', label='ΔE = 2')
    ax1.axvline(3, color='red', linestyle='--', label='ΔE = 3')
    ax1.legend()

    # Cumulative distribution plot
    sorted_deltaE = numpy.sort(deltaE)
    cumulative_pct = numpy.arange(1, len(sorted_deltaE) + 1) / len(sorted_deltaE) * 100
    ax2.plot(sorted_deltaE, cumulative_pct, color='green', linewidth=2)
    ax2.set_title('Cumulative Distribution')
    ax2.set_xlabel('Delta E')
    ax2.set_ylabel('Percentage of Colors (%)')
    ax2.grid(True, alpha=0.3)
    line1 = ax2.axvline(1, color='green', linestyle='--', alpha=0.7)
    line2 = ax2.axvline(2, color='orange', linestyle='--', alpha=0.7)
    line3 = ax2.axvline(3, color='red', linestyle='--', alpha=0.7)
    ax2.legend([line1, line2, line3], ['ΔE = 1', 'ΔE = 2', 'ΔE = 3'], loc='lower right')
    ax2.set_xlim(0, max(5, numpy.percentile(deltaE, 95)))

    # Bar chart for color quality summary with 0.5 delta E steps starting from 1.0
    max_deltaE = int(numpy.ceil(numpy.max(deltaE)))
    bin_edges = numpy.arange(1.0, max_deltaE + 0.5, 0.5)
    counts, _ = numpy.histogram(deltaE, bins=bin_edges)
    total_colors = len(deltaE)
    percentages = (counts / total_colors) * 100

    bin_centers = bin_edges[:-1] + 0.25
    bars = ax3.bar(bin_centers, counts, width=0.4, alpha=0.7, edgecolor='black')

    for i, (count, pct) in enumerate(zip(counts, percentages)):
        if count > 0:
            ax3.text(bin_centers[i], count + max(counts) * 0.01,
                    f'{count}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9)

    ax3.set_title('Delta E Distribution (≥ 1)')
    ax3.set_xlabel('Delta E Range')
    ax3.set_ylabel('Number of Colors')
    ax3.set_xticks(bin_centers)
    ax3.set_xticklabels([f'{edge:.1f}-{edge+0.5:.1f}' for edge in bin_edges[:-1]])
    ax3.grid(True, alpha=0.3, axis='y')

    # Delta E statistics in bottom-right corner
    ax4.text(0.5, 0.7, f'Delta E Statistics', ha='center', va='center', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    ax4.text(0.5, 0.5, f'Mean: {numpy.mean(deltaE):.4f}', ha='center', va='center', fontsize=12, transform=ax4.transAxes)
    ax4.text(0.5, 0.4, f'Std Dev: {numpy.std(deltaE):.4f}', ha='center', va='center', fontsize=12, transform=ax4.transAxes)
    ax4.text(0.5, 0.3, f'Max: {numpy.max(deltaE):.4f}', ha='center', va='center', fontsize=12, transform=ax4.transAxes)
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')

    plot.tight_layout()
    plot.show()


def get_sRGB_hull():
    target_screen_colors = get_target_screen_colors()
    target_screen_colors_xyz = colour.RGB_to_XYZ(
        RGB=target_screen_colors,
        colourspace='sRGB',
        illuminant=None,
        chromatic_adaptation_transform=None,
        apply_cctf_decoding=True
    )
    target_screen_colors_lab = colour.XYZ_to_Lab(target_screen_colors_xyz)
    hull = ConvexHull(target_screen_colors_lab)
    return hull

if __name__ == "__main__":

    # Check for command line arguments
    if len(sys.argv) != 2:
        print("Usage: python image_converter.py <output_lut_image>")
        sys.exit(1)

    output_path = sys.argv[1]

    lut_colors = generate_lut_colors()

    # Calculate the 3D LUT size
    lut_size = (1 << BIT_DEPTH)

    # colorspace conversion
    converted_pixels = colour.RGB_to_RGB(
        RGB=lut_colors,
        input_colourspace=target_colourspace,
        output_colourspace='sRGB',
        chromatic_adaptation_transform='Bradford',
        apply_cctf_decoding=True,
        apply_cctf_encoding=True
    )

    '''
    source_xyz = colour.RGB_to_XYZ(
        RGB=pixels,
        colourspace=target_colourspace,
        illuminant=None,
        chromatic_adaptation_transform=None,
        apply_cctf_decoding=True
    )

    target_xyz = colour.adaptation.chromatic_adaptation_VonKries(
        XYZ=source_xyz,
        XYZ_w=REFERENCE_W_XYZ,
        XYZ_wr=colour.xy_to_XYZ(TARGET_W_CHROMATICITY),
        transform="Bradford"
    )

    converted_pixels = colour.XYZ_to_RGB(
        XYZ=target_xyz,
        colourspace='sRGB',
        illuminant=None,
        chromatic_adaptation_transform=None,
        apply_cctf_encoding=True
    )
    '''

    # To save as an image, flatten the 3D LUT into a 2D layout
    # A common option is to arrange the LUT layers horizontally
    lut_2d = converted_pixels.reshape(lut_size, lut_size * lut_size, 3)

    # Clamp values to valid range and convert back to 8-bit
    converted_image = numpy.clip(lut_2d, 0, 1)
    converted_image = (converted_image * 255.0).astype(numpy.uint8)


    xyz_reference = colour.RGB_to_XYZ(
        RGB=lut_colors,
        colourspace=target_colourspace,
        illuminant=colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65'],
        chromatic_adaptation_transform='Bradford',
        apply_cctf_decoding=True
    )

    xyz_actual = colour.RGB_to_XYZ(
        RGB=(converted_image.astype(numpy.float64) / 255.0).reshape(-1, 3),
        colourspace='sRGB',
        illuminant=None,
        chromatic_adaptation_transform=None,
        apply_cctf_decoding=True
    )

    deltaE = colour.difference.delta_E_CIE2000(
        Lab_1 = colour.XYZ_to_Lab(xyz_reference),
        Lab_2 = colour.XYZ_to_Lab(xyz_actual),
        textiles = False
    )

    '''
    # Gamut mapping optimization for colors with deltaE > 0.75
    high_deltaE_mask = deltaE > 0.75
    if numpy.any(high_deltaE_mask):
        print(f"Optimizing {numpy.sum(high_deltaE_mask)} colors with deltaE > 0.75...")

        hull = get_sRGB_hull()
        target_screen_colors = get_target_screen_colors()
        target_screen_colors_xyz = colour.RGB_to_XYZ(
            RGB=target_screen_colors,
            colourspace='sRGB',
            illuminant=None,
            chromatic_adaptation_transform=None,
            apply_cctf_decoding=True
        )
        target_screen_colors_lab = colour.XYZ_to_Lab(target_screen_colors_xyz)

        # Get only colors within the sRGB hull
        hull_colors_lab = target_screen_colors_lab[hull.vertices]
        hull_colors_rgb = numpy.array(target_screen_colors)[hull.vertices]

        high_deltaE_indices = numpy.where(high_deltaE_mask)[0]
        source_lab = colour.XYZ_to_Lab(xyz_reference[high_deltaE_indices])

        for i, idx in enumerate(high_deltaE_indices):
            current_deltaE = deltaE[idx]
            source_color_lab = source_lab[i]

            # Find closest hull color that minimizes deltaE
            candidate_deltaE = colour.difference.delta_E_CIE2000(
                Lab_1=numpy.tile(source_color_lab, (len(hull_colors_lab), 1)),
                Lab_2=hull_colors_lab,
                textiles=False
            )

            best_hull_idx = numpy.argmin(candidate_deltaE)
            best_deltaE = candidate_deltaE[best_hull_idx]

            if best_deltaE < current_deltaE:
                # Update the converted pixel and deltaE
                best_rgb = hull_colors_rgb[best_hull_idx]
                flat_idx = idx
                row = flat_idx // (lut_size * lut_size)
                col = (flat_idx % (lut_size * lut_size)) // lut_size
                depth = flat_idx % lut_size

                converted_image[row, col * lut_size + depth] = (best_rgb * 255.0).astype(numpy.uint8)
                deltaE[idx] = best_deltaE
    '''


    print(f"DeltaE mean: {numpy.mean(deltaE):.4f}")
    print(f"DeltaE stddev: {numpy.std(deltaE):.4f}")
    print(f"DeltaE max: {numpy.max(deltaE):.4f}")

    plot_deltaE_analysis(deltaE)

    # Create PIL image and save
    output_image = Image.fromarray(converted_image)
    output_image.save(output_path)

    print(f"Converted LUT saved to: {output_path}")
    print(f"Output image dimensions: {converted_image.shape[:2]}")
