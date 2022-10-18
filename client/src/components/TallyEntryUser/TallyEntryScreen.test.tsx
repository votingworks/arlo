import React from 'react'
import { QueryClientProvider } from 'react-query'
import { render, screen } from '@testing-library/react'
import { tallyEntryApiCalls } from '../_mocks'
import TallyEntryScreen from './TallyEntryScreen'
import { queryClient } from '../../App'
import { withMockFetch } from '../testUtilities'
import { contestMocks } from '../AuditAdmin/useSetupMenuItems/_mocks'
import { batchesMocks } from '../JurisdictionAdmin/_mocks'

const renderScreen = () =>
  render(
    <QueryClientProvider client={queryClient}>
      <TallyEntryScreen
        electionId="1"
        jurisdictionId="jurisdiction-id-1"
        roundId="round-1"
      />
    </QueryClientProvider>
  )

describe('TallyEntryScreen', () => {
  it('shows batch tally results', async () => {
    const expectedCalls = [
      tallyEntryApiCalls.getContests(contestMocks.oneTargeted),
      tallyEntryApiCalls.getBatches(batchesMocks.emptyInitial),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderScreen()
      await screen.findByRole('heading', { name: 'Enter Tallies' })
      screen.getByText(
        'For each batch, enter the number of votes tallied for each candidate/choice.'
      )
      screen.getByText('Batch One')
      // TODO fill in comprehensive tests once the tally entry interface is finalized
    })
  })
})
