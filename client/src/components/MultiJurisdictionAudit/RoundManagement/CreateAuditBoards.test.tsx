import React from 'react'
import { render, waitFor, fireEvent } from '@testing-library/react'
import CreateAuditBoards from './CreateAuditBoards'

test('names audit boards numerically', async () => {
  const createAuditBoards = jest.fn()
  const { getByText, getByTestId } = render(
    <CreateAuditBoards createAuditBoards={createAuditBoards} />
  )

  fireEvent.change(getByTestId('numAuditBoards'), { target: { value: '3' } })
  fireEvent.click(getByText('Save & Next'))

  await waitFor(() => {
    expect(createAuditBoards).toHaveBeenCalledWith([
      { name: 'Audit Board #1' },
      { name: 'Audit Board #2' },
      { name: 'Audit Board #3' },
    ])
  })
})

test('names audit boards such that the names sort sensibly', async () => {
  const createAuditBoards = jest.fn()
  const { getByText, getByTestId } = render(
    <CreateAuditBoards createAuditBoards={createAuditBoards} />
  )

  fireEvent.change(getByTestId('numAuditBoards'), { target: { value: '10' } })
  fireEvent.click(getByText('Save & Next'))

  await waitFor(() => {
    expect(createAuditBoards).toHaveBeenCalledWith([
      { name: 'Audit Board #01' },
      { name: 'Audit Board #02' },
      { name: 'Audit Board #03' },
      { name: 'Audit Board #04' },
      { name: 'Audit Board #05' },
      { name: 'Audit Board #06' },
      { name: 'Audit Board #07' },
      { name: 'Audit Board #08' },
      { name: 'Audit Board #09' },
      { name: 'Audit Board #10' },
    ])
  })
})
