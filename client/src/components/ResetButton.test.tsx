import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react'
import ResetButton from './ResetButton'
import * as utilities from './utilities'
import AuthDataProvider from './UserContext'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

apiMock.mockImplementationOnce(async () => ({}))

afterEach(() => {
  apiMock.mockClear()
})

describe('ResetButton', () => {
  it('renders', () => {
    const updateAuditMock = jest.fn()
    const { container } = render(
      <ResetButton electionId="1" updateAudit={updateAuditMock} />
    )
    expect(container).toMatchSnapshot()
  })

  it('does not render when authenticated', async () => {
    apiMock.mockImplementation(async () => ({
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [],
      organizations: [
        {
          id: 'org-id',
          name: 'State',
          elections: [],
        },
      ],
    }))
    const updateAuditMock = jest.fn()
    const { container, queryAllByText } = render(
      <AuthDataProvider>
        <ResetButton electionId="1" updateAudit={updateAuditMock} />
      </AuthDataProvider>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(queryAllByText('Clear & Restart').length).toBe(0)
    expect(container).toMatchSnapshot()
  })

  it('renders disabled', () => {
    const updateAuditMock = jest.fn()
    const { container } = render(
      <ResetButton electionId="1" updateAudit={updateAuditMock} />
    )
    expect(container).toMatchSnapshot()
  })

  it('posts to /audit/reset and calls updateAudit', async () => {
    const updateAuditMock = jest.fn()
    const wrapper = document.createElement('div')
    wrapper.setAttribute('id', 'reset-button-wrapper')

    const { getByText } = render(
      <ResetButton electionId="1" updateAudit={updateAuditMock} />,
      { container: document.body.appendChild(wrapper) }
    )

    fireEvent.click(getByText('Clear & Restart'), { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(1)
    })
  })

  it('handles server errors', async () => {
    const updateAuditMock = jest.fn()
    const wrapper = document.createElement('div')
    wrapper.setAttribute('id', 'reset-button-wrapper')

    const { getByText } = render(
      <ResetButton electionId="1" updateAudit={updateAuditMock} />,
      { container: document.body.appendChild(wrapper) }
    )

    fireEvent.click(getByText('Clear & Restart'), { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })

  it('handles 404 errors', async () => {
    apiMock.mockResolvedValueOnce(null)
    const updateAuditMock = jest.fn()
    const wrapper = document.createElement('div')
    wrapper.setAttribute('id', 'reset-button-wrapper')

    const { getByText } = render(
      <ResetButton electionId="1" updateAudit={updateAuditMock} />,
      { container: document.body.appendChild(wrapper) }
    )

    fireEvent.click(getByText('Clear & Restart'), { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })
})
