import { expect, test } from 'vitest'
import { renderHook } from '@testing-library/react-hooks'

import { useDebounce } from './debounce'

test('useDebounce debounces provided value', async () => {
  const { rerender, result, waitForNextUpdate } = renderHook(
    ({ value }) => useDebounce(value),
    { initialProps: { value: 'value' } }
  )

  let [debouncedValue, isDebouncing] = result.current
  expect(debouncedValue).toEqual('value')
  expect(isDebouncing).toEqual(true)
  await waitForNextUpdate()
  ;[debouncedValue, isDebouncing] = result.current
  expect(debouncedValue).toEqual('value')
  expect(isDebouncing).toEqual(false)

  rerender({ value: 'newValue' })
  ;[debouncedValue, isDebouncing] = result.current
  expect(debouncedValue).toEqual('value')
  expect(isDebouncing).toEqual(true)
  await waitForNextUpdate()
  ;[debouncedValue, isDebouncing] = result.current
  expect(debouncedValue).toEqual('newValue')
  expect(isDebouncing).toEqual(false)
})
