import React, { useState } from 'react'
import { useParams, useHistory } from 'react-router-dom'
import { H4, Callout, RadioGroup, Radio } from '@blueprintjs/core'
import { toast } from 'react-toastify'
import { Formik, FormikProps, Form, getIn, Field } from 'formik'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'
import useAuditSettings from '../../useAuditSettings'
import useContests from '../../useContests'
import { IContest, ISampleSizeOption } from '../../../../types'
import useJurisdictions, { FileProcessingStatus } from '../../useJurisdictions'
import { testNumber } from '../../../utilities'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import ContestsTable from './ContestsTable'
import SettingsTable from './SettingsTable'
import { isSetupComplete } from '../../StatusBox'
import useJurisdictionFile from '../Participants/useJurisdictionFile'
import ConfirmLaunch from './ConfirmLaunch'
import FormField from '../../../Atoms/Form/FormField'
import ElevatedCard from '../../../Atoms/SpacedCard'
import useSampleSizes from './useSampleSizes'

const percentFormatter = new Intl.NumberFormat(undefined, {
  style: 'percent',
})

interface IStringSampleSizes {
  [key: string]: {
    size: string
    type: string | null
    prob: number | null
  }[]
}

interface IFormOptions {
  [key: string]: string
}

interface IProps {
  locked: boolean
  prevStage: ISidebarMenuItem
  refresh: () => void
}

