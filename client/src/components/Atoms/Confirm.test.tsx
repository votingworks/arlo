import React from 'react'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Intent } from '@blueprintjs/core'
import { useConfirm, Confirm, IConfirmOptions } from './Confirm'

const confirmMock: IConfirmOptions = {
  title: 'Confirm Component',
  description: (
    <div>
      <p>
        <strong>This action cannot be undone.</strong>
      </p>
    </div>
  ),
  yesButtonLabel: 'Yes',
  yesButtonIntent: Intent.PRIMARY,
  onYesClick: () =>
    new Promise<void>(resolve => {
      resolve()
    }),
}

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useState: jest.fn(),
}))

afterEach(() => {
  jest.clearAllMocks()
})

describe('Confirm component', () => {
  it('opens confirm component', async () => {
    const setOptions = jest.fn()

    // passing default values for state to open the component
    // as state is mocked
    const useStateMock: any = () => [confirmMock, setOptions]
    jest.spyOn(React, 'useState').mockImplementation(useStateMock)

    const { confirm: confirm1, confirmProps: confirmProps1 } = useConfirm()
    confirm1(confirmMock)

    expect(setOptions).toHaveBeenCalledTimes(1)

    const { container } = render(<Confirm {...confirmProps1} />)
    const dialog = (await screen.findByRole('heading', {
      name: /Confirm Component/,
    })).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText('This action cannot be undone.')
    expect(container).toMatchSnapshot()
  })

  it('closes confirm component', async () => {
    const setOptions = jest.fn()

    // passing default values for state to open the component
    // as state is mocked
    const useStateMock: any = () => [confirmMock, setOptions]
    jest.spyOn(React, 'useState').mockImplementation(useStateMock)

    const { confirm: confirm1, confirmProps: confirmProps1 } = useConfirm()
    confirm1(confirmMock)

    expect(setOptions).toHaveBeenCalledTimes(1)

    const { container, rerender } = render(<Confirm {...confirmProps1} />)
    const dialog = (await screen.findByRole('heading', {
      name: /Confirm Component/,
    })).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText('This action cannot be undone.')
    userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))

    // re-mocking state to update the values as
    // state is mocked, setOptions won't update it to close component.
    const useStateMock2: any = () => [null, setOptions]
    jest.spyOn(React, 'useState').mockImplementation(useStateMock2)

    const { confirm: confirm2, confirmProps: confirmProps2 } = useConfirm()
    confirm2(null)

    // re-rendering component to pass null values
    // to not open the popup
    rerender(<Confirm {...confirmProps2} />)

    await waitFor(() => {
      expect(
        screen.queryByText('This action cannot be undone.')
      ).not.toBeInTheDocument()
    })
    expect(container).toMatchSnapshot()
  })
})
