#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * Fixed-size chunk memory pool allocator.
 */
typedef struct MemoryBlock {
    size_t size;
    int is_free;
    struct MemoryBlock* next;
} MemoryBlock;

/**
 * Allocates a fixed-size memory chunk from pool buffer.
 */
void* pool_allocate(size_t size) {
    if (size == 0) {
        return NULL;
    }
    MemoryBlock* block = (MemoryBlock*)malloc(sizeof(MemoryBlock) + size);
    if (!block) {
        return NULL;
    }
    block->size = size;
    block->is_free = 0;
    block->next = NULL;
    return (void*)(block + 1);
}

/**
 * Frees previously allocated memory chunk back to pool.
 */
void pool_free(void* ptr) {
    if (!ptr) {
        return;
    }
    MemoryBlock* block = ((MemoryBlock*)ptr) - 1;
    block->is_free = 1;
    free(block);
}
