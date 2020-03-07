import React from 'react'
import { render, wait } from '@testing-library/react'
import { BrowserRouter as Router } from 'react-router-dom'
import Header from './Header'
import * as utilities from './utilities'
import { asyncActRender } from './testUtilities'
import AuthDataProvider from './UserContext'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('Header', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Router>
        <Header />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('shows the logout button when authenticated', async () => {
    apiMock.mockImplementation(async () => ({
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [],
      organizations: [],
    }))
    const { queryByText } = await asyncActRender(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )

    const loginButton = queryByText('Log out')
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/auth/me')
      expect(loginButton).toBeTruthy()
    })
  })

  it('does not show logout button if not authenticated', async () => {
    apiMock.mockImplementation(async () => ({}))
    const { queryByText } = await asyncActRender(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )

    const loginButton = queryByText('Log out')
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/auth/me')
      expect(loginButton).toBeFalsy()
    })
  })

  it('does not show logout button if the authentication verification has a server error', async () => {
    checkAndToastMock.mockReturnValue(true)
    apiMock.mockImplementation(async () => ({}))
    const { queryByText } = await asyncActRender(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )

    const loginButton = queryByText('Log out')
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/auth/me')
      expect(loginButton).toBeFalsy()
    })
  })
})
