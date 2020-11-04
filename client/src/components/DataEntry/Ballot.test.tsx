import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react'
import { Router } from 'react-router-dom'
import { createMemoryHistory } from 'history'
import Ballot from './Ballot'
import { contest, dummyBallots } from './_mocks'

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
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
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
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
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
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    fireEvent.click(getByText('Choice One'), { bubbles: true })
    await waitFor(() => fireEvent.click(getByText('Review'), { bubbles: true }))
    await waitFor(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
    })
    await waitFor(() => {
      expect(container).toMatchSnapshot()
    })
    fireEvent.click(getByText('Edit'), { bubbles: true })
    await waitFor(() => {
      expect(getByText('Choice One')).toBeTruthy()
      expect(getByText('Review')).toBeTruthy()
    })
  })

  const buttonLabels = ['Blank vote', 'Not on Ballot']
  buttonLabels.forEach(buttonLabel => {
    it(`selects ${buttonLabel}`, async () => {
      const { container, getByLabelText, getByText } = render(
        <Router history={history}>
          <Ballot
            home="/election/1/audit-board/1"
            ballots={dummyBallots.ballots}
            boardName="audit board #1"
            contests={[contest]}
            previousBallot={jest.fn()}
            nextBallot={jest.fn()}
            submitBallot={jest.fn()}
            batchId="batch-id-1"
            ballotPosition={2112}
          />
        </Router>
      )

      fireEvent.click(getByLabelText(buttonLabel), {
        bubbles: true,
      })
      await waitFor(() =>
        fireEvent.click(getByText('Review'), { bubbles: true })
      )
      await waitFor(() =>
        expect(getByText('Submit & Next Ballot')).toBeTruthy()
      )
      await waitFor(() => {
        expect(getByText(buttonLabel)).toBeTruthy()
        expect(container).toMatchSnapshot()
      })
    })
  })

  it('toggles and submits comment', async () => {
    const { container, getByText, queryByText, getByRole } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    fireEvent.click(getByText('Add comment'), { bubbles: true })

    const commentInput = getByRole('textbox')
    fireEvent.change(commentInput, { target: { value: 'a test comment' } })

    fireEvent.click(getByText('Choice One'), { bubbles: true })
    await waitFor(() => fireEvent.click(getByText('Review'), { bubbles: true }))
    await waitFor(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(getByText('COMMENT: a test comment')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })

    // Go back and make sure an empty comment doesn't get saved
    fireEvent.click(getByText('Edit'), { bubbles: true })

    fireEvent.change(commentInput, { target: { value: '' } })

    fireEvent.click(getByText('Choice One'), { bubbles: true })
    await waitFor(() => fireEvent.click(getByText('Review'), { bubbles: true }))
    await waitFor(() => {
      expect(queryByText('COMMENT:')).toBeFalsy()
    })
  })

  it('toggles and deletes a comment', async () => {
    const { container, getByText, queryByText, getByRole } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    fireEvent.click(getByText('Add comment'), { bubbles: true })

    const commentInput = getByRole('textbox')
    fireEvent.change(commentInput, { target: { value: 'a test comment' } })

    fireEvent.click(getByText('Remove comment'), { bubbles: true })

    fireEvent.click(getByText('Choice One'), { bubbles: true })
    await waitFor(() => fireEvent.click(getByText('Review'), { bubbles: true }))
    await waitFor(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(queryByText('COMMENT: a test comment')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })

  it('submits review and progresses to next ballot', async () => {
    const submitMock = jest.fn()
    const nextBallotMock = jest.fn()
    const { getByText, findByText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={jest.fn()}
          nextBallot={nextBallotMock}
          submitBallot={submitMock}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )

    fireEvent.click(getByText('Choice One'), { bubbles: true })

    const reviewButton = getByText('Review')
    fireEvent.click(reviewButton, { bubbles: true })
    const nextButton = await findByText('Submit & Next Ballot')
    fireEvent.click(nextButton, { bubbles: true })

    await waitFor(() => {
      expect(nextBallotMock).toBeCalled()
      expect(submitMock).toHaveBeenCalledTimes(1)
    })
  })

  it('navigates to previous ballot', async () => {
    const previousBallotMock = jest.fn()
    const { getByText } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/audit-board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contests={[contest]}
          previousBallot={previousBallotMock}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          batchId="batch-id-1"
          ballotPosition={2112}
        />
      </Router>
    )
    fireEvent.click(getByText('Back'), { bubbles: true })

    await waitFor(() => {
      expect(previousBallotMock).toBeCalledTimes(1)
    })

    fireEvent.click(getByText('Choice One'), { bubbles: true })
    await waitFor(() => fireEvent.click(getByText('Review'), { bubbles: true }))
    await waitFor(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
    })
    fireEvent.click(getByText('Back'), { bubbles: true })
    await waitFor(() => {
      expect(getByText('Review')).toBeTruthy()
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
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
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
