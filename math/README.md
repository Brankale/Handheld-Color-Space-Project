# Index

- [Colorspace conversion Math](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#colorspace-conversion-math)
   - [Calculate RGB => CIE XYZ conversion matrix](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#calculate-rgb--cie-xyz-conversion-matrix)
   - [Calculate the Chromatic Adaptation Transform (CAT) Matrix](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#calculate-the-chromatic-adaptation-transform-cat-matrix)




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
