import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import TallyEntryLoginScreen, {
  ITallyEntryLoginScreenProps,
} from './TallyEntryLoginScreen'
import { tallyEntryUser, tallyEntryApiCalls } from '../_mocks'
import { withMockFetch, createQueryClient } from '../testUtilities'

const renderScreen = (props: ITallyEntryLoginScreenProps) =>
  render(
    <QueryClientProvider client={createQueryClient()}>
      <TallyEntryLoginScreen {...props} />
    </QueryClientProvider>
  )

describe('TallyEntryLoginScreen', () => {
  it('when login not started, shows a form to enter member names and start login', async () => {
    const expectedCalls = [
      tallyEntryApiCalls.postRequestLoginCode({
        members: [
          { name: 'John Doe', affiliation: 'DEM' },
          { name: 'Jane Smith', affiliation: null },
        ],
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderScreen({ user: tallyEntryUser.initial })
      screen.getByRole('heading', { name: 'Tally Entry Login' })
      screen.getByText('Jurisdiction One — Test Audit')

      const [nameInput1, nameInput2] = screen.getAllByLabelText('Name')
      const [partySelect1, _partySelect2] = screen.getAllByLabelText(
        'Party Affiliation (if required)'
      )
      const loginButton = screen.getByRole('button', { name: 'Log In' })

      userEvent.type(nameInput1, 'John Doe')
      userEvent.selectOptions(partySelect1, 'Democrat')
      userEvent.type(nameInput2, 'Jane Smith')
      expect(_partySelect2).toHaveValue('')

      userEvent.click(loginButton)
      await waitFor(() => {
        expect(loginButton).toBeDisabled()
      })
    })
  })

  it('in login form, requires one member name, but nothing more', async () => {
    const expectedCalls = [
      tallyEntryApiCalls.postRequestLoginCode({
        members: [{ name: 'John Doe', affiliation: null }],
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderScreen({ user: tallyEntryUser.initial })
      screen.getByRole('heading', { name: 'Tally Entry Login' })

      const [nameInput1] = screen.getAllByLabelText('Name')
      const loginButton = screen.getByRole('button', { name: 'Log In' })

      // First member name is required
      userEvent.click(loginButton)
      await screen.findByText('Enter your name')

      userEvent.type(nameInput1, 'John Doe')
      await waitFor(() => {
        expect(screen.queryByText('Enter your name')).not.toBeInTheDocument()
      })

      userEvent.click(loginButton)
      await waitFor(() => {
        expect(loginButton).toBeDisabled()
      })
    })
  })

  it('shows the login code once the user has requested it', () => {
    renderScreen({ user: tallyEntryUser.unconfirmed })
    screen.getByRole('heading', { name: 'Login Code' })
    screen.getByText('Jurisdiction One — Test Audit')

    screen.getByText('123')
    screen.getByText('Tell your login code to the person running your audit.')
  })
})
