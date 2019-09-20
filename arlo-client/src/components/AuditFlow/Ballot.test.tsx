import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import Ballot from './Ballot'
import { dummyBoard } from './_mocks'

describe('Ballot', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Ballot
        home="/election/1/board/1"
        roundId="1"
        ballotId="1"
        board={dummyBoard[2]}
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('switches audit and review views', async () => {
    const { container, getByText, getByTestId } = render(
      <Ballot
        home="/election/1/board/1"
        roundId="1"
        ballotId="1"
        board={dummyBoard[2]}
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={jest.fn()}
      />
    )

    fireEvent.click(getByTestId('YES'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('toggles and submits comment', async () => {
    const { container, getByText, getByTestId } = render(
      <Ballot
        home="/election/1/board/1"
        roundId="1"
        ballotId="1"
        board={dummyBoard[2]}
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={jest.fn()}
      />
    )

    fireEvent.click(getByText('Add comment'), { bubbles: true })
    await wait(() => {
      const commentInput = getByTestId('comment-textarea')
      fireEvent.change(commentInput, { target: { value: 'a test comment' } })
    })

    fireEvent.click(getByTestId('YES'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(getByText('COMMENT: a test comment')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })
})
