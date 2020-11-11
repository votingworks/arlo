import React from 'react'
import { useParams } from 'react-router-dom'
import { Formik, FormikProps, Field, FieldArray } from 'formik'
import { Button, HTMLTable } from '@blueprintjs/core'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { IRound } from '../useRoundsAuditAdmin'
import useOfflineBatchResults, {
  IOfflineBatchResults,
} from './useOfflineBatchResults'

interface IProps {
  round: IRound
}

const OfflineBatchRoundDataEntry = ({ round }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const [batchResults, updateResults, finalizeResults] = useOfflineBatchResults(
    electionId,
    jurisdictionId,
    round.id
  )

  if (!contests || !batchResults) return null

  // We only support one contest for now
  const contest = contests[0]

  const { results, finalizedAt } = batchResults

  return (
    <Formik
      initialValues={{ results }}
      enableReinitialize
      onSubmit={async values => {
        // TODO validation to prevent partially empty rows
        // Omit empty rows
        const filteredResults = values.results.filter(
          result =>
            result.batchName !== '' &&
            Object.values(result.choiceResults).every(
              value => (value as string | number) !== ''
            )
        )
        await updateResults(filteredResults)
        // TODO change isSubmitting?
      }}
    >
      {({
        handleSubmit,
        values,
      }: FormikProps<{ results: IOfflineBatchResults['results'] }>) => (
        <form>
          <p>
            When you have examined all the ballots assigned to you, enter the
            number of votes recorded for each candidate/choice for each batch of
            audited ballots.
          </p>
          <fieldset disabled={!!finalizedAt}>
            <HTMLTable>
              <thead>
                <tr>
                  <th />
                  <th>Batch Name</th>
                  {contest.choices.map(choice => (
                    <th key={`th-${choice.id}`}>{choice.name}</th>
                  ))}
                </tr>
              </thead>
              <FieldArray
                name="results"
                render={arrayHelpers => (
                  <tbody>
                    {values.results.map((_, r) => (
                      // eslint-disable-next-line react/no-array-index-key
                      <tr key={`batchName-${r}`}>
                        <td>
                          <Button
                            icon="cross"
                            onClick={() => arrayHelpers.remove(r)}
                          />
                        </td>
                        <td>
                          <Field
                            type="text"
                            name={`results.${r}.batchName`}
                            placeholder="Enter a batch name..."
                          />
                        </td>
                        {contest.choices.map(choice => (
                          // eslint-disable-next-line react/no-array-index-key
                          <td key={`${r}-${choice.id}`}>
                            <Field
                              type="number"
                              name={`results.${r}.choiceResults.${choice.id}`}
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                    <tr>
                      <td />
                      <td>
                        <Button
                          onClick={() =>
                            arrayHelpers.push({
                              batchName: '',
                              choiceResults: {},
                            })
                          }
                        >
                          + Add batch
                        </Button>
                      </td>
                      {contest.choices.map(choice => (
                        <td key={`add-${choice.id}`}></td>
                      ))}
                    </tr>
                  </tbody>
                )}
              />
            </HTMLTable>
            <Button onClick={handleSubmit as (e: React.FormEvent) => void}>
              Save Results
            </Button>
            <Button onClick={finalizeResults}>Finalize Results</Button>
          </fieldset>
        </form>
      )}
    </Formik>
  )
}
//   return (
//     <OfflineBatchResultsForm
//       contest={contest}
//       initialResults={results.results}
//       finalizedAt={results.finalizedAt}
//       updateResults={updateResults}
//       finalizeResults={finalizeResults}
//     />
//   )

// interface IFormProps {
//   contest: IContest
//   initialResults: IOfflineBatchResults['results']
//   finalizedAt: IOfflineBatchResults['finalizedAt']
//   updateResults: (
//     newResults: IOfflineBatchResults['results']
//   ) => Promise<boolean>
//   finalizeResults: () => Promise<boolean>
// }

// const OfflineBatchResultsForm = ({
//   contest,
//   initialResults,
//   finalizedAt,
//   updateResults,
//   finalizeResults,
// }: IFormProps) => {
//   const choiceIdToName = Object.fromEntries(
//     contest.choices.map(choice => [choice.id, choice.name])
//   )

//   return <form> </form>
// }

/* {Object.entries(results.results).map((batch_name, choice_results) => */

// const alreadySubmittedResults = Object.values(results).some(a =>
//   Object.values(a).some(b => b)
// )

// const submit = async (values: IValues) => {
//   updateResults(values.results)
// }

// return (
//   <Formik initialValues={{ results }} enableReinitialize onSubmit={submit}>
//     {({ handleSubmit }: FormikProps<IValues>) => (
//       <form>
//         <p>
//           When you have examined all the ballots assigned to you, enter the
//           number of votes recorded for each candidate/choice from the audited
//           ballots.
//         </p>
//         {batches.map(batch => (
//           <Card key={batch.id}>
//             <H5>{`Batch: ${batch.name}, Contest: ${contest.name}`}</H5>
//             {contest.choices.map(choice => (
//               <BlockLabel
//                 key={choice.id}
//                 htmlFor={`results[${batch.id}][${choice.id}]`}
//               >
//                 Votes for {choice.name}:
//                 {alreadySubmittedResults ? (
//                   results[batch.id][choice.id]
//                 ) : (
//                   <Field
//                     id={`results[${batch.id}][${choice.id}]`}
//                     name={`results[${batch.id}][${choice.id}]`}
//                     disabled={alreadySubmittedResults}
//                     validate={testNumber()}
//                     component={FormField}
//                   />
//                 )}
//               </BlockLabel>
//             ))}
//           </Card>
//         ))}
//         <BottomButton
//           type="submit"
//           intent="primary"
//           disabled={alreadySubmittedResults}
//           onClick={handleSubmit}
//         >
//           {alreadySubmittedResults
//             ? `Already Submitted Data for Round ${round.roundNum}`
//             : `Submit Data for Round ${round.roundNum}`}
//         </BottomButton>
//       </form>
//     )}
//   </Formik>
// )
// }

export default OfflineBatchRoundDataEntry
