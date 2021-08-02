import React from 'react'
import { render } from '@testing-library/react'
import RoundProgress from './RoundProgress'
import { auditBoardMocks } from '../useSetupMenuItems/_mocks'

describe('RoundProgress', () => {
  it('renders nothing with no audit boards', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.empty} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders incomplete round with an audit board', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.single} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders incomplete round with two audit boards', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.double} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders incomplete round with auditing in progress', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.started} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders incomplete round with an audit board with no ballots sampled', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.noBallots} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders an audit board with auditing complete that has not signed off', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.finished} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders complete round', () => {
    const { container } = render(
      <RoundProgress auditBoards={auditBoardMocks.signedOff} />
    )
    expect(container).toMatchSnapshot()
  })
})
