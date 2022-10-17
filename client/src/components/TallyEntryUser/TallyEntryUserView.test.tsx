import React from 'react'
import { screen } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import TallyEntryUserView from './TallyEntryUserView'
import { queryClient } from '../../App'
import { withMockFetch, renderWithRouter } from '../testUtilities'
import { tallyEntryApiCalls, tallyEntryUser } from '../_mocks'

const renderView = () =>
  renderWithRouter(
    <QueryClientProvider client={queryClient}>
      <TallyEntryUserView />
    </QueryClientProvider>,
    { route: '/tally-entry' }
  )

describe('TallyEntryUserView', () => {
  it('shows the login start screen when the user has not started logging in', async () => {
    const expectedCalls = [tallyEntryApiCalls.getUser(tallyEntryUser.initial)]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: 'Tally Entry Log In' })
      const logOutLink = screen.getByRole('link', { name: 'Log out' })
      expect(logOutLink).toHaveAttribute('href', '/auth/logout')
    })
  })

  it('shows the login code screen when the user has started logging in but is not confirmed', async () => {
    const expectedCalls = [
      tallyEntryApiCalls.getUser(tallyEntryUser.unconfirmed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: 'Login Code' })
      const logOutLink = screen.getByRole('link', { name: 'Log out' })
      expect(logOutLink).toHaveAttribute('href', '/auth/logout')
    })
  })

  it('polls login status on the login code screen and switches to the tally entry screen once the user is confirmed', async () => {
    const expectedCalls = [
      tallyEntryApiCalls.getUser(tallyEntryUser.unconfirmed),
      tallyEntryApiCalls.getUser(tallyEntryUser.confirmed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: 'Login Code' })
      await screen.findByRole('heading', { name: 'Enter Tallies' })
      const logOutLink = screen.getByRole('link', { name: 'Log out' })
      expect(logOutLink).toHaveAttribute('href', '/auth/logout')
    })
  })
})
