import React from 'react'
import { render } from '@testing-library/react'
import { RouteComponentProps } from 'react-router-dom'
import Header from './Header'
import { ICreateAuditParams } from '../types'
import { routerTestProps } from './testUtilities'

const routeProps: RouteComponentProps<ICreateAuditParams> = routerTestProps(
  '/election/:electionId',
  {
    electionId: '1',
  }
)

it('renders correctly', () => {
  const { container } = render(<Header {...routeProps} />)
  expect(container).toMatchSnapshot()
})
