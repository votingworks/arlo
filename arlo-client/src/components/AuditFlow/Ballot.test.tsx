import React from 'react'
import {
  render,
  fireEvent,
  wait,
  waitForElement,
  queryByText,
} from '@testing-library/react'
import { Router } from 'react-router-dom'
import { createMemoryHistory } from 'history'
import Ballot from './Ballot'
import { dummyBallots } from './_mocks'

const history = createMemoryHistory()

const contest = {
  choices: [
    {
      id: 'choice-1',
      name: 'choice one',
      numVotes: 792,
    },
    {
      id: 'choice-2',
      name: 'choice two',
      numVotes: 1325,
    },
  ],
  id: 'contest-1',
  name: 'contest name',
  winners: '1',
  votesAllowed: '1',
  totalBallotsCast: '2123',
}

describe('Ballot', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id-1"
          ballotId={313}
        />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('switches audit and review views', async () => {
    const { container, getByText, getByTestId } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id-1"
          ballotId={313}
        />
      </Router>
    )

    fireEvent.click(getByTestId('choice one'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
    })
    await wait(() => {
      expect(container).toMatchSnapshot()
    })
    fireEvent.click(getByText('Edit'), { bubbles: true })
    await wait(() => {
      expect(getByText('Review')).toBeTruthy()
    })
  })

  it('toggles and submits comment', async () => {
    const { container, getByText, getByTestId } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id-1"
          ballotId={313}
        />
      </Router>
    )

    fireEvent.click(getByText('Add comment'), { bubbles: true })

    const commentInput = getByTestId('comment-textarea')
    fireEvent.change(commentInput, { target: { value: 'a test comment' } })

    fireEvent.click(getByTestId('choice one'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(getByText('COMMENT: a test comment')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('toggles and deletes a comment', async () => {
    const { container, getByText, queryByText, getByTestId } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id-1"
          ballotId={313}
        />
      </Router>
    )

    fireEvent.click(getByText('Add comment'), { bubbles: true })

    const commentInput = getByTestId('comment-textarea')
    fireEvent.change(commentInput, { target: { value: 'a test comment' } })

    fireEvent.click(getByText('Remove comment'), { bubbles: true })

    fireEvent.click(getByTestId('choice one'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(queryByText('COMMENT: a test comment')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })

  it('submits review and progresses to next ballot', async () => {
    const submitMock = jest.fn()
    const nextBallotMock = jest.fn()
    const { container, getByText, getByTestId } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={jest.fn()}
          nextBallot={nextBallotMock}
          submitBallot={submitMock}
          roundIx="1"
          batchId="batch-id-1"
          ballotId={313}
        />
      </Router>
    )

    fireEvent.click(getByTestId('choice one'), { bubbles: true })

    const reviewButton = await waitForElement(
      () => getByTestId('enabled-review'),
      { container }
    )
    fireEvent.click(reviewButton, { bubbles: true })
    const nextButton = await waitForElement(
      () => getByText('Submit & Next Ballot'),
      { container }
    )
    fireEvent.click(nextButton, { bubbles: true })

    await wait(() => {
      expect(nextBallotMock).toBeCalled()
      expect(submitMock).toHaveBeenCalledTimes(1)
    })
  })

  it('navigates to previous ballot', async () => {
    const previousBallotMock = jest.fn()
    const { getByText, getByTestId } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={previousBallotMock}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id-1"
          ballotId={2112}
        />
      </Router>
    )
    fireEvent.click(getByText('Back'), { bubbles: true })

    await wait(() => {
      expect(previousBallotMock).toBeCalledTimes(1)
    })

    fireEvent.click(getByTestId('choice one'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
    })
    fireEvent.click(getByText('Back'), { bubbles: true })
    await wait(() => {
      expect(previousBallotMock).toBeCalledTimes(2)
    })
  })

  it('redirects if ballot does not exist', async () => {
    const { container } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest={contest}
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id"
          ballotId={6}
        />
      </Router>
    )

    await wait(() => {
      expect(container).toMatchSnapshot()
    })
  })
})
