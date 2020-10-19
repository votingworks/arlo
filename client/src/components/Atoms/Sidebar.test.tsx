import React from 'react'
import { render } from '@testing-library/react'
import Sidebar, { ISidebarMenuItem } from './Sidebar'

const mockMenuItems: ISidebarMenuItem[] = [
  {
    id: '1',
    title: 'Item One',
    activate: jest.fn(),
    active: false,
    state: 'live',
  },
  {
    id: '2',
    title: 'Item Two',
    activate: jest.fn(),
    active: false,
    state: 'locked',
  },
  {
    id: '3',
    title: 'Item Three',
    activate: jest.fn(),
    active: false,
    state: 'processing',
  },
  {
    id: '4',
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
