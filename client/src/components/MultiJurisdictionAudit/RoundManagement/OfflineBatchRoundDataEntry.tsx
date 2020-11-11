import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { H5 } from '@blueprintjs/core'
import { Field, Formik, FormikProps } from 'formik'
import styled from 'styled-components'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import Card from '../../Atoms/SpacedCard'
import FormField from '../../Atoms/Form/FormField'
import FormButton from '../../Atoms/Form/FormButton'
import { testNumber } from '../../utilities'
import useBatchResults, { IResultValues } from './useBatchResults'
import { IRound } from '../useRoundsAuditAdmin'
import useOfflineBatchResults, {
  IOfflineBatchResults,
} from './useOfflineBatchResults'
import { IContest } from '../../../types'

const BottomButton = styled(FormButton)`
  margin: 30px 0;
`

const BlockLabel = styled.label`
  display: block;
  margin: 20px 0;
`

interface IProps {
  round: IRound
}

interface IValues {
  results: IResultValues
}

const OfflineBatchRoundDataEntry = ({ round }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const [results, updateResults, finalizeResults] = useOfflineBatchResults(
    electionId,
    jurisdictionId,
    round.id
  )
  const [newResults, setNewResults] = useState<
    IOfflineBatchResults['results'] | null
  >(results && results.results)

  if (!contests || !results) return null

  // We only support one contest for now
  const contest = contests[0]

  return (
    <form>
      <p>
        When you have examined all the ballots assigned to you, enter the number
        of votes recorded for each candidate/choice for each batch of audited
        ballots.
      </p>
      <table>
        <thead>
          <th>Batch</th>
          {contest.choices.map(choice => (
            <th key={choice.id}>{choice.name}</th>
          ))}
        </thead>
        <tbody>
          {Object.entries(newResults!).map(([batchName, choiceResults]) => (
            <tr key={batchName}>
              <td>{batchName}</td>
              {contest.choices.map(choice => (
                <td key={choice.id}>{choiceResults[choice.id]}</td>
              ))}
            </tr>
          ))}
          <tr>
            <td>Add batch</td>
          </tr>
        </tbody>
      </table>
    </form>
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