const Review: React.FC<IProps> = ({ prevStage, locked, refresh }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings] = useAuditSettings(electionId)
  const { electionName, randomSeed, riskLimit, online } = auditSettings
  const jurisdictions = useJurisdictions(electionId)
  const [jurisdictionFile] = useJurisdictionFile(electionId)
  const [contests] = useContests(electionId)
  const [sampleSizes, setSampleSizes] = useState<IFormOptions>({})
  const history = useHistory()
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false)
  const [sampleSizeOptions, uploadSampleSizes] = useSampleSizes(electionId)

  const submit = async () => {
    try {
      if (uploadSampleSizes(sampleSizes)) {
        refresh()
        history.push(`/election/${electionId}/progress`)
      } else {
        return
      }
    } catch (err) /* istanbul ignore next */ {
      // TEST TODO
      toast.error(err.message)
    }
  }

  if (!contests) return null // Still loading

  const targetedContests = contests
    .filter(c => c.isTargeted === true)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        jurisdictions.length > 0
          ? jurisdictions.find(p => p.id === j)!.name
          : ''
      ),
    }))
  const opportunisticContests = contests
    .filter(c => c.isTargeted === false)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        jurisdictions.length > 0
          ? jurisdictions.find(p => p.id === j)!.name
          : ''
      ),
    }))

  const completedBallotUploads = jurisdictions.filter(
    j =>
      j.ballotManifest.processing &&
      j.ballotManifest.processing.status === FileProcessingStatus.PROCESSED
  ).length

  const initialValues = targetedContests.length
    ? targetedContests.map(c => ({
        [c.id]: sampleSizeOptions ? sampleSizeOptions[c.id][0].size : '',
      }))
    : []
  const initialCustomValues = targetedContests.length
    ? targetedContests.map(c => ({ [c.id]: '' }))
    : []

  return (
    <div>
      <H2Title>Review &amp; Launch</H2Title>
      <Callout intent="warning">
        Once the audit is started, the audit definition will no longer be
        editable. Please make sure this data is correct before launching the
        audit.
      </Callout>
      <ElevatedCard>
        <H4>Audit Settings</H4>
        <SettingsTable>
          <tbody>
            <tr>
              <td>Election Name:</td>
              <td>{electionName}</td>
            </tr>
            <tr>
              <td>Risk Limit:</td>
              <td>{riskLimit}</td>
            </tr>
            <tr>
              <td>Random Seed:</td>
              <td>{randomSeed}</td>
            </tr>
            <tr>
              <td>Participating Jurisdictions:</td>
              <td>
                <a
                  href={`/api/election/${electionId}/jurisdiction/file/csv`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {jurisdictionFile && jurisdictionFile.file
                    ? jurisdictionFile.file.name
                    : ''}
                </a>
              </td>
            </tr>
            <tr>
              <td>Audit Board Data Entry:</td>
              <td>{online ? 'Online' : 'Offline'}</td>
            </tr>
          </tbody>
        </SettingsTable>
        <ContestsTable>
          <thead>
            <tr>
              <th>Target Contests</th>
              <th>Jurisdictions</th>
            </tr>
          </thead>
          <tbody>
            {targetedContests.map((c: IContest) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.jurisdictionIds.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </ContestsTable>
        <ContestsTable>
          <thead>
            <tr>
              <th>Opportunistic Contests</th>
              <th>Jurisdictions</th>
            </tr>
          </thead>
          <tbody>
            {opportunisticContests.map((c: IContest) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.jurisdictionIds.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </ContestsTable>
      </ElevatedCard>
      <br />
      <H4>Estimated Sample Sizes</H4>
      <Formik
        initialValues={{
          sampleSizes: initialValues,
          customSampleSizes: initialCustomValues,
        }}
        enableReinitialize
        onSubmit={values => {
          setSampleSizes(
            values.sampleSizes.reduce((a, s, i) => {
              const contestId = Object.keys(s)[0]
              if (s[contestId] === 'custom') {
                return {
                  ...a,
                  [contestId]: values.customSampleSizes[i][contestId],
                }
              }
              return { ...a, [contestId]: s[contestId] }
            }, {})
          )
          setIsConfirmDialogOpen(true)
        }}
      >
        {({
          values,
          handleSubmit,
          setFieldValue,
        }: FormikProps<{ sampleSizes: { [key: string]: string }[] }>) => (
          <Form data-testid="sample-size-form">
            {sampleSizeOptions && Object.keys(sampleSizeOptions).length && (
              <FormSection>
                <FormSectionDescription>
                  Choose the initial sample size for each contest you would like
                  to use for Round 1 of the audit from the options below.
                </FormSectionDescription>
                {targetedContests.map((contest, i) => (
                  <ElevatedCard key={contest.id}>
                    <FormSectionDescription>
                      <H4>{contest.name}</H4>
                      <RadioGroup
                        name={`sampleSizes[${i}][${contest.id}]`}
                        onChange={e =>
                          setFieldValue(
                            `sampleSizes[${i}][${contest.id}]`,
                            e.currentTarget.value
                          )
                        }
                        selectedValue={getIn(
                          values,
                          `sampleSizes[${i}][${contest.id}]`
                        )}
                        disabled={locked}
                      >
                        {sampleSizeOptions[contest.id].map(
                          (option: ISampleSizeOption) => {
                            return (
                              <Radio value={option.size} key={option.size}>
                                {option.type
                                  ? 'BRAVO Average Sample Number: '
                                  : ''}
                                {`${option.size} samples`}
                                {option.prob
                                  ? ` (${percentFormatter.format(
                                      option.prob
                                    )} chance of reaching risk limit and completing the audit in one round)`
                                  : ''}
                              </Radio>
                            )
                          }
                        )}
                        <Radio value="custom">
                          Enter your own sample size (not recommended)
                        </Radio>
                        {getIn(values, `sampleSizes[${i}][${contest.id}]`) ===
                          'custom' && (
                          <Field
                            component={FormField}
                            name={`customSampleSizes[${i}][${contest.id}]`}
                            type="text"
                            validate={testNumber(
                              Number(contest.totalBallotsCast),
                              `Must be less than or equal to: ${contest.totalBallotsCast} (the total number of ballots in this targeted contest)`
                            )}
                          />
                        )}
                      </RadioGroup>
                    </FormSectionDescription>
                  </ElevatedCard>
                ))}
              </FormSection>
            )}
            <FormButtonBar>
              <FormButton onClick={prevStage.activate}>Back</FormButton>
              <FormButton
                intent="primary"
                disabled={
                  locked ||
                  !isSetupComplete(jurisdictions, contests, auditSettings)
                }
                onClick={handleSubmit}
              >
                Launch Audit
              </FormButton>
            </FormButtonBar>
          </Form>
        )}
      </Formik>
      <ConfirmLaunch
        isOpen={isConfirmDialogOpen}
        handleClose={() => setIsConfirmDialogOpen(false)}
        onLaunch={submit}
        numJurisdictions={jurisdictions.length}
        completedBallotUploads={completedBallotUploads}
      />
    </div>
  )
}

export default Review
