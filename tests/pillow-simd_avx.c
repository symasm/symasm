// [https://raw.githubusercontent.com/uploadcare/pillow-simd/fd828595fc77f0999481871a766fee6bc4a061eb/libImaging/Antialias.c <- https://habr.com/ru/articles/326900/ <- https://habr.com/ru/articles/569204/ <- google:‘masm64 disassembler’]

#include "pillow-simd_Imaging.h"

#include <math.h>
#include <emmintrin.h>
#include <mmintrin.h>
#include <smmintrin.h>

#ifdef __AVX2__
    #include "immintrin.h"
#endif

void
ImagingResampleHorizontalConvolution8u(UINT32 *lineOut, UINT32 *lineIn,
    int xsize, int *xbounds, float *kk, int kmax)
{
    int xmin, xmax, xx, x;
    float *k;

    for (xx = 0; xx < xsize; xx++) {
        xmin = xbounds[xx * 2 + 0];
        xmax = xbounds[xx * 2 + 1];
        k = &kk[xx * kmax];
        x = xmin;
#ifdef __AVX2__
        __m256 sss256 = _mm256_set1_ps(0.25);
        for (; x < xmax - 1; x += 2) {
            __m256 mmk = _mm256_set1_ps(k[x - xmin]);
            mmk = _mm256_insertf128_ps(mmk, _mm_set1_ps(k[x - xmin + 1]), 1);
            __m256i pix = _mm256_cvtepu8_epi32(*(__m128i *) &lineIn[x]);
            __m256 mul = _mm256_mul_ps(_mm256_cvtepi32_ps(pix), mmk);
            sss256 = _mm256_add_ps(sss256, mul);
        }
        __m128 sss = _mm_add_ps(
            _mm256_castps256_ps128(sss256),
            _mm256_extractf128_ps(sss256, 1));
#else
        __m128 sss = _mm_set1_ps(0.5);
#endif
        for (; x < xmax; x++) {
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
    int y, xx = 0;

#ifdef __AVX2__
    for (; xx < imIn->xsize - 1; xx += 2) {
        __m256 sss = _mm256_set1_ps(0.5);
        for (y = ymin; y < ymax; y++) {
            __m256i pix = _mm256_cvtepu8_epi32(*(__m128i *) &imIn->image32[y][xx]);
            __m256 mmk = _mm256_set1_ps(k[y - ymin]);
            __m256 mul = _mm256_mul_ps(_mm256_cvtepi32_ps(pix), mmk);
            sss = _mm256_add_ps(sss, mul);
        }
        __m256i ssi = _mm256_cvtps_epi32(sss);
        ssi = _mm256_packs_epi32(ssi, ssi);
        ssi = _mm256_packus_epi16(ssi, ssi);
        _mm_storel_epi64((__m128i *) &lineOut[xx], _mm256_castsi256_si128(ssi));
    }
#endif

    for (; xx < imIn->xsize; xx++) {
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
