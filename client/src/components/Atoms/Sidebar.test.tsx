import React from 'react'
import { render } from '@testing-library/react'
import Sidebar, { ISidebarMenuItem } from './Sidebar'

const mockMenuItems: ISidebarMenuItem[] = [
  {
    id: '1',
    text: 'Item One',
    onClick: jest.fn(),
    active: false,
  },
  {
    id: '2',
    text: 'Item Two',
    onClick: jest.fn(),
    active: false,
    disabled: true,
  },
  {
    id: '3',
    text: 'Item Three',
    onClick: jest.fn(),
    active: false,
  },
  {
    id: '4',
    text: 'Item Four',
    onClick: jest.fn(),
    active: true,
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
