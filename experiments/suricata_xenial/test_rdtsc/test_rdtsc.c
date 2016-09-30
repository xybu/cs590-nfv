#include <stdint.h>

uint64_t UtilCpuGetTicks(void) {
    uint64_t val;
#if defined(__GNUC__) && (defined(__x86_64) || defined(_X86_64_) || defined(ia_64) || defined(__i386__))
#if defined(__x86_64) || defined(_X86_64_) || defined(ia_64)
    __asm__ __volatile__ (
    "xorl %%eax,%%eax\n\t"
    "cpuid\n\t"
    ::: "%rax", "%rbx", "%rcx", "%rdx");
#else
    __asm__ __volatile__ (
    "xorl %%eax,%%eax\n\t"
    "pushl %%ebx\n\t"
    "cpuid\n\t"
    "popl %%ebx\n\t"
    ::: "%eax", "%ecx", "%edx");
#endif
    uint32_t a, d;
    __asm__ __volatile__ ("rdtsc" : "=a" (a), "=d" (d));
    val = ((uint64_t)a) | (((uint64_t)d) << 32);
#if defined(__x86_64) || defined(_X86_64_) || defined(ia_64)
    __asm__ __volatile__ (
    "xorl %%eax,%%eax\n\t"
    "cpuid\n\t"
    ::: "%rax", "%rbx", "%rcx", "%rdx");
#else
    __asm__ __volatile__ (
    "xorl %%eax,%%eax\n\t"
    "pushl %%ebx\n\t"
    "cpuid\n\t"
    "popl %%ebx\n\t"
    ::: "%eax", "%ecx", "%edx");
#endif

#else /* #if defined(__GNU__) */
#warning Using inferior version of UtilCpuGetTicks
    struct timeval now;
    gettimeofday(&now, NULL);
    val = (now.tv_sec * 1000000) + now.tv_usec;
#endif
    return val;
}

int main(void) {
	int i;
	uint64_t v;

	for (i = 0; i < 100000000; ++i) {
		v = UtilCpuGetTicks();
	}

	return 0;
}
