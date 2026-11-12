import numpy as np

from common import REPEAT_DATA, md_table, noise_floor, repeatability

differences = repeatability()
print(f"\nSources: {REPEAT_DATA}\n")
print("Five readings per greyscale patch; ten within-patch pairs; section 3 cleaning before D50, CIE 1931 2° integration.")
print("Bands through 423.333 nm inclusive and all negative reflectance values are set to zero.")
rows = []
for filename, values in differences.items():
    rows.append([filename, values.shape[0], values.shape[0] * 5, values.size,
                 f"{values.mean():.2f}", f"{np.percentile(values, 95):.2f}", f"{values.max():.2f}"])
pooled = np.concatenate([values.ravel() for values in differences.values()])
rows.append(["All", sum(values.shape[0] for values in differences.values()), pooled.size // 2, pooled.size,
             f"{pooled.mean():.2f}", f"{np.percentile(pooled, 95):.2f}", f"{pooled.max():.2f}"])
print(md_table(["Source", "Patch blocks", "Readings", "Pairs", "mean ΔE", "p95 ΔE", "max ΔE"], rows))

rows = [[index + 1] + [f"{np.percentile(values[index], 95):.2f}" for values in differences.values()]
        for index in range(32)]
print("\nWithin-patch p95 ΔE; patch blocks numbered in acquisition order\n")
print(md_table(["Patch block"] + list(differences), rows))
mean, p95 = noise_floor()
print(f"\nHistorical repeatability reference: mean ΔE = {mean:.2f}, p95 ΔE = {p95:.2f}")
print("Pairs within a block share readings; this empirical p95 is not a significance threshold or a single-reading standard deviation.")
