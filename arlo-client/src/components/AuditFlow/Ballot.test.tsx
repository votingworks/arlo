import React from 'react'
import { render, fireEvent, wait, waitForElement } from '@testing-library/react'
import { Router } from 'react-router-dom'
import { createMemoryHistory } from 'history'
import Ballot from './Ballot'
import { dummyBallots } from './_mocks'

const history = createMemoryHistory()

describe('Ballot', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Ballot
        home="/election/1/board/1"
        ballots={dummyBallots.ballots}
        boardName="audit board #1"
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={jest.fn()}
        submitBallot={jest.fn()}
        roundIx="1"
        batchId="batch-id"
        ballotId={1}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('switches audit and review views', async () => {
    const { container, getByText, getByTestId } = render(
      <Ballot
        home="/election/1/board/1"
        ballots={dummyBallots.ballots}
        boardName="audit board #1"
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={jest.fn()}
        submitBallot={jest.fn()}
        roundIx="1"
        batchId="batch-id"
        ballotId={1}
      />
    )

    fireEvent.click(getByTestId('YES'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
    fireEvent.click(getByText('Edit'), { bubbles: true })
    await wait(() => {
      expect(getByText('Review')).toBeTruthy()
    })
  })

  it('toggles and submits comment', async () => {
    const { container, getByText, getByTestId } = render(
      <Ballot
        home="/election/1/board/1"
        ballots={dummyBallots.ballots}
        boardName="audit board #1"
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={jest.fn()}
        submitBallot={jest.fn()}
        roundIx="1"
        batchId="batch-id"
        ballotId={1}
      />
    )

    fireEvent.click(getByText('Add comment'), { bubbles: true })
    await wait(() => {
      const commentInput = getByTestId('comment-textarea')
      fireEvent.change(commentInput, { target: { value: 'a test comment' } })
    })

    fireEvent.click(getByTestId('YES'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      expect(getByText('Submit & Next Ballot')).toBeTruthy()
      expect(getByText('COMMENT: a test comment')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('submits review and progresses to next ballot', async () => {
    const nextBallotMock = jest.fn()
    const { container, getByText, getByTestId } = render(
      <Ballot
        home="/election/1/board/1"
        ballots={dummyBallots.ballots}
        boardName="audit board #1"
        contest="contest name"
        previousBallot={jest.fn()}
        nextBallot={nextBallotMock}
        submitBallot={jest.fn()}
        roundIx="1"
        batchId="batch-id"
        ballotId={1}
      />
    )

    fireEvent.click(getByTestId('YES'), { bubbles: true })

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
          contest="contest name"
          previousBallot={previousBallotMock}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id"
          ballotId={2}
        />
      </Router>
    )
    fireEvent.click(getByText('Back'), { bubbles: true })

    await wait(() => {
      expect(previousBallotMock).toBeCalledTimes(1)
    })

    fireEvent.click(getByTestId('YES'), { bubbles: true })
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
          contest="contest name"
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

  it('redirects if ballots array does not exist', async () => {
    const { container } = render(
      <Router history={history}>
        <Ballot
          home="/election/1/board/1"
          ballots={dummyBallots.ballots}
          boardName="audit board #1"
          contest="contest name"
          previousBallot={jest.fn()}
          nextBallot={jest.fn()}
          submitBallot={jest.fn()}
          roundIx="1"
          batchId="batch-id"
          ballotId={1}
        />
      </Router>
    )

    await wait(() => {
      expect(container).toMatchSnapshot()
    })
  })
})
