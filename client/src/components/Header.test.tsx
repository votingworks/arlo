import React from 'react'
import { waitFor, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Header from './Header'
import * as utilities from './utilities'
import AuthDataProvider from './UserContext'
import { renderWithRouter, withMockFetch } from './testUtilities'
import {
  aaApiCalls,
  apiCalls,
  jaApiCalls,
  superadminApiCalls,
} from './MultiJurisdictionAudit/_mocks'

const renderHeader = (route: string) =>
  renderWithRouter(
    <AuthDataProvider>
      <Header />
    </AuthDataProvider>,
    { route }
  )

describe('Header', () => {
  it('shows just the logo when no authenticated user', async () => {
    const expectedCalls = [apiCalls.unauthenticatedUser]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/')

      // Arlo logo
      const arloLogo = await screen.findByRole('link', {
        name: 'Arlo, by VotingWorks',
      })
      expect(arloLogo).toHaveAttribute('href', '/')
      expect(within(arloLogo).getByRole('img')).toHaveAttribute(
        'src',
        '/arlo.png'
      )

      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  it('shows the authenticated user', async () => {
    const expectedCalls = [aaApiCalls.getUser]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/')

      // Arlo logo
      const arloLogo = await screen.findByRole('link', {
        name: 'Arlo, by VotingWorks',
      })

      // User's email
      const userButton = screen.getByRole('button', {
        name: /auditadmin@email.org/,
      })
      userEvent.click(userButton)

      // Dropdown menu should show with log out option
      const logOutButton = screen.getByRole('link', { name: 'Log out' })
      expect(logOutButton).toHaveAttribute('href', '/auth/logout')
    })
  })

  it('shows just the logo on server error', async () => {
    const expectedCalls = [apiCalls.serverError('/api/me')]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/')

      // Arlo logo
      const arloLogo = await screen.findByRole('link', {
        name: 'Arlo, by VotingWorks',
      })
      expect(arloLogo).toHaveAttribute('href', '/')
      expect(within(arloLogo).getByRole('img')).toHaveAttribute(
        'src',
        '/arlo.png'
      )

      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  it('shows navigation buttons when authenticated on audit screens', async () => {
    const expectedCalls = [aaApiCalls.getUserWithAudit]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/election/1')

      // Arlo logo
      const arloLogo = await screen.findByRole('link', {
        name: 'Arlo, by VotingWorks',
      })

      // Navigation buttons
      const buttons = screen.getAllByRole('button')
      expect(buttons[0]).toHaveTextContent(/Audit Setup/)
      expect(buttons[0]).toHaveAttribute('href', '/election/1/setup')
      expect(buttons[1]).toHaveTextContent(/Audit Progress/)
      expect(buttons[1]).toHaveAttribute('href', '/election/1/progress')
      expect(buttons[2]).toHaveTextContent(/View Audits/)
      expect(buttons[2]).toHaveAttribute('href', '/')
      expect(buttons[3]).toHaveTextContent(/New Audit/)
      expect(buttons[3]).toHaveAttribute('href', '/')

      // User's email
      screen.getByRole('button', {
        name: /auditadmin@email.org/,
      })
    })
  })

  it('shows the active jurisdiction name when authenticated as ja', async () => {
    const expectedCalls = [jaApiCalls.getUser]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/election/1/jurisdiction/jurisdiction-id-1')

      // Arlo logo
      const arloLogo = await screen.findByRole('link', {
        name: 'Arlo, by VotingWorks',
      })

      // Jurisdiction name
      screen.getByText('Jurisdiction: Jurisdiction One')

      // User's email
      const userButton = screen.getByRole('button', {
        name: /jurisdictionadmin@email.org/,
      })
      userEvent.click(userButton)

      // Dropdown menu should show with log out option
      const logOutButton = screen.getByRole('link', { name: 'Log out' })
      expect(logOutButton).toHaveAttribute('href', '/auth/logout')

      // No other buttons
      expect(screen.getAllByRole('button')).toHaveLength(1)
    })
  })

  it('shows Support Tools navbar when authenticated as a superadmin', async () => {
    const expectedCalls = [superadminApiCalls.getUser]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/superadmin/')

      // Support tools link
      const supportToolsLink = await screen.findByRole('link', {
        name: /Support Tools/,
      })
      expect(supportToolsLink).toHaveAttribute('href', '/superadmin/')

      // Superadmin user email
      screen.getByText('superadmin@example.com')

      // Log out button
      const logOutButton = screen.getByRole('link', { name: 'Log out' })
      expect(logOutButton).toHaveAttribute('href', '/auth/logout')

      // No regular navbar
      // TODO once we actually move the Support Tools interface to the React App
      // - currently we don't actually render the navbar on /superadmin/
      // expect(
      //   screen.queryByRole('link', {
      //     name: 'Arlo, by VotingWorks',
      //   })
      // ).not.toBeInTheDocument()
    })
  })

  it('shows both navbars when a superadmin impersonates an audit admin', async () => {
    const expectedCalls = [superadminApiCalls.getUserImpersonatingAA]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/')

      // Support tools navbar

      // Support tools link
      const supportToolsLink = await screen.findByRole('link', {
        name: /Support Tools/,
      })
      expect(supportToolsLink).toHaveAttribute('href', '/superadmin/')

      // Superadmin user email
      screen.getByText('superadmin@example.com')

      // Log out button
      const logOutButton = screen.getByRole('link', { name: 'Log out' })
      expect(logOutButton).toHaveAttribute('href', '/auth/logout')

      // Audit admin navbar

      // Arlo logo
      const arloLogo = screen.getByRole('link', {
        name: 'Arlo, by VotingWorks',
      })

      // User's email
      const userButton = screen.getByRole('button', {
        name: /auditadmin@email.org/,
      })
      userEvent.click(userButton)

      // Dropdown menu should show with log out option
      const aalogOutButton = screen.getAllByRole('link', {
        name: 'Log out',
      })[1]
      expect(aalogOutButton).toHaveAttribute('href', '/auth/logout')
    })
  })

  it('shows both navbars when a superadmin impersonates a jurisdiction admin', async () => {
    const expectedCalls = [superadminApiCalls.getUserImpersonatingJA]
    await withMockFetch(expectedCalls, async () => {
      renderHeader('/')

      // Support tools navbar

      // Support tools link
      const supportToolsLink = await screen.findByRole('link', {
        name: /Support Tools/,
      })
      expect(supportToolsLink).toHaveAttribute('href', '/superadmin/')

      // Superadmin user email
      screen.getByText('superadmin@example.com')

      // Log out button
      const logOutButton = screen.getByRole('link', { name: 'Log out' })
      expect(logOutButton).toHaveAttribute('href', '/auth/logout')

      // Jurisdiction admin navbar

      // Arlo logo
      const arloLogo = screen.getByRole('link', {
        name: 'Arlo, by VotingWorks',
      })

      // User's email
      const userButton = screen.getByRole('button', {
        name: /jurisdictionadmin@email.org/,
      })
      userEvent.click(userButton)

      // Dropdown menu should show with log out option
      const jalogOutButton = screen.getAllByRole('link', {
        name: 'Log out',
      })[1]
      expect(jalogOutButton).toHaveAttribute('href', '/auth/logout')
    })
  })
})
