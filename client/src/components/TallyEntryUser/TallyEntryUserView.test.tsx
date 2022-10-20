import React from 'react'
import { screen } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import TallyEntryUserView from './TallyEntryUserView'
import { queryClient } from '../../App'
import { withMockFetch, renderWithRouter } from '../testUtilities'
import { tallyEntryApiCalls, tallyEntryUser, apiCalls } from '../_mocks'
import { contestMocks } from '../AuditAdmin/useSetupMenuItems/_mocks'
import { batchesMocks } from '../JurisdictionAdmin/_mocks'

const renderView = ({ route = '/tally-entry' }: { route?: string } = {}) =>
  renderWithRouter(
    <QueryClientProvider client={queryClient}>
      <TallyEntryUserView />
    </QueryClientProvider>,
    { route }
  )

describe('TallyEntryUserView', () => {
  it('shows an error screen when the user is not logged in', async () => {
    const expectedCalls = [apiCalls.unauthenticatedUser]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: "You're logged out" })
      screen.getByText('To log in, enter your login link in the URL bar.')
    })
  })

  it('shows an error screen when the user types the wrong login link', async () => {
    const expectedCalls = [apiCalls.unauthenticatedUser]
    await withMockFetch(expectedCalls, async () => {
      renderView({ route: '/tally-entry?error=login_link_not_found' })
      await screen.findByRole('heading', {
        name: "We couldn't find the login link you entered",
      })
      screen.getByText(
        'Did you make a typo? Please try entering your login link again.'
      )
    })
  })

  it('shows the login start screen when the user has not started logging in', async () => {
    const expectedCalls = [tallyEntryApiCalls.getUser(tallyEntryUser.initial)]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: 'Tally Entry Login' })
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
      tallyEntryApiCalls.getContests(contestMocks.oneTargeted),
      tallyEntryApiCalls.getBatches(batchesMocks.emptyInitial),
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
