import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from './useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));
    expect(result.current).toBe('initial');
  });

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    );

    expect(result.current).toBe('initial');

    act(() => {
      rerender({ value: 'updated', delay: 500 });
    });
    expect(result.current).toBe('initial'); // Still initial

    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe('updated');
  });

  it('cancels previous debounce on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    );

    act(() => {
      rerender({ value: 'first', delay: 500 });
    });
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(result.current).toBe('initial');

    act(() => {
      rerender({ value: 'second', delay: 500 });
    });
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(result.current).toBe('initial');

    act(() => {
      rerender({ value: 'third', delay: 500 });
    });
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe('third');
  });

  it('respects custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 1000 },
      }
    );

    act(() => {
      rerender({ value: 'updated', delay: 1000 });
    });
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe('initial');

    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe('updated');
  });
});
