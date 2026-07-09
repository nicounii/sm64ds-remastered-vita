#ifndef STDDEF_H
#define STDDEF_H

#include "PR/ultratypes.h"

/* Pull in the system <stddef.h> for size_t, NULL, ptrdiff_t, etc. */
#include_next <stddef.h>

#ifndef offsetof
#define offsetof(st, m) ((size_t)&(((st *)0)->m))
#endif

#endif
