import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import MemberForm from './MemberForm'
import { statusStates } from '../Audit/_mocks'
import { dummyBoard, dummyBallots } from './_mocks'
import * as utilities from '../utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

const dummy = statusStates[3]
dummy.jurisdictions[0].auditBoards = [dummyBoard[0]]

apiMock
  .mockImplementationOnce(async () => dummy)
  .mockImplementationOnce(async () => dummyBallots)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

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
    names.forEach(nameInput => {
      fireEvent.change(nameInput, { target: { value: 'my name' } })
      expect(nameInput.value)
    })
    parties.forEach(partyInput => {
      fireEvent.click(partyInput, { bubbles: true })
    })

    const nextButton = getByText('Next')
    fireEvent.click(nextButton, { bubbles: true })
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
    })
  })

  it('handles server errors', async () => {
    const updateAuditMock = jest.fn()
    checkAndToastMock.mockReturnValue(true)
    const { queryAllByLabelText, getByText } = render(
      <MemberForm
        boardName="board name"
        jurisdictionName="jurisdiction name"
        updateAudit={updateAuditMock}
        boardId="123"
        jurisdictionId="321"
        electionId="1"
      />
    )

    const names = queryAllByLabelText('Full Name') as HTMLInputElement[]
    names.forEach(nameInput => {
      fireEvent.change(nameInput, { target: { value: 'my name' } })
      expect(nameInput.value)
    })

    const nextButton = getByText('Next')
    fireEvent.click(nextButton, { bubbles: true })
    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(checkAndToastMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })
})
