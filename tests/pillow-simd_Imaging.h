// [https://raw.githubusercontent.com/uploadcare/pillow-simd/fd828595fc77f0999481871a766fee6bc4a061eb/libImaging/Imaging.h <- https://raw.githubusercontent.com/uploadcare/pillow-simd/fd828595fc77f0999481871a766fee6bc4a061eb/libImaging/Antialias.c <- https://habr.com/ru/articles/326900/ <- https://habr.com/ru/articles/569204/ <- google:‘masm64 disassembler’]

#define INT16 short /* most things works just fine anyway... */
#define INT32 int

#define INT8  signed char
#define UINT8 unsigned char

#define UINT16 unsigned INT16
#define UINT32 unsigned INT32

/* Handles */

typedef struct ImagingMemoryInstance* Imaging;

typedef struct ImagingAccessInstance* ImagingAccess;
typedef struct ImagingHistogramInstance* ImagingHistogram;
typedef struct ImagingOutlineInstance* ImagingOutline;
typedef struct ImagingPaletteInstance* ImagingPalette;

/* handle magics (used with PyCObject). */
#define IMAGING_MAGIC "PIL Imaging"

/* pixel types */
#define IMAGING_TYPE_UINT8 0
#define IMAGING_TYPE_INT32 1
#define IMAGING_TYPE_FLOAT32 2
#define IMAGING_TYPE_SPECIAL 3 /* check mode for details */

#define IMAGING_MODE_LENGTH 6+1 /* Band names ("1", "L", "P", "RGB", "RGBA", "CMYK", "YCbCr", "BGR;xy") */

struct ImagingMemoryInstance {

    /* Format */
    char mode[IMAGING_MODE_LENGTH]; /* Band names ("1", "L", "P", "RGB", "RGBA", "CMYK", "YCbCr", "BGR;xy") */
    int type;       /* Data type (IMAGING_TYPE_*) */
    int depth;      /* Depth (ignored in this version) */
    int bands;      /* Number of bands (1, 2, 3, or 4) */
    int xsize;      /* Image dimension. */
    int ysize;

    /* Colour palette (for "P" images only) */
    ImagingPalette palette;

    /* Data pointers */
    UINT8 **image8; /* Set for 8-bit images (pixelsize=1). */
    INT32 **image32;    /* Set for 32-bit images (pixelsize=4). */

    /* Internals */
    char **image;   /* Actual raster data. */
    char *block;    /* Set if data is allocated in a single block. */

    int pixelsize;  /* Size of a pixel, in bytes (1, 2 or 4) */
    int linesize;   /* Size of a line, in bytes (xsize * pixelsize) */

    /* Virtual methods */
    void (*destroy)(Imaging im);
};
