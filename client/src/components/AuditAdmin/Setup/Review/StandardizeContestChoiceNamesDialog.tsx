import {
  Button,
  Callout,
  Classes,
  Colors,
  Dialog,
  HTMLSelect,
  HTMLTable,
} from '@blueprintjs/core'
import React, { useState } from 'react'
import styled from 'styled-components'

import FormButton from '../../../Atoms/Form/FormButton'
import { IContest } from '../../../../types'
import { IContestChoiceNameStandardizations } from '../../../useContestChoiceNameStandardizations'
import { IJurisdiction } from '../../../useJurisdictions'

export function isContestChoiceNameStandardizationComplete(
  standardizations: IContestChoiceNameStandardizations
): boolean {
  for (const jurisdictionStandardizations of Object.values(standardizations)) {
    for (const contestStandardizations of Object.values(
      jurisdictionStandardizations
    )) {
      for (const standardizedChoiceName of Object.values(
        contestStandardizations
      )) {
        if (standardizedChoiceName === null) {
          return false
        }
      }
    }
  }
  return true
}

const Table = styled(HTMLTable)`
  background: ${Colors.WHITE};
  border: 1px solid ${Colors.LIGHT_GRAY1};
  width: 100%;

  tr th,
  tr td {
    vertical-align: middle;
    word-wrap: break-word;
  }
`

interface IDialogProps {
  contest: IContest
  isOpen: boolean
  jurisdictionsById: { [id: string]: IJurisdiction }
  onClose: () => void
  standardizations: IContestChoiceNameStandardizations
  standardizedContestChoiceNames: string[]
  updateStandardizations: (
    newStandardizations: IContestChoiceNameStandardizations
  ) => Promise<void>
}

/**
 * A dialog for standardizing contest choice names
 */
export const StandardizeContestChoiceNamesDialog: React.FC<IDialogProps> = ({
  isOpen,
  onClose,
  standardizations,
  contest,
  jurisdictionsById,
  standardizedContestChoiceNames,
  updateStandardizations,
}) => {
  const [formState, setFormState] = useState(standardizations)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const setStandardization = ({
    jurisdictionId,
    cvrChoiceName,
    standardizedChoiceName,
  }: {
    jurisdictionId: string
    cvrChoiceName: string
    standardizedChoiceName: string | null
  }) => {
    setFormState({
      ...formState,
      [jurisdictionId]: {
        ...formState[jurisdictionId],
        [contest.id]: {
          ...formState[jurisdictionId]?.[contest.id],
          [cvrChoiceName]: standardizedChoiceName,
        },
      },
    })
  }

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Standardize Contest Choice Names"
      style={{ width: '600px' }}
    >
      <div className={Classes.DIALOG_BODY}>
        <p>
          For each contest choice below, select the standardized choice name
          that matches the CVR choice name.
        </p>
        <Table striped bordered>
          <thead>
            <tr>
              <th>Jurisdiction</th>
              <th>CVR Choice</th>
              <th>Standardized Choice</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(standardizations).map(
              ([jurisdictionId, jurisdictionStandardizations]) =>
                Object.keys(jurisdictionStandardizations[contest.id] ?? {}).map(
                  cvrChoiceName => (
                    <tr key={`${jurisdictionId}${cvrChoiceName}`}>
                      <td>{jurisdictionsById[jurisdictionId].name}</td>
                      <td>{cvrChoiceName}</td>
                      <td>
                        <HTMLSelect
                          onChange={e =>
                            setStandardization({
                              jurisdictionId,
                              cvrChoiceName,
                              standardizedChoiceName: e.target.value || null,
                            })
                          }
                          value={
                            formState[jurisdictionId]?.[contest.id]?.[
                              cvrChoiceName
                            ] ?? ''
                          }
                        >
                          <option key="" value="" />
                          {standardizedContestChoiceNames.map(name => (
                            <option value={name} key={name}>
                              {name}
                            </option>
                          ))}
                        </HTMLSelect>
                      </td>
                    </tr>
                  )
                )
            )}
          </tbody>
        </Table>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button onClick={onClose}>Cancel</Button>
          <FormButton
            intent="primary"
            loading={isSubmitting}
            onClick={async () => {
              setIsSubmitting(true)
              try {
                await updateStandardizations(formState)
                onClose()
              } finally {
                setIsSubmitting(false)
              }
            }}
          >
            Submit
          </FormButton>
        </div>
      </div>
    </Dialog>
  )
}

const CalloutWithBottomMargin = styled(Callout)`
  margin-bottom: 16px;
`

interface ICalloutProps {
  contest: IContest
  disabled: boolean
  openDialog: () => void
  standardizations: IContestChoiceNameStandardizations
}

/**
 * A callout indicating the status of contest choice name standardization
 */
export const StandardizeContestChoiceNamesCallout: React.FC<ICalloutProps> = ({
  contest,
  disabled,
  openDialog,
  standardizations,
}) => {
  let isStandardizationNeeded = false
  let isStandardizationNeededAndOutstanding = false
  for (const jurisdictionStandardizations of Object.values(standardizations)) {
    const contestStandardization =
      jurisdictionStandardizations[contest.id] ?? {}
    for (const standardizedChoiceName of Object.values(
      contestStandardization
    )) {
      isStandardizationNeeded = true
      if (standardizedChoiceName === null) {
        isStandardizationNeededAndOutstanding = true
        break
      }
    }
  }

  if (!isStandardizationNeeded) {
    return null
  }

  if (isStandardizationNeededAndOutstanding) {
    return (
      <CalloutWithBottomMargin intent="warning">
        <p>
          Some {contest.name} choice names in the uploaded CVR files do not
          match the standardized contest choice names.
        </p>
        <Button disabled={disabled} intent="primary" onClick={openDialog}>
          Standardize Contest Choice Names
        </Button>
      </CalloutWithBottomMargin>
    )
  }

  // Standardization is needed and has been completed
  return (
    <CalloutWithBottomMargin intent="success">
      <p>
        All {contest.name} choice names in the uploaded CVR files have been
        standardized.
      </p>
      <Button disabled={disabled} intent="none" onClick={openDialog}>
        Edit Standardized Contest Choice Names
      </Button>
    </CalloutWithBottomMargin>
  )
}
