import React from 'react'
import { render, screen } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import BoardTable from './BoardTable'
import { doneDummyBallots } from './_mocks'

describe('BoardTable', () => {
  it('enables the submit button when all ballots are done', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={doneDummyBallots.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Audit Board #1: Ballot Cards to Audit')

    screen.getByText('Not Found')
    expect(screen.getByText('Auditing Complete - Submit Results')).toBeEnabled()

    expect(container).toMatchSnapshot()
  })
})
