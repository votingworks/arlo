import React from 'react'
import { QueryClientProvider } from 'react-query'
import { render, screen } from '@testing-library/react'
import { tallyEntryApiCalls, contestMocks } from '../_mocks'
import TallyEntryScreen from './TallyEntryScreen'
import { withMockFetch, createQueryClient } from '../testUtilities'
import { batchesMocks } from '../JurisdictionAdmin/_mocks'

const renderScreen = () =>
  render(
    <QueryClientProvider client={createQueryClient()}>
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
      tallyEntryApiCalls.getBatches(batchesMocks.emptyInitial),
      tallyEntryApiCalls.getContests(contestMocks.oneTargeted),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderScreen()
      await screen.findByRole('heading', { name: 'Enter Tallies' })
      expect(screen.getAllByText('Batch One')).toHaveLength(2)
    })
  })
})
