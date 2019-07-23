import React from 'react'
// import { render } from '@testing-library/react'
import { shallow } from 'enzyme'
import AuditForms from './RiskLimitingAuditForm'

it('renders correctly', () => {
  const container = shallow(<AuditForms />)
  expect(container).toMatchSnapshot()
})
