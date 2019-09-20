import React from 'react'
import { render } from '@testing-library/react'
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
})
