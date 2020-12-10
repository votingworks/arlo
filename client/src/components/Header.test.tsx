import React from 'react'
import { waitFor, screen } from '@testing-library/react'
import Header from './Header'
import * as utilities from './utilities'
import AuthDataProvider from './UserContext'
import { renderWithRouter } from './testUtilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const renderHeader = (route: string) =>
  renderWithRouter(
    <AuthDataProvider>
      <Header />
    </AuthDataProvider>,
    { route }
  )

afterEach(() => {
  apiMock.mockClear()
})

describe('Header', () => {
  it('renders correctly', async () => {
    apiMock.mockResolvedValue({ user: null, superadminUser: null })
    const { container } = renderHeader('/election/1')
    await screen.findAllByAltText('Arlo, by VotingWorks')
    expect(container).toMatchSnapshot()
  })

  it('shows the logout button when authenticated', async () => {
    apiMock.mockResolvedValue({
      user: {
        type: 'audit_admin',
        name: 'Joe',
        email: 'test@email.org',
        jurisdictions: [],
        organizations: [],
      },
      superadminUser: null,
    })
    renderHeader('/election/1')

    await screen.findByText('Log out')
    expect(apiMock).toHaveBeenCalledTimes(1)
    expect(apiMock).toHaveBeenCalledWith('/me')
  })

  it('does not show logout button if not authenticated', async () => {
    apiMock.mockResolvedValue({ user: null, superadminUser: null })
    renderHeader('/election/1')

    const loginButton = screen.queryByText('Log out')
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/me')
      expect(loginButton).toBeFalsy()
    })
  })

  it('does not show logout button if the authentication verification has a server error', async () => {
    apiMock.mockResolvedValue(null)
    renderHeader('/election/1')

    const loginButton = screen.queryByText('Log out')
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/me')
      expect(loginButton).toBeFalsy()
    })
  })

  it('shows the nav bar when authenticated and there is an electionId', async () => {
    apiMock.mockResolvedValue({
      user: {
        type: 'audit_admin',
        name: 'Joe',
        email: 'test@email.org',
        jurisdictions: [],
        organizations: [],
      },
      superadminUser: null,
    })
    const { container } = renderHeader('/election/1')
    await waitFor(() => {
      expect(screen.getByText('Audit Setup')).toBeTruthy()
      expect(screen.getByText('Audit Progress')).toBeTruthy()
      expect(screen.getByText('View Audits')).toBeTruthy()
      expect(screen.getByText('New Audit')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('shows the active jurisdiction name when authenticated as ja', async () => {
    apiMock.mockResolvedValue({
      user: {
        type: 'jurisdiction_admin',
        name: 'Joe',
        email: 'test@email.org',
        jurisdictions: [
          {
            id: 'jurisdiction-id-1',
            name: 'Jurisdiction One',
          },
          {
            id: 'jurisdiction-id-2',
            name: 'Jurisdiction Two',
          },
        ],
        organizations: [],
      },
      superadminUser: null,
    })
    renderHeader('/election/1/jurisdiction/jurisdiction-id-1')

    await screen.findByText('Jurisdiction: Jurisdiction One')
    expect(apiMock).toHaveBeenCalledTimes(1)
    expect(apiMock).toHaveBeenCalledWith('/me')
  })
})
