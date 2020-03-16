import React from 'react'
import { statusStates } from '../_mocks'
import * as utilities from '../../utilities'
import { asyncActRender } from '../../testUtilities'
import Setup from './index'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('Setup', () => {
  it('renders Participants stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Participants"
        setStage={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Target Contests"
        setStage={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Opportunistic Contests"
        setStage={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Audit Settings"
        setStage={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Review & Launch"
        setStage={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })
})
