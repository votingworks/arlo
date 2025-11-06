import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render } from '@testing-library/react'
import Sidebar, { ISidebarMenuItem } from './Sidebar'

const mockMenuItems: ISidebarMenuItem[] = [
  {
    id: '1',
    text: 'Item One',
    onClick: vi.fn(),
    active: false,
  },
  {
    id: '2',
    text: 'Item Two',
    onClick: vi.fn(),
    active: false,
    disabled: true,
  },
  {
    id: '3',
    text: 'Item Three',
    onClick: vi.fn(),
    active: false,
  },
  {
    id: '4',
    text: 'Item Four',
    onClick: vi.fn(),
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
