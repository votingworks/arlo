import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import {
  render,
  fireEvent,
  waitFor,
  screen,
  within,
} from '@testing-library/react'
import { ToastContainer } from 'react-toastify'
import userEvent from '@testing-library/user-event'
import { Router } from 'react-router-dom'
import { createMemoryHistory } from 'history'
import Ballot from './Ballot'
import { contest, dummyBallots } from './_mocks'
import { findAndCloseToast } from '../testUtilities'

const history = createMemoryHistory()

describe('Ballot', () => {
  it('renders correctly with an unaudited ballot', () => {
    const { container } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={vi.fn()}
          submitBallot={vi.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders correctly with an audited ballot', () => {
    const { container, getByLabelText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={vi.fn()}
          submitBallot={vi.fn()}
          batchId="batch-id-1"
          ballotPosition={313}
        />
      </Router>
    )
    const choiceOneButton = getByLabelText('Choice One')
    expect(choiceOneButton).toBeTruthy()
    expect(choiceOneButton).toBeChecked()
    expect(container).toMatchSnapshot()
  })

  it('switches audit and review views', async () => {
    const { container, getByText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={vi.fn()}
          submitBallot={vi.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    fireEvent.click(getByText('Choice One'), { bubbles: true })

    fireEvent.click(screen.getByRole('button', { name: 'Submit Selections' }), {
      bubbles: true,
    })

    const dialog = (
      await screen.findByRole('heading', {
        name: /Confirm the Ballot Selections/,
      })
    ).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText('Contest Name')
    within(dialog).getByText('Choice One')
    userEvent.click(
      within(dialog).getByRole('button', { name: 'Change Selections' })
    )
    await waitFor(() => {
      expect(dialog).not.toBeInTheDocument()
    })

    expect(getByText('Choice One')).toBeTruthy()
    expect(
      screen.getByRole('button', { name: 'Submit Selections' })
    ).toBeTruthy()
    expect(container).toMatchSnapshot()
  })

  const buttonLabels = ['Blank Vote', 'Not on Ballot']
  buttonLabels.forEach(buttonLabel => {
    it(`selects ${buttonLabel}`, async () => {
      const { container, getByLabelText } = render(
        <Router history={history}>
          <Ballot
            home="/election/1/audit-board/1"
            ballots={dummyBallots.ballots}
            boardName="audit board #1"
            contests={[contest]}
            previousBallot={vi.fn()}
            nextBallot={vi.fn()}
            submitBallot={vi.fn()}
            batchId="batch-id-1"
            ballotPosition={2112}
          />
        </Router>
      )

      fireEvent.click(getByLabelText(buttonLabel), {
        bubbles: true,
      })
      userEvent.click(screen.getByRole('button', { name: 'Submit Selections' }))

      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm the Ballot Selections/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(buttonLabel)

      await waitFor(() => {
        expect(within(dialog).getByText(buttonLabel)).toBeTruthy()
      })

      expect(container).toMatchSnapshot()
    })
  })

  it('toggles and submits comment', async () => {
    const { getByText, getByRole } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={vi.fn()}
          submitBallot={vi.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    const commentInput = getByRole('textbox')
    fireEvent.change(commentInput, { target: { value: 'a test comment' } })

    fireEvent.click(getByText('Choice One'), { bubbles: true })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Selections' }), {
      bubbles: true,
    })

    const dialog = (
      await screen.findByRole('heading', {
        name: /Confirm the Ballot Selections/,
      })
    ).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText('Contest Name')
    within(dialog).getByText('Comment: a test comment')
    userEvent.click(
      within(dialog).getByRole('button', { name: 'Change Selections' })
    )

    await waitFor(() => {
      expect(dialog).not.toBeInTheDocument()
    })

    fireEvent.change(commentInput, { target: { value: '' } })

    fireEvent.click(screen.getByRole('button', { name: 'Submit Selections' }), {
      bubbles: true,
    })

    const dialog2 = (
      await screen.findByRole('heading', {
        name: /Confirm the Ballot Selections/,
      })
    ).closest('.bp3-dialog')! as HTMLElement

    expect(within(dialog2).queryByText('COMMENT:')).toBeFalsy()
  })

  it('submits review and progresses to next ballot', async () => {
    const submitMock = vi.fn()
    const nextBallotMock = vi.fn()
    const { getByText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={nextBallotMock}
          submitBallot={submitMock}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
        <ToastContainer />
      </Router>
    )

    fireEvent.click(getByText('Choice One'), { bubbles: true })

    const reviewButton = screen.getByRole('button', {
      name: 'Submit Selections',
    })
    fireEvent.click(reviewButton, { bubbles: true })

    const dialog = (
      await screen.findByRole('heading', {
        name: /Confirm the Ballot Selections/,
      })
    ).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText('Contest Name')
    within(dialog).getByText('Choice One')
    userEvent.click(
      within(dialog).getByRole('button', { name: 'Confirm Selections' })
    )

    await findAndCloseToast('Success! Now showing the next ballot to audit.')

    await waitFor(() => {
      expect(dialog).not.toBeInTheDocument()
    })

    await waitFor(() => {
      expect(nextBallotMock).toBeCalled()
      expect(submitMock).toHaveBeenCalledTimes(1)
    })
  })

  it('submits review with double click without screwing up', async () => {
    const submitMock = vi.fn()
    const nextBallotMock = vi.fn()
    const { getByText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={nextBallotMock}
          submitBallot={submitMock}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    fireEvent.click(getByText('Choice One'), { bubbles: true })

    const reviewButton = screen.getByRole('button', {
      name: 'Submit Selections',
    })
    fireEvent.click(reviewButton, { bubbles: true })
    const dialog = (
      await screen.findByRole('heading', {
        name: /Confirm the Ballot Selections/,
      })
    ).closest('.bp3-dialog')! as HTMLElement
    within(dialog).getByText('Contest Name')
    within(dialog).getByText('Choice One')
    const confirmButton = within(dialog).getByRole('button', {
      name: 'Confirm Selections',
    })
    fireEvent.click(confirmButton, { bubbles: true }) // the doubleClick event doesn't submit it at all
    fireEvent.click(confirmButton, { bubbles: true }) // but this successfully fails without the Formik double submission protection

    await waitFor(() => {
      expect(dialog).not.toBeInTheDocument()
    })

    await waitFor(() => {
      expect(submitMock).toHaveBeenCalledTimes(1)
      expect(nextBallotMock).toBeCalled()
    })
  })

  it('navigates to previous ballot', async () => {
    const previousBallotMock = vi.fn()
    const { getByText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={previousBallotMock}
          nextBallot={vi.fn()}
          submitBallot={vi.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )
    fireEvent.click(getByText('Back'), { bubbles: true })

    await waitFor(() => {
      expect(previousBallotMock).toBeCalledTimes(1)
    })
  })

  it('redirects if ballot does not exist', async () => {
    const { container } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={vi.fn()}
          nextBallot={vi.fn()}
          submitBallot={vi.fn()}
          batchId="batch-id"
          ballotPosition={6}
        />
      </Router>
    )

    await waitFor(() => {
      expect(container).toMatchSnapshot()
    })
  })
})
