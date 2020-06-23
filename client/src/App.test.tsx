import React from 'react'
import { render, screen } from '@testing-library/react'
import App from './App'
import * as utilities from './components/utilities'

jest.unmock('react-toastify')
jest.spyOn(utilities, 'api')

describe('App', () => {
  it('renders properly', async () => {
    const { container } = render(<App />)
    await screen.findByAltText('Arlo, by VotingWorks')
    expect(container).toMatchSnapshot()
  })
})
