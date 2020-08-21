import React from 'react'
import { render, screen } from '@testing-library/react'
import App from './App'
import { withMockFetch } from './components/testUtilities'
import { IUserMeta } from './types'

jest.unmock('react-toastify')

const userMocks: { [key in 'ja' | 'aa']: IUserMeta } = {
  ja: {
    name: 'Han Solo',
    email: 'falcon@gmail.com',
    type: 'jurisdiction_admin',
    organizations: [],
    jurisdictions: [],
  },
  aa: {
    name: 'Han Solo',
    email: 'falcon@gmail.com',
    type: 'audit_admin',
    organizations: [],
    jurisdictions: [],
  },
}

const apiMocks = {
  failedAuth: {
    url: '/api/me',
    response: {},
    error: {
      status: 401,
      statusText: 'UNAUTHORIZED',
    },
  },
  successAuth: (response: IUserMeta) => ({
    url: '/api/me',
    response,
  }),
}

describe('App', () => {
  it('renders unauthenticated properly', async () => {
    const expectedCalls = [apiMocks.failedAuth]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(<App />)
      await screen.findByAltText('Arlo, by VotingWorks')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders ja logged in properly', async () => {
    const expectedCalls = [apiMocks.successAuth(userMocks.ja)]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(<App />)
      await screen.findByAltText('Arlo, by VotingWorks')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders aa logged in properly', async () => {
    const expectedCalls = [apiMocks.successAuth(userMocks.aa)]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(<App />)
      await screen.findByAltText('Arlo, by VotingWorks')
      expect(container).toMatchSnapshot()
    })
  })
})
