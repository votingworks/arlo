import React from 'react'
import { fireEvent, screen } from '@testing-library/react'
import { RouteComponentProps } from 'react-router-dom'
import CreateSingleJurisdictionAudit from './CreateSingleJurisdictionAudit'
import {
  routerTestProps,
  withMockFetch,
  renderWithRouter,
} from './components/testUtilities'

const routeProps: RouteComponentProps<{}> = routerTestProps('/audit', {})
routeProps.history.push = jest.fn()

const apiCalls = {
  putAudit: {
    url: '/api/election/new',
    options: {
      method: 'POST',
      body: JSON.stringify({
        auditName: 'Audit Name',
        isMultiJurisdiction: false,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { electionId: '12345' },
  },
}

const renderView = () =>
  renderWithRouter(<CreateSingleJurisdictionAudit {...routeProps} />, {
    route: '/audit',
  })

describe('CreateSingleJurisdictionAudit', () => {
  it('calls the /api/election/new endpoint for nonauthenticated user', async () => {
    const expectedCalls = [apiCalls.putAudit]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()

      fireEvent.change(
        await screen.findByLabelText('Give your new audit a unique name.'),
        {
          target: { value: 'Audit Name' },
        }
      )
      expect(container).toMatchSnapshot()

      fireEvent.click(screen.getByText('Create a New Audit'), { bubbles: true })

      await expect(routeProps.history.push).toHaveBeenCalledTimes(1)
    })
  })
})
