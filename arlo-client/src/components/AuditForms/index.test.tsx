import React from 'react'
import { render } from '@testing-library/react'
import AuditForms from '.'
import { routerTestProps } from '../testUtilities'

it('renders correctly', () => {
  const { history, location, match } = routerTestProps(
    '/election/:electionId',
    { electionId: '1' }
  )
  const container = render(
    <AuditForms history={history} location={location} match={match} />
  )
  expect(container).toMatchSnapshot()
})
