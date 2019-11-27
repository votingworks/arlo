import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import MemberForm from './MemberForm'
import { api } from '../utilities'
import { statusStates } from '../AuditForms/_mocks'
import { dummyBoard, dummyBallots } from './_mocks'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

const dummy = statusStates[3]
dummy.jurisdictions[0].auditBoards = [dummyBoard[0]]

apiMock
  .mockImplementationOnce(async () => dummy)
  .mockImplementationOnce(async () => dummyBallots)

describe('MemberForm', () => {
  it('renders correctly', () => {
    const { container } = render(
      <MemberForm
        boardName="board name"
        jurisdictionName="jurisdiction name"
        updateAudit={jest.fn()}
        boardId="123"
        jurisdictionId="321"
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('handles inputs', async () => {
    const { queryAllByLabelText, queryAllByText, getByText } = render(
      <MemberForm
        boardName="board name"
        jurisdictionName="jurisdiction name"
        updateAudit={jest.fn()}
        boardId="123"
        jurisdictionId="321"
        electionId="1"
      />
    )

    const names = queryAllByLabelText('Full Name') as HTMLInputElement[]
    const parties = queryAllByText('Democrat') as HTMLInputElement[]
    expect(names.length).toBe(2)
    expect(parties.length).toBe(2)
    names &&
      names.forEach(nameInput => {
        fireEvent.change(nameInput, { target: { value: 'my name' } })
        expect(nameInput.value)
      })
    parties &&
      parties.forEach(partyInput => {
        fireEvent.click(partyInput, { bubbles: true })
      })

    const nextButton = getByText('Next')
    fireEvent.click(nextButton, { bubbles: true })
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
    })
  })
})
