# Index

- [Colorspace conversion Math](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#colorspace-conversion-math)
   - [Calculate RGB => CIE XYZ conversion matrix](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#calculate-rgb--cie-xyz-conversion-matrix)
   - [Calculate the Chromatic Adaptation Transform (CAT) Matrix](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#calculate-the-chromatic-adaptation-transform-cat-matrix)
 

# Spectral Power Distribution (SPD)

## Definition

A **Spectral Power Distribution (SPD)** describes the amount of optical power present at each wavelength in the visible spectrum (≈ 380–780 nm).
It is a wavelength-resolved description of light and represents the most complete physical characterization of a color stimulus.

<img width="1552" height="534" alt="spd_w" src="https://github.com/user-attachments/assets/458ee8e3-ed55-4de7-9ba7-39d455856d8e" />

## From SPD to CIE XYZ

Human color perception is commonly modeled using the **CIE 1931 color matching functions** $`\overline{x}(\lambda),\overline{y}(\lambda),\overline{z}(\lambda)`$.

Given an SPD $`S(\lambda)`$, the corresponding **CIE XYZ tristimulus values** are obtained by:

$`X = k \displaystyle\int_{\lambda_{\min}}^{\lambda_{\max}} S(\lambda)\,\overline{x}(\lambda)\,d\lambda`$

$`Y = k \displaystyle\int_{\lambda_{\min}}^{\lambda_{\max}} S(\lambda)\,\overline{y}(\lambda)\,d\lambda`$

$`Z = k \displaystyle\int_{\lambda_{\min}}^{\lambda_{\max}} S(\lambda)\,\overline{z}(\lambda)\,d\lambda`$

where:

- $`\lambda`$ is the wavelength
- $`S(\lambda)`$ is the spectral power distribution
- $`k`$ is a normalization constant (often chosen so that $`Y=1`$ or $`Y=100`$)

These XYZ values are the basis for all subsequent colorimetric operations (e.g. chromaticity, RGB conversion, gamut mapping).

## Emissive Displays

Modern displays are emissive: each pixel emits light with its own SPD.

Example of SPD taken from measurements of the Game Boy Micro:

<table>
  <tr>
    <td><img width="1553" height="536" alt="red SPD" src="https://github.com/user-attachments/assets/894a46dc-437d-4877-b76b-76234644d839" /> $SPD_{red}$ </td>
    <td><img width="1555" height="534" alt="green SPD" src="https://github.com/user-attachments/assets/b68a4d60-5537-4b9a-a881-f05da41ba176" /> $SPD_{green}$ </td>
  </tr>
  <tr>
    <td><img width="1553" height="535" alt="blue SPD" src="https://github.com/user-attachments/assets/f9c97410-367e-4953-9bd9-4051a968f3e8" /> $SPD_{blue}$ </td>
    <td><img width="1552" height="534" alt="white SPD" src="https://github.com/user-attachments/assets/458ee8e3-ed55-4de7-9ba7-39d455856d8e" /> $SPD_{white} = SPD_{red} + SPD_{green} + SPD_{blue}$ </td>
  </tr>
</table>

For emissive systems:

- The SPD is fixed by the display hardware
- The emitted light directly reaches the observer
- Once the SPD is integrated into XYZ, no further spectral information is required

For this reason, **CIE XYZ coordinates are generally sufficient to model emissive displays** for color reproduction purposes.

## Reflective Displays

Old handheld consoles commonly used reflective or transflective LCDs.
These displays do not emit light: they modulate and reflect the incident illumination.
The resulting SPD is:

$`S_{out}(\lambda) = S_{illuminant}(\lambda) \cdot R_{display}(\lambda)`$

where:

- $`S_{illuminant}(\lambda)`$ is the SPD of the ambient light
- $`R_{display}(\lambda)`$ is the spectral reflectance of the display

> The following GIF [7] shows a 560 nm-normalized SPD of a CIE D illuminant (blue area) as a function of color temperature (red curve).
> The same principle applies to reflective displays: the effective SPD of the display changes with the SPD of the incident illuminant. In other words, a reflective display does not have a fixed SPD — it is spectrally shaped by the light that illuminates it.
> ![CIE_illuminants_D_and_blackbody_small](https://github.com/user-attachments/assets/6392a2c4-a622-4f3f-b212-2d53c0d1ed18)


In this case:

- The **illuminant is an essential part** of the color formation
- **Different illuminants produce different XYZ values from the same display**
- **A single set of XYZ coordinates cannot fully describe the system**

To accurately model a reflective display, the full SPD (or spectral reflectance) must be retained until the final observer-dependent integration step.

## Relevance to This Project

This project reproduces the colors of emissive/reflective handheld displays on modern emissive screens.

This requires:

- Modeling the original color generation in the spectral domain
- Converting a reflective, illuminant-dependent SPD into an emitted SPD
- Only then reducing the result to XYZ for rendering on modern hardware

Using XYZ alone is sufficient for emissive displays, but insufficient to accurately model reflective displays without prior spectral reconstruction.

## Key Takeaway

- SPD → XYZ is the fundamental bridge between physics and colorimetry
- XYZ is enough for emissive displays
- **Reflective displays require spectral modeling before XYZ conversion**




# Colorspace conversion Math

## Calculate RGB => CIE XYZ conversion matrix

Given the chromaticity coordinates of an RGB system $`(x_{r}, y_{r})`$ , $`(x_{g}, y_{g})`$ and $`(x_{b}, y_{b})`$ using the CIE xyY colorspace and its reference white $`(X_{w}, Y_{w}, Z_{w})`$ using the CIE XYZ colorspace, here is the method to compute the 3 × 3 matrix for converting RGB to CIE XYZ:

$`
\begin{equation}
    \begin{bmatrix}
        X \\ Y \\ Z
    \end{bmatrix}
    =
    \begin{bmatrix}
        M
    \end{bmatrix}
    \begin{bmatrix}
        R \\ G \\ B
    \end{bmatrix}
\end{equation}
`$

where $`M`$ is

$`
\begin{equation}
    \begin{bmatrix}
        M
    \end{bmatrix}
    =
    \begin{bmatrix}
        S_{r}X_{r} & S_{g}X_{g} & S_{b}X_{b} \\
        S_{r}Y_{r} & S_{g}Y_{g} & S_{b}Y_{b} \\
        S_{r}Z_{r} & S_{g}Z_{g} & S_{b}Z_{b} \\
    \end{bmatrix}
\end{equation}
`$

the scaling factors $`(S_{r}, S_{g}, S_{b})`$ are

$`
\begin{equation}
    \begin{bmatrix}
        S_{r} \\ S_{g} \\ S_{b}
    \end{bmatrix}
    =
    \begin{bmatrix}
        X_{r} & X_{g} & X_{b} \\
        Y_{r} & Y_{g} & Y_{b} \\
        Z_{r} & Z_{g} & Z_{b} \\
    \end{bmatrix}
    ^{-1}
    \begin{bmatrix}
        X_{w} \\ Y_{w} \\ Z_{w}
    \end{bmatrix}
\end{equation}
`$

and XYZ values are

$`
\begin{align}
    & X_{r} = \frac{x_{r}}{y_{r}} &
    & Y_{r} = 1 &
    & Z_{r} = \frac{1-x_{r}-y_{r}}{y_{r}}
\end{align}
`$

$`
\begin{align}
    & X_{g} = \frac{x_{g}}{y_{g}} &
    & Y_{g} = 1 &
    & Z_{g} = \frac{1-x_{g}-y_{g}}{y_{g}}
\end{align}
`$

$`
\begin{align}
    & X_{b} = \frac{x_{b}}{y_{b}} &
    & Y_{b} = 1 &
    & Z_{b} = \frac{1-x_{b}-y_{b}}{y_{b}}
\end{align}
`$

$`
\begin{align}
    & X_{w} = \frac{x_{w}}{y_{w}} &
    & Y_{w} = 1 &
    & Z_{w} = \frac{1-x_{w}-y_{w}}{y_{w}}
\end{align}
`$

> [!NOTE]
> Given CIE xyY coordinates, CIE XYZ coordinates are:
> 
> $` X = \frac{x}{y}Y `$
> 
> $` Z = \frac{1-x-y}{y}Y `$

## Step-by-step derivation from measured display primaries

The previous section starts from chromaticity coordinates and a reference white. In this section we start from a different situation: we have measured the XYZ coordinates of the black level, the three full-level primaries and a grayscale ramp.

The purpose is to begin with the simplest possible model, based on the additivity of XYZ coordinates, and only then introduce systems of equations and matrices.

### 1. Additivity of XYZ coordinates

The CIE XYZ tristimulus values are linear with respect to the spectral power distribution. If two independent light contributions have spectral power distributions $`S_{1}(\lambda)`$ and $`S_{2}(\lambda)`$, their sum is:

$$
S_{sum}(\lambda) = S_{1}(\lambda) + S_{2}(\lambda)
$$

For example, the X tristimulus value of the sum is:

$$
X_{sum} = k \int S_{sum}(\lambda)\,\overline{x}(\lambda)\,d\lambda
$$

Substituting the definition of $`S_{sum}(\lambda)`$ gives:

$$
X_{sum} = k \int \left[S_{1}(\lambda) + S_{2}(\lambda)\right]\overline{x}(\lambda)\,d\lambda
$$

By distributing the integral:

$$
X_{sum} = k \int S_{1}(\lambda)\overline{x}(\lambda)\,d\lambda
          + k \int S_{2}(\lambda)\overline{x}(\lambda)\,d\lambda
$$

Therefore:

$$
X_{sum} = X_{1} + X_{2}
$$

The same reasoning applies to $`Y`$ and $`Z`$, so the XYZ vector is additive:

$$
\begin{bmatrix}
X_{sum} \\
Y_{sum} \\
Z_{sum}
\end{bmatrix}
=
\begin{bmatrix}
X_{1} \\
Y_{1} \\
Z_{1}
\end{bmatrix}
+
\begin{bmatrix}
X_{2} \\
Y_{2} \\
Z_{2}
\end{bmatrix}
$$

This is the property that allows the XYZ coordinates of additive display channels to be summed.

### 2. Emissive and transmissive displays

It is useful to begin with the cleanest possible picture. A display creates a color by combining its red, green and blue channels. For RGB levels $`r`$, $`g`$ and $`b`$:

$$
\mathbf{XYZ}(r,g,b)
= r\mathbf{R} + g\mathbf{G} + b\mathbf{B}
$$

where:

$$
\mathbf{R} = \mathbf{XYZ}(1,0,0),
\qquad
\mathbf{G} = \mathbf{XYZ}(0,1,0),
\qquad
\mathbf{B} = \mathbf{XYZ}(0,0,1)
$$

> [!NOTE]
> In this section, $`r`$, $`g`$ and $`b`$ denote linear RGB levels. Any transfer-function decoding must therefore be performed before applying these equations. In other words, these are the values that can be added directly in the formula below.

This gives us a simple reference point. If all three channels are off, the ideal model gives:

$$
\mathbf{XYZ}(0,0,0) = \mathbf{0}
$$

The ideal result is zero, but a real measurement of the black patch may still be non-zero. We call that measured value $`\mathbf{K}`$:

$$
\mathbf{K} = \mathbf{XYZ}_{measured}(0,0,0)
$$

If this value is stable and behaves as an additive baseline, the measured XYZ value of any patch can be written as the black contribution plus the color contribution:

$$
\mathbf{XYZ}_{measured}(r,g,b)
= \mathbf{K} + \mathbf{XYZ}(r,g,b)
$$

This also explains how to read the measured primaries. For the red primary, subtracting the black patch leaves only the red contribution. The same operation applies to all three channels:

$$
\mathbf{R}_{net} = \mathbf{R}_{measured} - \mathbf{K},
\qquad
\mathbf{G}_{net} = \mathbf{G}_{measured} - \mathbf{K},
\qquad
\mathbf{B}_{net} = \mathbf{B}_{measured} - \mathbf{K}
$$

Once the three net primary contributions have been isolated, they can be added to reconstruct white. The black baseline is included as the starting point:

$$
\mathbf{W}_{model}
= \mathbf{K} + \mathbf{R}_{net} + \mathbf{G}_{net} + \mathbf{B}_{net}
$$

The important detail is that the baseline is removed from each measured primary before the addition, and then included once in the reconstructed white.

> [!NOTE]
> $`\mathbf{K}`$ is simply the measured output of the black patch. For an emissive display it may come from residual emission, reflections or the measurement setup. For a transmissive display it may include light that passes through the panel when the channels are off. The subtraction model is appropriate only when $`\mathbf{K}`$ is stable and additive; otherwise, one black subtraction should not be applied automatically to every patch.

### 3. Primaries, secondaries and white without matrices

Let the measured XYZ coordinates of the black level be:

$$
\mathbf{K} =
\begin{bmatrix}
X_{K} \\
Y_{K} \\
Z_{K}
\end{bmatrix}
$$

Let the measured XYZ coordinates of the full-level red, green and blue patches be:

$$
\mathbf{R}_{m} =
\begin{bmatrix}
X_{R,m} \\
Y_{R,m} \\
Z_{R,m}
\end{bmatrix},
\qquad
\mathbf{G}_{m} =
\begin{bmatrix}
X_{G,m} \\
Y_{G,m} \\
Z_{G,m}
\end{bmatrix},
\qquad
\mathbf{B}_{m} =
\begin{bmatrix}
X_{B,m} \\
Y_{B,m} \\
Z_{B,m}
\end{bmatrix}
$$

If the measured primary patches contain the same black contribution as the other patches, define the net primaries by subtracting the baseline one time from each measured primary:

$$
\mathbf{R}_{net} = \mathbf{R}_{m} - \mathbf{K}
$$

$$
\mathbf{G}_{net} = \mathbf{G}_{m} - \mathbf{K}
$$

$$
\mathbf{B}_{net} = \mathbf{B}_{m} - \mathbf{K}
$$

For the yellow secondary, the signal contribution is the sum of red and green:

$$
\mathbf{Y}_{signal} = \mathbf{R}_{net} + \mathbf{G}_{net}
$$

The measured output also contains the black baseline, so:

$$
\mathbf{Y}_{model} = \mathbf{K} + \mathbf{R}_{net} + \mathbf{G}_{net}
$$

Similarly, the other secondary colors are:

$$
\mathbf{C}_{model} = \mathbf{K} + \mathbf{G}_{net} + \mathbf{B}_{net}
$$

$$
\mathbf{M}_{model} = \mathbf{K} + \mathbf{R}_{net} + \mathbf{B}_{net}
$$

The white contains all three channel contributions, plus one black baseline:

$$
\mathbf{W}_{model} = \mathbf{K} + \mathbf{R}_{net} + \mathbf{G}_{net} + \mathbf{B}_{net}
$$

Substituting the definitions of the net primaries gives:

$$
\mathbf{W}_{model}
= \mathbf{K}
+ (\mathbf{R}_{m} - \mathbf{K})
+ (\mathbf{G}_{m} - \mathbf{K})
+ (\mathbf{B}_{m} - \mathbf{K})
$$

Collecting the black terms:

$$
\mathbf{W}_{model}
= \mathbf{R}_{m} + \mathbf{G}_{m} + \mathbf{B}_{m} - 2\mathbf{K}
$$

The black is therefore not subtracted from the final white. It is subtracted from each primary contribution and then added once as the common output baseline.

### 4. Numerical example

Consider the following relative XYZ measurements:

$$
\mathbf{K} =
\begin{bmatrix}
0.01 \\
0.01 \\
0.02
\end{bmatrix},
\quad
\mathbf{R}_{m} =
\begin{bmatrix}
0.61 \\
0.21 \\
0.12
\end{bmatrix},
\quad
\mathbf{G}_{m} =
\begin{bmatrix}
0.11 \\
0.71 \\
0.12
\end{bmatrix},
\quad
\mathbf{B}_{m} =
\begin{bmatrix}
0.06 \\
0.11 \\
0.82
\end{bmatrix}
$$

First subtract the black baseline from each primary:

$$
\mathbf{R}_{net} =
\begin{bmatrix}
0.61 - 0.01 \\
0.21 - 0.01 \\
0.12 - 0.02
\end{bmatrix}
=
\begin{bmatrix}
0.60 \\
0.20 \\
0.10
\end{bmatrix}
$$

$$
\mathbf{G}_{net} =
\begin{bmatrix}
0.10 \\
0.70 \\
0.10
\end{bmatrix},
\qquad
\mathbf{B}_{net} =
\begin{bmatrix}
0.05 \\
0.10 \\
0.80
\end{bmatrix}
$$

The yellow model is obtained in two steps. First sum the net red and green contributions:

$$
\mathbf{R}_{net} + \mathbf{G}_{net}
=
\begin{bmatrix}
0.70 \\
0.90 \\
0.20
\end{bmatrix}
$$

Then add the black baseline once:

$$
\mathbf{Y}_{model}
=
\begin{bmatrix}
0.01 \\
0.01 \\
0.02
\end{bmatrix}
+
\begin{bmatrix}
0.70 \\
0.90 \\
0.20
\end{bmatrix}
=
\begin{bmatrix}
0.71 \\
0.91 \\
0.22
\end{bmatrix}
$$

The white model is obtained in the same way:

$$
\mathbf{R}_{net} + \mathbf{G}_{net} + \mathbf{B}_{net}
=
\begin{bmatrix}
0.75 \\
1.00 \\
1.00
\end{bmatrix}
$$

$$
\mathbf{W}_{model}
= \mathbf{K} + \mathbf{R}_{net} + \mathbf{G}_{net} + \mathbf{B}_{net}
=
\begin{bmatrix}
0.76 \\
1.01 \\
1.02
\end{bmatrix}
$$

Suppose that the directly measured white is:

$$
\mathbf{W}_{m} =
\begin{bmatrix}
0.75 \\
1.00 \\
1.01
\end{bmatrix}
$$

The additivity residual is then calculated component by component:

$$
\boldsymbol{\varepsilon}_{W}
= \mathbf{W}_{m} - \mathbf{W}_{model}
=
\begin{bmatrix}
-0.01 \\
-0.01 \\
-0.01
\end{bmatrix}
$$

This residual should not automatically be forced to zero. It is a measurement of how well the additive model agrees with the real display and the measurement procedure.

### 5. Why the scaling factors are needed

There are two different situations that are often described with the same scaling factors.

#### Primaries reconstructed from xy chromaticities

When starting from the chromaticity coordinates $`(x_{R},y_{R})`$, $`(x_{G},y_{G})`$ and $`(x_{B},y_{B})`$, the usual conversion to XYZ is normalized to $`Y=1`$:

$$
X_{R} = \frac{x_{R}}{y_{R}},
\qquad
Y_{R} = 1,
\qquad
Z_{R} = \frac{1-x_{R}-y_{R}}{y_{R}}
$$

The same is done for green and blue. This normalization fixes the chromaticity of each primary, but it does not yet fix the relative amount of red, green and blue needed to reproduce the chosen white point.

To determine those relative amounts, the primary vectors are combined with unknown scaling factors. The white constraint is first written as three scalar equations:

$$
\begin{cases}
S_{R}X_{R} + S_{G}X_{G} + S_{B}X_{B} = X_{W} \\
S_{R}Y_{R} + S_{G}Y_{G} + S_{B}Y_{B} = Y_{W} \\
S_{R}Z_{R} + S_{G}Z_{G} + S_{B}Z_{B} = Z_{W}
\end{cases}
$$

The factors are needed because $`Y=1`$ in the initial xy-to-XYZ conversion is only a normalization. The factors restore the relative scale that makes $`r_{lin}=g_{lin}=b_{lin}=1`$ reproduce the selected white.

Only now is the system written as a matrix equation:

$$
\begin{bmatrix}
X_{R} & X_{G} & X_{B} \\
Y_{R} & Y_{G} & Y_{B} \\
Z_{R} & Z_{G} & Z_{B}
\end{bmatrix}
\begin{bmatrix}
S_{R} \\
S_{G} \\
S_{B}
\end{bmatrix}
=
\begin{bmatrix}
X_{W} \\
Y_{W} \\
Z_{W}
\end{bmatrix}
$$

and, when the primary matrix is invertible:

$$
\begin{bmatrix}
S_{R} \\
S_{G} \\
S_{B}
\end{bmatrix}
=
\begin{bmatrix}
X_{R} & X_{G} & X_{B} \\
Y_{R} & Y_{G} & Y_{B} \\
Z_{R} & Z_{G} & Z_{B}
\end{bmatrix}^{-1}
\begin{bmatrix}
X_{W} \\
Y_{W} \\
Z_{W}
\end{bmatrix}
$$

This is the reason for the scaling factors in the existing RGB to XYZ derivation. They are not gamma values.

#### Primaries measured directly in XYZ

When the XYZ values of the primaries are measured directly, their absolute or relative scale is already present in the measurements. However, measurements of the three primaries and the white do not necessarily satisfy exact additivity:

$$
\mathbf{W}_{m}
\neq
\mathbf{R}_{m} + \mathbf{G}_{m} + \mathbf{B}_{m}
$$

after accounting for the black baseline. The mismatch can be caused by measurement error, repeatability, display drift or a display behaviour that is not additive.

In this situation, scaling factors can still be useful as correction factors, but they should not be assumed to be one constant triplet for the entire display response. In the workflow of this project, the three primaries and the grayscale ramp are used to estimate a different triplet for each grayscale level.

> [!WARNING]
> The direct use of measured primary vectors as the columns of one fixed RGB to XYZ matrix assumes that the channel response is linear with respect to the RGB values being used. That assumption is not valid for a display whose channel response changes from one level to another or has a non-standard EOTF. The measured response curves must be retained instead.

### 6. Scaling factors from the grayscale ramp

Let $`x`$ be a normalized grayscale input level, with $`0 \leq x \leq 1`$. Let the measured XYZ coordinates of that grayscale patch be:

$$
\mathbf{G}_{m}(x_{lin}) =
\begin{bmatrix}
X_{gray,m}(x) \\
Y_{gray,m}(x) \\
Z_{gray,m}(x)
\end{bmatrix}
$$

If the black level is a valid additive baseline, subtract it before estimating the channel contributions:

$$
\mathbf{G}_{net}(x) = \mathbf{G}_{m}(x) - \mathbf{K}
$$

At level $`x`$, the grayscale patch contains a contribution from each channel. Write the three scalar equations first:

$$
\begin{cases}
S_{R}(x)X_{R,net} + S_{G}(x)X_{G,net} + S_{B}(x)X_{B,net} = X_{gray,net}(x) \\
S_{R}(x)Y_{R,net} + S_{G}(x)Y_{G,net} + S_{B}(x)Y_{B,net} = Y_{gray,net}(x) \\
S_{R}(x)Z_{R,net} + S_{G}(x)Z_{G,net} + S_{B}(x)Z_{B,net} = Z_{gray,net}(x)
\end{cases}
$$

The first equation describes the X component, the second describes Y, and the third describes Z. The unknowns are the three channel response factors at this particular level: $`S_{R}(x)`$, $`S_{G}(x)`$ and $`S_{B}(x)`$.

Now define the matrix whose columns are the net measured primaries:

$$
P_{net} =
\begin{bmatrix}
X_{R,net} & X_{G,net} & X_{B,net} \\
Y_{R,net} & Y_{G,net} & Y_{B,net} \\
Z_{R,net} & Z_{G,net} & Z_{B,net}
\end{bmatrix}
$$

The same system can then be written as:

$$
P_{net}
\begin{bmatrix}
S_{R}(x) \\
S_{G}(x) \\
S_{B}(x)
\end{bmatrix}
=
\begin{bmatrix}
X_{gray,net}(x) \\
Y_{gray,net}(x) \\
Z_{gray,net}(x)
\end{bmatrix}
$$

Finally, if $`P_{net}`$ is invertible, the response factors are:

$$
\begin{bmatrix}
S_{R}(x) \\
S_{G}(x) \\
S_{B}(x)
\end{bmatrix}
=
P_{net}^{-1}
\begin{bmatrix}
X_{gray,net}(x) \\
Y_{gray,net}(x) \\
Z_{gray,net}(x)
\end{bmatrix}
$$

Repeating this calculation for every measured grayscale level produces three response curves:

$$
S_{R}(x), \qquad S_{G}(x), \qquad S_{B}(x)
$$

These factors are normalized channel contributions relative to the measured full-level primaries. They are not assumed to be constant. A single gamma value is therefore not required to describe the display.

For $`0 < x < 1`$ and a positive response factor, an effective gamma relative to the origin can be calculated as:

$$
\gamma_{i,eff}(x) = \frac{\ln\left(S_{i}(x)\right)}{\ln(x)},
\qquad i \in \{R,G,B\}
$$

This is an effective exponent between the origin and $`x`$, not a statement that the complete response is a power function. The measured curves $`S_{R}(x)`$, $`S_{G}(x)`$ and $`S_{B}(x)`$, or equivalent lookup tables, are the primary result.

At $`x=0`$, logarithmic gamma is undefined. Near black, small measurement errors can also make a response factor zero or negative; such values cannot be used directly in the logarithm and must be treated as unreliable measurements rather than silently corrected.

### 7. Conditions and source notes

The baseline-subtracted model should be used only after checking that:

- the black patch was measured with the same geometry, timing and display settings as the other patches;
- the black level is sufficiently stable during the measurement sequence;
- the white and secondary patches are compared with the model using the same patch conditions;
- the residual between measured and reconstructed white is compatible with the repeatability of the measurement;
- the display does not change its behaviour because of ABL, local dimming, backlight variation or significant channel interaction.

If these conditions do not hold, keep the absolute XYZ measurements and treat the additive model as an approximation. The baseline subtraction is a characterization choice, not a universal rule for all emissive or transmissive displays.

The following sources support the treatment of non-zero black levels and measured response curves. They do not, by themselves, establish the specific subtraction formula above:

- [ArgyllCMS dispcal documentation](https://www.argyllcms.com/doc/dispcal.html): “Instrument black level drift compensation attempts to combat measurement deviations caused by black calibration drift ... by using an initial display black test patch as a reference.” This concerns instrument drift and measurement repeatability, not a direct prescription to subtract display black from every primary.
- [DisplayCAL documentation](https://displaycal.net/): “a real display usually can't reproduce any of the ideal pre-defined curves, since it will have a non-zero black point” and “Curves are more accurate than gamma values.” This supports keeping a measured response curve and accounting for a non-zero black point, but it does not prove that a single black subtraction is valid for every display.

The subtraction and the equations in this section follow instead from the explicitly stated additive-baseline model:

$$
\mathbf{XYZ}_{measured}(p)
=
\mathbf{K} + \mathbf{XYZ}_{signal}(p)
$$

The model must be tested against the available measurements before it is used to derive the channel response curves.

## Calculate the Chromatic Adaptation Transform (CAT) Matrix

When performing a conversion between two colorspaces with a different white point, a chromatic adaptation must also be applied.

To perform a chromatic adaptation you must use the following equation:

$`
\begin{equation}
    \begin{bmatrix}
        X_{D} \\ Y_{D} \\ Z_{D}
    \end{bmatrix}
    =
    \begin{bmatrix}
        M_{CAM}
    \end{bmatrix}
    \begin{bmatrix}
        X_{S} \\ Y_{S} \\ Z_{S}
    \end{bmatrix}
\end{equation}
`$

$`
\begin{equation}
    \begin{bmatrix}
        M_{CAM}
    \end{bmatrix}
    =
    \begin{bmatrix}
        M_{CAT}
    \end{bmatrix}^{-1}
    \begin{bmatrix}
        L_{WD} / L_{WS} & 0 & 0 \\
        0 & M_{WD} / M_{WS} & 0 \\
        0 & 0 & S_{WD} / S_{WS} \\
    \end{bmatrix}
    \begin{bmatrix}
        M_{CAT}
    \end{bmatrix}
\end{equation}
`$

$`
\begin{equation}
    \begin{bmatrix}
        L_{WS} \\ M_{WS} \\ S_{WS}
    \end{bmatrix}
    =
    \begin{bmatrix}
        M_{CAT}
    \end{bmatrix}
    \begin{bmatrix}
        X_{WS} \\ Y_{WS} \\ Z_{WS}
    \end{bmatrix}
\end{equation}
`$

$`
\begin{equation}
    \begin{bmatrix}
        L_{WD} \\ M_{WD} \\ S_{WD}
    \end{bmatrix}
    =
    \begin{bmatrix}
        M_{CAT}
    \end{bmatrix}
    \begin{bmatrix}
        X_{WD} \\ Y_{WD} \\ Z_{WD}
    \end{bmatrix}
\end{equation}
`$

You can choose among several chromatic adaptation transforms. The most common are: Von Kries, Bradford, CIECAT02 and CIECAT16.



#### Von Kries matrix (not recommended)
$`
\begin{equation}
    \begin{bmatrix}
        M_{VK}
    \end{bmatrix}
    =
    \begin{bmatrix}
         0.40024 &  0.70760 & -0.08081 \\
        -0.22630 &  1.16532 &  0.04570 \\
         0.00000 & 0.00000 &  0.91822 \\
    \end{bmatrix}
\end{equation}
`$

#### Bradford matrix
$`
\begin{equation}
    \begin{bmatrix}
        M_{BF}
    \end{bmatrix}
    =
    \begin{bmatrix}
         0.8951 &  0.2664 & -0.1614 \\
        -0.7502 &  1.7135 &  0.0367 \\
         0.0389 & -0.0685 &  1.0296 \\
    \end{bmatrix}
\end{equation}
`$

#### CIECAT02 matrix (*)

$`
\begin{equation}
    \begin{bmatrix}
        M_{CAT02}
    \end{bmatrix}
    =
    \begin{bmatrix}
         0.7328 & 0.4296 & -0.1624 \\
        -0.7036 & 1.6975 &  0.0061 \\
         0.0030 & 0.0136 &  0.9834 \\
    \end{bmatrix}
\end{equation}
`$

#### CIECAT16 matrix (*)

$`
\begin{equation}
    \begin{bmatrix}
        M_{CAT16}
    \end{bmatrix}
    =
    \begin{bmatrix}
         0.401288 & 0.650173 & -0.051461 \\
        -0.250268 & 1.204414 &  0.045854 \\
        -0.002079 & 0.048952 &  0.953127 \\
    \end{bmatrix}
\end{equation}
`$

> [!WARNING]
> (*) CIECAT02 and its revision CIECAT16 should provide higher accuracy than the Bradford matrix, however they likely involve more complex operations than a simple 3×3 matrix multiplication as can be seen here: https://en.wikipedia.org/wiki/CIECAM02.
> Since there are few publicly available resources to support precise calculations with these models, the Bradford matrix will be used to minimize the risk of errors.

## Calculate gamma of the primaries from the greyscale (for emissive displays)

> [!WARNING]
> this section is a draft

> [!IMPORTANT]
> Using only the greyscale gamma curve is not enough to get accurate results. To make things clear, think the greyscale gamma as the mean between the red gamma (γR), the green gamma (γG) and the blue gamma (γB) (this is an oversemplification, this is not actually a mean). You can have a greyscale gamma of 2.2 which seems great but this can be the results of both (γR = 2.2, γG = 2.2, γB = 2.2) and (γR = 2.9, γG = 2.2, γB = 1.5) which leads to completely different colors.

In emissive displays you can sum XYZ coordinates of the primaries.

e.g.
$`
\begin{equation}
    \begin{bmatrix}
      X_{red} \\
      Y_{red} \\
      Z_{red} \\
    \end{bmatrix}
    +
    \begin{bmatrix}
      X_{green} \\
      Y_{green} \\
      Z_{green} \\
    \end{bmatrix}
    =
    \begin{bmatrix}
      X_{yellow} \\
      Y_{yellow} \\
      Z_{yellow} \\
    \end{bmatrix}
\end{equation}
`$

e.g.
$`
\begin{equation}
    \begin{bmatrix}
      X_{red} \\
      Y_{red} \\
      Z_{red} \\
    \end{bmatrix}
    +
    \begin{bmatrix}
      X_{green} \\
      Y_{green} \\
      Z_{green} \\
    \end{bmatrix}
    +
    \begin{bmatrix}
      X_{blue} \\
      Y_{blue} \\
      Z_{blue} \\
    \end{bmatrix}
    =
    \begin{bmatrix}
      X_{white} \\
      Y_{white} \\
      Z_{white} \\
    \end{bmatrix}
\end{equation}
`$

XYZ coordinates of the primaries, XYZ coordinates of a grey color at position x in [0.0, 1.0] where 0.0 is black and 1.0 is white:

Solve the system of three equations to find the scaling factors ($S_{r}$, $S_{g}$, $S_{b}$):

$`
\begin{equation}
    \begin{cases}
      S_{r} X_{r} + S_{g} X_{g} + S_{b} X_{b} = X_{grey}(x) \\
      S_{r} Y_{r} + S_{g} Y_{g} + S_{b} Y_{b} = Y_{grey}(x) \\
      S_{r} Z_{r} + S_{g} Z_{g} + S_{b} Z_{b} = Z_{grey}(x) \\
    \end{cases}
\end{equation}
`$

We can rewrite the system of equations using matrices:

$`
\begin{equation}
    \begin{bmatrix}
      X_{r} & X_{g} & X_{b} \\
      Y_{r} & Y_{g} & Y_{b} \\
      Z_{r} & Z_{g} & Z_{b} \\
    \end{bmatrix}
    \begin{bmatrix}
      S_{r} \\
      S_{g} \\
      S_{b} \\
    \end{bmatrix}
    =
    \begin{bmatrix}
        X_{grey}(x) \\
        Y_{grey}(x) \\
        Z_{grey}(x) \\
    \end{bmatrix}
\end{equation}
`$

$`
\begin{equation}
    \begin{bmatrix}
      S_{r} \\
      S_{g} \\
      S_{b} \\
    \end{bmatrix}
    =
    \begin{bmatrix}
      X_{r} & X_{g} & X_{b} \\
      Y_{r} & Y_{g} & Y_{b} \\
      Z_{r} & Z_{g} & Z_{b} \\
    \end{bmatrix}^{-1}
    \begin{bmatrix}
        X_{grey}(x) \\
        Y_{grey}(x) \\
        Z_{grey}(x) \\
    \end{bmatrix}
\end{equation}
`$

$`
\begin{align}
    & \gamma_{r}(x) = \log_{x}(S_{r}) &
    & \gamma_{g}(x) = \log_{x}(S_{g}) &
    & \gamma_{b}(x) = \log_{x}(S_{b}) &
\end{align}
`$


# External links
1. https://www.audioholics.com/news/nintendo-ds-price-fixing
2. -
3. https://www.youtube.com/@hdtvtest channel
4. CIELUV: https://en.wikipedia.org/wiki/CIELUV
5. LMS colorspace and chromatic adaptation matrices (i.e. Bradford, CIECAT02, CIECAT16):
    - https://en.wikipedia.org/wiki/LMS_color_space
    - https://en.wikipedia.org/wiki/CIECAM02
6. Colorspace conversions: http://brucelindbloom.com/index.html
7. https://en.wikipedia.org/wiki/Standard_illuminant
