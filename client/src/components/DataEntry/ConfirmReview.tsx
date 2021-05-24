import React, { useState } from 'react'
import {
  Dialog,
  Classes,
  Button,
  Intent,
  Colors,
  H4,
  H3,
} from '@blueprintjs/core'
import styled from 'styled-components'
import {
  IBallotInterpretation,
  IContest as IContestApi,
  IContest,
  Interpretation,
} from '../../types'

export interface IConfirmOptions {
  onYesClick: () => Promise<void>
  contests: IContestApi[]
  interpretations: IBallotInterpretation[]
}

const AuditBoardDialog = styled(Dialog)`
  background-color: ${Colors.WHITE};
  padding-bottom: 0;
  font-family: 'ProximaNova-Condensed-Regular', 'Helvetica', 'Arial', sans-serif;
  font-size: 1.2em;
  .bp3-heading {
    color: ${Colors.BLACK};
  }
`

const DialogHeader = styled.div`
  background-color: ${Colors.BLACK};
  min-height: 50px;
  .bp3-heading,
  .bp3-button .bp3-icon {
    color: ${Colors.WHITE};
  }
`

const DialogFooter = styled.div`
  margin: 0;
  border-radius: 0 0 6px 6px;
  background-color: ${Colors.BLACK};
  padding: 10px 20px;
`

const ChoiceName = styled(H3)`
  font-weight: 500;
`

const ContestReviewCard = styled.div`
  margin-bottom: 20px;
`

const YesButton = styled(Button)`
  font-weight: 600;
`

const renderInterpretation = (
  { interpretation, choiceIds }: IBallotInterpretation,
  contest: IContest
) => {
  if (!interpretation) return <div />
  switch (interpretation) {
    case Interpretation.VOTE:
      return contest.choices.map(choice =>
        choiceIds.includes(choice.id) ? (
          <ChoiceName key={choice.id}>{choice.name}</ChoiceName>
        ) : null
      )
    case Interpretation.BLANK:
      return <ChoiceName>Blank vote</ChoiceName>
    case Interpretation.CONTEST_NOT_ON_BALLOT:
      return <ChoiceName>Not on Ballot</ChoiceName>
    case Interpretation.CANT_AGREE:
    default:
      return null
    // case for Interpretation.CANT_AGREE in case we decide to put it back in again
    // return (
    //   <LockedButton disabled large intent="primary">
    //     Audit board can&apos;t agree
    //   </LockedButton>
    // )
  }
}

export const useConfirm = () => {
  // We show the dialog whenever options are set.
  // On close, we set options to null.
  const [options, setOptions] = useState<IConfirmOptions | null>(null)

  const confirm = (newOptions: IConfirmOptions) => {
    setOptions(newOptions)
  }

  const onYesClick = async () => {
    await options!.onYesClick()
    setOptions(null)
  }

  const onClose = () => {
    setOptions(null)
  }

  const confirmProps = {
    isOpen: !!options,
    onYesClick,
    onClose,
    interpretations: options ? options.interpretations : [],
    contests: options ? options.contests : [],
  }

  return { confirm, confirmProps }
}

interface IConfirmProps extends IConfirmOptions {
  isOpen: boolean
  onClose: () => void
}

export const ConfirmReview = ({
  isOpen,
  onYesClick,
  onClose,
  contests,
  interpretations,
}: IConfirmProps) => {
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  const handleYesClick = async () => {
    setIsSubmitting(true)
    try {
      await onYesClick()
    } catch (error) {
      // Do nothing, error handling should happen within onYesClick
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuditBoardDialog onClose={onClose} isOpen={isOpen}>
      <DialogHeader className={Classes.DIALOG_HEADER}>
        <H4 className={Classes.HEADING}>Confirm the Ballot Selections</H4>
      </DialogHeader>
      <div className={Classes.DIALOG_BODY}>
        {contests.map((contest, i) => (
          <ContestReviewCard key={contest.id}>
            <p>{contest.name}</p>
            {renderInterpretation(interpretations[i], contest)}
            <p>
              {interpretations[i].comment &&
                `Comment: ${interpretations[i].comment}`}
            </p>
          </ContestReviewCard>
        ))}
      </div>
      <DialogFooter className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button disabled={isSubmitting} onClick={onClose} large>
            Change Selections
          </Button>
          <YesButton
            intent={Intent.SUCCESS}
            onClick={handleYesClick}
            loading={isSubmitting}
            large
          >
            Confirm Selections
          </YesButton>
        </div>
      </DialogFooter>
    </AuditBoardDialog>
  )
}
