import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import ResetButton from './ResetButton'
import api from '../utilities'
import { routerTestProps } from '../testUtilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

const { history } = routerTestProps('/election/:electionId', {
  electionId: '1',
})

jest.mock('../utilities')
apiMock.mockImplementationOnce(() => Promise.resolve({}))

describe('ResetButton', () => {
  it('renders', () => {
    const { container } = render(
      <ResetButton electionId="1" history={history} />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders disabled', () => {
    const { container } = render(
      <ResetButton electionId="1" disabled history={history} />
    )
    expect(container).toMatchSnapshot()
  })

  it('posts to /audit/reset and calls updateAudit', async () => {
    const historySpy = jest.spyOn(history, 'push').mockImplementation()
    const wrapper = document.createElement('div')
    wrapper.setAttribute('id', 'reset-button-wrapper')

    const { getByText } = render(
      <ResetButton electionId="1" history={history} />,
      { container: document.body.appendChild(wrapper) }
    )

    fireEvent.click(getByText('Clear & Restart'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(historySpy).toHaveBeenCalledTimes(1)
    })
  })
})
