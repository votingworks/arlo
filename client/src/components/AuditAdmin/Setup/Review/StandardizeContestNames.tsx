import React from 'react'
import styled from 'styled-components'
import {
  HTMLTable,
  Colors,
  Dialog,
  Classes,
  HTMLSelect,
  Button,
  Intent,
} from '@blueprintjs/core'
import { Formik } from 'formik'
import { IJurisdiction } from '../../../useJurisdictions'
import { IContestNameStandardizations } from '../../../useContestNameStandardizations'
import FormButton from '../../../Atoms/Form/FormButton'

interface IStandardizeContestNamesDialogProps {
  isOpen: boolean
  onClose: () => void
  standardizations: IContestNameStandardizations
  updateStandardizations: (
    standardizations: IContestNameStandardizations['standardizations']
  ) => Promise<boolean>
  jurisdictionsById: { [id: string]: IJurisdiction }
}

const StandardizeContestsTable = styled(HTMLTable)`
  border: 1px solid ${Colors.LIGHT_GRAY1};
  background: ${Colors.WHITE};
  width: 100%;

  tr th,
  tr td {
    vertical-align: middle;
    word-wrap: break-word;
  }

  .bp3-html-select {
    width: 100%;
  }
`

const StandardizeContestNamesDialog: React.FC<IStandardizeContestNamesDialogProps> = ({
  isOpen,
  onClose,
  standardizations,
  updateStandardizations,
  jurisdictionsById,
}) => (
  <Dialog
    isOpen={isOpen}
    onClose={onClose}
    title="Standardize Contest Names"
    style={{ width: '600px' }}
  >
    <Formik
      initialValues={standardizations.standardizations}
      enableReinitialize
      onSubmit={async newStandardizations => {
        await updateStandardizations(newStandardizations)
        onClose()
      }}
    >
      {({ values, setValues, handleSubmit, isSubmitting }) => (
        <form>
          <div className={Classes.DIALOG_BODY}>
            <p>
              For each contest below, select the CVR contest name that matches
              the standardized contest name.
            </p>
            {
              <StandardizeContestsTable striped bordered>
                <thead>
                  <tr>
                    <th>Jurisdiction</th>
                    <th>Standardized Contest</th>
                    <th>CVR Contest</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(values).map(
                    ([jurisdictionId, jurisdictionStandardizations]) =>
                      Object.entries(jurisdictionStandardizations).map(
                        ([contestName, standardizedCvrContestName]) => (
                          <tr key={jurisdictionId + contestName}>
                            <td>{jurisdictionsById[jurisdictionId].name}</td>
                            <td>{contestName}</td>
                            <td>
                              <HTMLSelect
                                value={standardizedCvrContestName || undefined}
                                onChange={e =>
                                  // We have to use setValues because the contest name
                                  // might have a dot or apostrophe in it, so
                                  // setFieldValue won't work.
                                  setValues({
                                    ...values,
                                    [jurisdictionId]: {
                                      ...values[jurisdictionId],
                                      [contestName]:
                                        e.currentTarget.value || null,
                                    },
                                  })
                                }
                              >
                                {[<option key="" value="" />].concat(
                                  standardizations.cvrContestNames[
                                    jurisdictionId
                                  ].map(cvrContestName => (
                                    <option
                                      value={cvrContestName}
                                      key={cvrContestName}
                                    >
                                      {cvrContestName}
                                    </option>
                                  ))
                                )}
                              </HTMLSelect>
                            </td>
                          </tr>
                        )
                      )
                  )}
                </tbody>
              </StandardizeContestsTable>
            }
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={onClose}>Cancel</Button>
              <FormButton
                intent={Intent.PRIMARY}
                onClick={handleSubmit}
                loading={isSubmitting}
              >
                Submit
              </FormButton>
            </div>
          </div>
        </form>
      )}
    </Formik>
  </Dialog>
)

export default StandardizeContestNamesDialog
