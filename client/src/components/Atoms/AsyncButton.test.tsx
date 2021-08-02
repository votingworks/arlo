import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AsyncButton from './AsyncButton'

const asyncMock = (): [
  () => Promise<unknown>,
  () => unknown,
  () => unknown
] => {
  let resolvePromise = () => {}
  let rejectPromise = () => {}
  const promise = new Promise((resolve, reject) => {
    resolvePromise = resolve
    rejectPromise = reject
  })
  const mock = jest.fn().mockReturnValue(promise)
  return [mock, resolvePromise, rejectPromise]
}

describe('AsyncButton', () => {
  it('disables the button until onClick resolves', async () => {
    const [onClickMock, resolve] = asyncMock()
    render(<AsyncButton onClick={onClickMock}>Download</AsyncButton>)
    userEvent.click(screen.getByRole('button', { name: 'Download' }))
    expect(screen.getByRole('button')).toBeDisabled()
    resolve()
    await waitFor(() => expect(screen.getByRole('button')).toBeEnabled())
  })

  it('disables the button until onClick rejects', async () => {
    const [onClickMock, _, reject] = asyncMock()
    render(<AsyncButton onClick={onClickMock}>Download</AsyncButton>)
    userEvent.click(screen.getByRole('button', { name: 'Download' }))
    expect(screen.getByRole('button')).toBeDisabled()
    reject()
    await waitFor(() => expect(screen.getByRole('button')).toBeEnabled())
  })
})
