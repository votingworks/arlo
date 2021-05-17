import React from 'react'
import { render, screen } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import BoardTable from './BoardTable'
import {
  doneDummyBallots,
  dummyColumnBallots,
  dummyBallots,
  dummyBallotsNotAudited,
} from './_mocks'

describe('BoardTable', () => {
  it('shows audit first ballot button when no ballots are audited', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={dummyBallotsNotAudited.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Ballots for Audit Board #1')
    expect(screen.getByRole('button', { name: 'Audit First Ballot' }))
    await screen.findByText('0 of 27 ballots have been audited.')

    expect(
      screen.getByRole('button', {
        name: 'Submit Audited Ballots',
      })
    ).toBeDisabled()

    expect(container).toMatchSnapshot()
  })

  it('shows audit next ballot button when some are remaining to audit', async () => {
    const { container } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={dummyBallots.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await screen.findByText('Ballots for Audit Board #1')

    expect(screen.getByRole('button', { name: 'Audit Next Ballot' }))
    await screen.findByText('18 of 27 ballots have been audited.')
    expect(
      screen.getByRole('button', {
        name: 'Submit Audited Ballots',
      })
    ).toBeDisabled()

    expect(container).toMatchSnapshot()
  })

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
    await screen.findByText('Ballots for Audit Board #1')

    screen.getByText('Not Found')
    const submitBallotsBtn = screen.getAllByText('Submit Audited Ballots')
    expect(submitBallotsBtn.length).toBe(2)
    // assert bottom button to be enabled
    expect(submitBallotsBtn[1]).toBeEnabled()

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
    await screen.findByText('Ballots for Audit Board #1')

    const submitBallotsBtn = screen.getAllByText('Submit Audited Ballots')
    expect(submitBallotsBtn.length).toBe(2)
    // assert bottom button to be enabled
    expect(submitBallotsBtn[1]).toBeEnabled()

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
    await screen.findByText('Ballots for Audit Board #1')

    const submitBallotsBtn = screen.getAllByText('Submit Audited Ballots')
    expect(submitBallotsBtn.length).toBe(2)
    // assert bottom button to be enabled
    expect(submitBallotsBtn[1]).toBeEnabled()

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
    await screen.findByText('Ballots for Audit Board #1')

    const submitBallotsBtn = screen.getAllByText('Submit Audited Ballots')
    expect(submitBallotsBtn.length).toBe(2)
    // assert bottom button to be enabled
    expect(submitBallotsBtn[1]).toBeEnabled()

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
    await screen.findByText('Ballots for Audit Board #1')

    const submitBallotsBtn = screen.getAllByText('Submit Audited Ballots')
    expect(submitBallotsBtn.length).toBe(2)
    // assert bottom button to be enabled
    expect(submitBallotsBtn[1]).toBeEnabled()

    expect(container).toMatchSnapshot()
  })
})
