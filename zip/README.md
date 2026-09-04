How does basic compression work? The DEFLATE algorithm first uses the LZ77 to find and replace strings with `(distance, length)` using a sliding window, then uses huffman coding.

There is no uniform loseless compression algorithm. In fact, if an algorithm makes even one string smaller, the total compression result across all strings would be strictly larger. Meaning losless compression only works on human data.

Huffman coding works by using basic prefix matching, moving the more frequent to less length and the less frequent to more length. It works if only a list of chars are used and some chars appear a lot.

We download zlib-0.71

```
user@fedora ~/D/zlib> ls
adler32.c   deflate.h   infcodes.c  inftrees.c  minigzip.c  zlib.h
ChangeLog   example.c   infcodes.h  inftrees.h  README      zutil.c
compress.c  gzio.c      inflate.c   infutil.c   trees.c     zutil.h
crc32.c     infblock.c  inflate.h   infutil.h   uncompr.c
deflate.c   infblock.h  inftest.c   Makefile    zconf.h
```

Mainly it's just `deflate.c` and `trees.c` that does the work.

Almost no string matching in practice uses the Knuth algorithm, whether it's in Redis or compression. They usually just use a dummy algorithm.
