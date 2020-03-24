import React from 'react'
import { render } from '@testing-library/react'
import Sidebar, { ISidebarMenuItem } from './Sidebar'

const mockMenuItems: ISidebarMenuItem[] = [
  {
    title: 'Item One',
    activate: jest.fn(),
    active: false,
    state: 'live',
  },
  {
    title: 'Item Two',
    activate: jest.fn(),
    active: false,
    state: 'locked',
  },
  {
    title: 'Item Three',
    activate: jest.fn(),
    active: false,
    state: 'processing',
  },
  {
    title: 'Item Four',
    activate: jest.fn(),
    active: true,
    state: 'live',
  },
]

describe('Sidebar', () => {
  it('renders all options', () => {
    const { container } = render(
      <Sidebar menuItems={mockMenuItems} title="Test Sidebar" />
    )
    expect(container).toMatchSnapshot()
  })
})
