import React from 'react'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@blueprintjs/core'
import { useConfirm, Confirm } from './Confirm'

const onYesClickMock = jest.fn().mockResolvedValue(true)

const ConfirmConsumer = () => {
  const { confirm, confirmProps } = useConfirm()
  return (
    <>
      <Button
        onClick={() =>
          confirm({
            title: 'Test Title',
            description:
              'This action cannot be undone. Do you want to continue?',
            onYesClick: onYesClickMock,
            yesButtonLabel: 'Yes',
          })
        }
      >
        Open Confirm
      </Button>
      <Confirm {...confirmProps} />
    </>
  )
}

afterEach(() => {
  jest.clearAllMocks()
})

describe('Confirm component', () => {
  it('opens confirm component', async () => {
    render(<ConfirmConsumer />)

    userEvent.click(screen.getByRole('button', { name: 'Open Confirm' }))

    const dialog = (await screen.findByRole('heading', {
      name: /Test Title/,
    })).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText(
      'This action cannot be undone. Do you want to continue?'
    )
  })

  it('closes confirm component when cancelled', async () => {
    render(<ConfirmConsumer />)

    userEvent.click(screen.getByRole('button', { name: 'Open Confirm' }))

    const dialog = (await screen.findByRole('heading', {
      name: /Test Title/,
    })).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText(
      'This action cannot be undone. Do you want to continue?'
    )

    userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))

    await waitFor(() => {
      expect(
        screen.queryByText(
          'This action cannot be undone. Do you want to continue?'
        )
      ).not.toBeInTheDocument()
    })
  })

  it('closes confirm component when clicked on Yes', async () => {
    render(<ConfirmConsumer />)

    userEvent.click(screen.getByRole('button', { name: 'Open Confirm' }))

    const dialog = (await screen.findByRole('heading', {
      name: /Test Title/,
    })).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText(
      'This action cannot be undone. Do you want to continue?'
    )

    userEvent.click(within(dialog).getByRole('button', { name: 'Yes' }))

    expect(onYesClickMock).toHaveBeenCalled()

    await waitFor(() => {
      expect(
        screen.queryByText(
          'This action cannot be undone. Do you want to continue?'
        )
      ).not.toBeInTheDocument()
    })
  })
})
