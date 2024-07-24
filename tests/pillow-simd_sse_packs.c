// [https://raw.githubusercontent.com/uploadcare/pillow-simd/b17cdc92c958d666f2c6717fbfd2de532574ea06/libImaging/Antialias.c <- https://habr.com/ru/articles/326900/ <- https://habr.com/ru/articles/569204/ <- google:‘masm64 disassembler’]

#include "pillow-simd_Imaging.h"

#include <math.h>
#include <emmintrin.h>
#include <mmintrin.h>
#include <smmintrin.h>

void
ImagingResampleHorizontalConvolution8u(UINT32 *lineOut, UINT32 *lineIn,
    int xsize, int *xbounds, float *kk, int kmax)
{
    int xmin, xmax, xx, x;
    float *k;

    for (xx = 0; xx < xsize; xx++) {
        __m128 sss = _mm_set1_ps(0.5);
        xmin = xbounds[xx * 2 + 0];
        xmax = xbounds[xx * 2 + 1];
        k = &kk[xx * kmax];
        for (x = xmin; x < xmax; x++) {
            __m128i pix = _mm_cvtepu8_epi32(*(__m128i *) &lineIn[x]);
            __m128 mmk = _mm_set1_ps(k[x - xmin]);
            __m128 mul = _mm_mul_ps(_mm_cvtepi32_ps(pix), mmk);
            sss = _mm_add_ps(sss, mul);
        }
        __m128i ssi = _mm_cvtps_epi32(sss);
        ssi = _mm_packs_epi32(ssi, ssi);
        lineOut[xx] = _mm_cvtsi128_si32(_mm_packus_epi16(ssi, ssi));
    }
}


void
ImagingResampleVerticalConvolution8u(UINT32 *lineOut, Imaging imIn,
    int ymin, int ymax, float *k)
{
    int y, xx;

    for (xx = 0; xx < imIn->xsize; xx++) {
        __m128 sss = _mm_set1_ps(0.5);
        for (y = ymin; y < ymax; y++) {
            __m128i pix = _mm_cvtepu8_epi32(*(__m128i *) &imIn->image32[y][xx]);
            __m128 mmk = _mm_set1_ps(k[y - ymin]);
            __m128 mul = _mm_mul_ps(_mm_cvtepi32_ps(pix), mmk);
            sss = _mm_add_ps(sss, mul);
        }
        __m128i ssi = _mm_cvtps_epi32(sss);
        ssi = _mm_packs_epi32(ssi, ssi);
        lineOut[xx] = _mm_cvtsi128_si32(_mm_packus_epi16(ssi, ssi));
    }
}
