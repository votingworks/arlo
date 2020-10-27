import React from 'react'
import { render, screen } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import BoardTable from './BoardTable'
import { doneDummyBallots, dummyColumnBallots } from './_mocks'

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

  it('renders container and tabulator columns', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={dummyColumnBallots.ballotsBoth.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Audit Board #1: Ballot Cards to Audit')

    expect(screen.getByText('Auditing Complete - Submit Results')).toBeEnabled()

    expect(container).toMatchSnapshot()
  })

  it('renders container and no tabulator columns', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={dummyColumnBallots.ballotsNoTabulator.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Audit Board #1: Ballot Cards to Audit')

    expect(screen.getByText('Auditing Complete - Submit Results')).toBeEnabled()

    expect(container).toMatchSnapshot()
  })

  it('renders tabulator and no container columns', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={dummyColumnBallots.ballotsNoContainer.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Audit Board #1: Ballot Cards to Audit')

    expect(screen.getByText('Auditing Complete - Submit Results')).toBeEnabled()

    expect(container).toMatchSnapshot()
  })

  it('renders no container and no tabulator columns', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={dummyColumnBallots.ballotsNoTabulatorNoContainer.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Audit Board #1: Ballot Cards to Audit')

    expect(screen.getByText('Auditing Complete - Submit Results')).toBeEnabled()

    expect(container).toMatchSnapshot()
  })
})
