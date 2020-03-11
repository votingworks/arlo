import React from 'react'
import { render, wait } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import BoardTable from './BoardTable'
import { doneDummyBallots } from './_mocks'

describe('BoardTable', () => {
  it('loads a completion button when all ballots are done', async () => {
    const { container, getByText } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={doneDummyBallots.ballots}
          round={1}
          url="/home"
          isLoading={false}
          setIsLoading={jest.fn()}
        />
      </StaticRouter>
    )
    await wait(() => {
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(getByText('Review Complete - Finish Round')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })
})
