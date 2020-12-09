import React from 'react'
import { Route } from 'react-router-dom'
import { screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithRouter, withMockFetch } from '../../../testUtilities'
import relativeStages from '../_mocks'
import Contests from '.'
import { aaApiCalls } from '../../_mocks'
import { IContest, INewContest } from '../../useContestsBallotComparison'

const { nextStage, prevStage } = relativeStages('target-contests')

const render = (isTargeted: boolean = true) =>
  renderWithRouter(
    <Route path="/election/:electionId/setup">
      <Contests
        auditType="BALLOT_COMPARISON"
        locked={false}
        isTargeted={isTargeted}
        nextStage={nextStage}
        prevStage={prevStage}
      />
    </Route>,
    { route: '/election/1/setup' }
  )

const apiCalls = {
  getStandardizedContests: {
    url: '/api/election/1/standardized-contests',
    response: [
      {
        name: 'Contest 1',
        jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      },
      {
        name: 'Contest 2',
        jurisdictionIds: ['jurisdiction-id-1'],
      },
      { name: 'Contest 3', jurisdictionIds: ['jurisdiction-id-2'] },
    ],
  },
  getContests: (contests: IContest[]) => ({
    url: '/api/election/1/contest',
    response: { contests },
  }),
  putContests: (contests: INewContest[]) => ({
    url: '/api/election/1/contest',
    options: {
      method: 'PUT',
      body: JSON.stringify(contests),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  }),
}

jest.mock('uuidv4', () => {
  let id = 0
  return () => {
    id += 1
    return id.toString()
  }
})

describe('Audit Setup > Contests (Ballot Comparison)', () => {
  const expectedNewContestsRequest = [
    {
      name: 'Contest 1',
      id: '1',
      isTargeted: true,
      numWinners: 2,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
    },
    {
      name: 'Contest 2',
      id: '2',
      isTargeted: true,
      numWinners: 1,
      jurisdictionIds: ['jurisdiction-id-1'],
    },
  ]
  const newContests: IContest[] = expectedNewContestsRequest.map(c => ({
    ...c,
    votesAllowed: null,
    totalBallotsCast: null,
    choices: [],
  }))

  it('shows table of standardized contests with checkboxes', async () => {
    const expectedCalls = [
      apiCalls.getStandardizedContests,
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.putContests(expectedNewContestsRequest),
      apiCalls.getContests(newContests),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await screen.findByRole('heading', { name: 'Target Contests' })

      const headers = screen.getAllByRole('columnheader')
      expect(headers).toHaveLength(4)
      expect(headers[0]).toHaveTextContent(/Select/)
      expect(headers[1]).toHaveTextContent(/Contest Name/)
      expect(headers[2]).toHaveTextContent(/Jurisdictions/)
      expect(headers[3]).toHaveTextContent(/Winners/)

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(3 + 1) // Includes headers
      expect(within(rows[1]).getByRole('checkbox')).not.toBeChecked()
      expect(within(rows[1]).getAllByRole('cell')[1]).toHaveTextContent(
        'Contest 1'
      )
      expect(within(rows[1]).getAllByRole('cell')[2]).toHaveTextContent('All')
      expect(within(rows[1]).getByRole('spinbutton')).toBeDisabled()
      expect(within(rows[2]).getByRole('checkbox')).not.toBeChecked()
      expect(within(rows[2]).getAllByRole('cell')[1]).toHaveTextContent(
        'Contest 2'
      )
      expect(within(rows[2]).getAllByRole('cell')[2]).toHaveTextContent(
        'Jurisdiction One'
      )
      expect(within(rows[2]).getByRole('spinbutton')).toBeDisabled()
      expect(within(rows[3]).getByRole('checkbox')).not.toBeChecked()
      expect(within(rows[3]).getAllByRole('cell')[1]).toHaveTextContent(
        'Contest 3'
      )
      expect(within(rows[3]).getAllByRole('cell')[2]).toHaveTextContent(
        'Jurisdiction Two'
      )
      expect(within(rows[3]).getByRole('spinbutton')).toBeDisabled()

      // Select Contest 1
      userEvent.click(within(rows[1]).getByRole('checkbox'))
      expect(within(rows[1]).getByRole('checkbox')).toBeChecked()

      // Adjust num winners
      const winnersInput = within(rows[1]).getByRole('spinbutton')
      expect(winnersInput).toBeEnabled()
      expect(winnersInput).toHaveValue(1)
      userEvent.click(
        within(rows[1]).getByRole('button', { name: 'chevron-up' })
      )
      expect(within(rows[1]).getByRole('spinbutton')).toHaveValue(2)
      userEvent.click(
        within(rows[1]).getByRole('button', { name: 'chevron-up' })
      )

      expect(within(rows[1]).getByRole('spinbutton')).toHaveValue(3)
      userEvent.click(
        within(rows[1]).getByRole('button', { name: 'chevron-down' })
      )
      expect(within(rows[1]).getByRole('spinbutton')).toHaveValue(2)

      // Select Contest 3
      userEvent.click(within(rows[3]).getByRole('checkbox'))
      expect(within(rows[3]).getByRole('checkbox')).toBeChecked()

      // Select Contest 2
      userEvent.click(within(rows[2]).getByRole('checkbox'))
      expect(within(rows[2]).getByRole('checkbox')).toBeChecked()

      // Deselect Contest 3
      userEvent.click(within(rows[3]).getByRole('checkbox'))
      expect(within(rows[3]).getByRole('checkbox')).not.toBeChecked()

      // Submit the form
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('disables already selected targeted contests on opportunistic contest form', async () => {
    const newContest3 = {
      name: 'Contest 3',
      id: '5',
      isTargeted: false,
      numWinners: 1,
      jurisdictionIds: ['jurisdiction-id-2'],
    }
    const expectedCalls = [
      apiCalls.getStandardizedContests,
      apiCalls.getContests(newContests),
      aaApiCalls.getJurisdictions,
      apiCalls.putContests(expectedNewContestsRequest.concat([newContest3])),
      apiCalls.getContests(
        newContests.concat([
          {
            ...newContest3,
            votesAllowed: null,
            totalBallotsCast: null,
            choices: [],
          },
        ])
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(false)
      await screen.findByRole('heading', { name: 'Opportunistic Contests' })

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(3 + 1) // Includes headers
      expect(within(rows[1]).getByRole('checkbox')).toBeChecked()
      expect(within(rows[1]).getByRole('checkbox')).toBeDisabled()
      expect(within(rows[1]).getAllByRole('cell')[1]).toHaveTextContent(
        'Contest 1'
      )
      expect(within(rows[1]).getByRole('spinbutton')).toBeDisabled()

      expect(within(rows[2]).getByRole('checkbox')).toBeChecked()
      expect(within(rows[2]).getByRole('checkbox')).toBeDisabled()
      expect(within(rows[2]).getAllByRole('cell')[1]).toHaveTextContent(
        'Contest 2'
      )
      expect(within(rows[2]).getByRole('spinbutton')).toBeDisabled()

      expect(within(rows[3]).getByRole('checkbox')).not.toBeChecked()
      expect(within(rows[3]).getAllByRole('cell')[1]).toHaveTextContent(
        'Contest 3'
      )
      expect(within(rows[3]).getByRole('spinbutton')).toBeDisabled()

      // Select Contest 3
      userEvent.click(within(rows[3]).getByRole('checkbox'))
      expect(within(rows[3]).getByRole('checkbox')).toBeChecked()

      // Submit the form
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('filters and sorts contests', async () => {
    const expectedCalls = [
      apiCalls.getStandardizedContests,
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await screen.findByRole('heading', { name: 'Target Contests' })

      // Reverse sort by Contest Name
      const contestNameHeader = screen.getByRole('columnheader', {
        name: 'Contest Name',
      })
      userEvent.click(contestNameHeader)
      userEvent.click(contestNameHeader)

      let rows = screen.getAllByRole('row')
      within(rows[1]).getByText('Contest 3')
      within(rows[2]).getByText('Contest 2')
      within(rows[3]).getByText('Contest 1')

      // Select Contest 1
      userEvent.click(within(rows[3]).getByRole('checkbox'))

      // Now reset sorting and confirmed it's still checked
      userEvent.click(contestNameHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByText('Contest 1')
      expect(within(rows[1]).getByRole('checkbox')).toBeChecked()
      expect(within(rows[2]).getByRole('checkbox')).not.toBeChecked()
      expect(within(rows[3]).getByRole('checkbox')).not.toBeChecked()

      // Filter by contest name
      userEvent.type(screen.getByRole('textbox'), 'contest 2')
      rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(1 + 1) // Includes headers
      within(rows[1]).getByText('Contest 2')

      // Select Contest 2
      userEvent.click(within(rows[1]).getByRole('checkbox'))

      // Now reset filter and confirmed it's still checked
      userEvent.clear(screen.getByRole('textbox'))
      rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(3 + 1) // Includes headers
      expect(within(rows[1]).getByRole('checkbox')).toBeChecked()
      expect(within(rows[2]).getByRole('checkbox')).toBeChecked()
      expect(within(rows[3]).getByRole('checkbox')).not.toBeChecked()

      // Filter by jurisdiction name
      userEvent.type(screen.getByRole('textbox'), 'one')
      rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(2 + 1) // Includes headers
      within(rows[1]).getByText('Contest 1')
      within(rows[2]).getByText('Contest 2')

      // Deselect Contest 1
      userEvent.click(within(rows[1]).getByRole('checkbox'))

      // Now reset filter and confirmed it's still unchecked
      userEvent.clear(screen.getByRole('textbox'))
      rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(3 + 1) // Includes headers
      expect(within(rows[1]).getByRole('checkbox')).not.toBeChecked()
      expect(within(rows[2]).getByRole('checkbox')).toBeChecked()
      expect(within(rows[3]).getByRole('checkbox')).not.toBeChecked()
    })
  })
})
